#!/usr/bin/env python3
"""FACO Crumble: ten peer identities, server-managed rooms, direct/group chat.

Audio travels via DTLS-SRTP WebRTC mesh. The desktop host is the sole controller
for ephemeral credentials, presence, call memberships and message delivery; it
is not an audio mixer or a storage service. Local admin is a separate listener.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import secrets
import time
import unicodedata
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlsplit

import qrcode
from qrcode.image.svg import SvgPathImage
from aiohttp import WSMsgType, web

ROOT = Path(__file__).resolve().parent
USER_ROLES = tuple(f'user{i:02d}' for i in range(1, 11))
MAX_MSG_SIZE = 65536
MAX_CHAT_LENGTH = 2000
DEFAULT_ICE_SERVERS = [{'urls': ['stun:stun.l.google.com:19302']}]


def normalize_name(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    name = unicodedata.normalize('NFC', value.strip())
    if not (1 <= len(name) <= 40) or any(unicodedata.category(ch).startswith('C') for ch in name):
        return None
    return name


def normalize_message(value: Any) -> str | None:
    if not isinstance(value, str) or len(value) > MAX_CHAT_LENGTH + 32:
        return None
    value = unicodedata.normalize('NFC', value.strip())
    if not (1 <= len(value) <= MAX_CHAT_LENGTH) or any(ord(ch) in (0, 0x7f) for ch in value):
        return None
    return value


def digest(token: str) -> str:
    return hashlib.sha256(token.encode('utf8')).hexdigest()


def new_tokens(count: int) -> dict[str, str]:
    if type(count) is not int or not 1 <= count <= 10:
        raise ValueError('Participant count must be 1–10')
    return {role: secrets.token_urlsafe(32) for role in USER_ROLES[:count]}


def load_guest_settings(path: Path) -> int:
    try:
        if path.is_symlink():
            raise ValueError('Refusing symlinked FACO settings')
        data = json.loads(path.read_text(encoding='utf8'))
        count = data.get('guestCount', 10)
        return count if type(count) is int and 1 <= count <= 10 else 10
    except (FileNotFoundError, ValueError, OSError, TypeError, json.JSONDecodeError):
        return 10


def save_guest_settings(path: Path, count: int) -> None:
    if path.is_symlink():
        raise ValueError('Refusing symlinked FACO settings')
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + secrets.token_hex(6) + '.tmp')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf8') as f:
            json.dump({'guestCount': count}, f)
            f.write('\n')
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def make_invite(base: str, role: str, token: str) -> str:
    return f'{base}/#role={quote(role)}&key={quote(token)}'


def configured_ice_servers() -> list[dict[str, Any]]:
    raw = os.getenv('FACO_ICE_SERVERS_JSON')
    if not raw:
        return DEFAULT_ICE_SERVERS
    servers = json.loads(raw)
    if not isinstance(servers, list) or len(servers) > 5:
        raise ValueError('FACO_ICE_SERVERS_JSON must be a JSON array with <=5 servers')
    for item in servers:
        if not isinstance(item, dict) or not isinstance(item.get('urls'), (str, list)):
            raise ValueError('Invalid ICE server list')
    return servers


def valid_base_url(base: str) -> bool:
    try:
        u = urlsplit(base)
        return ((u.scheme == 'https' or (u.scheme == 'http' and u.hostname in ('127.0.0.1', 'localhost')))
                and bool(u.netloc) and bool(u.hostname) and (u.port is None or 0 < u.port < 65536)
                and not u.username and not u.password and u.path in ('', '/') and not u.query and not u.fragment)
    except (ValueError, UnicodeError):
        return False


@dataclass
class VoiceRoom:
    id: str
    members: set[str] = field(default_factory=set)
    pending: dict[str, str] = field(default_factory=dict)  # invitee -> inviter
    timeouts: dict[str, asyncio.Task] = field(default_factory=dict)


class Room:
    """Authenticated signaling coordinator. All shared state is RAM-only."""

    def __init__(self, hashes: dict[str, str], ice_servers: list[dict[str, Any]], ring_seconds: float = 35):
        self.hashes = hashes
        self.ice_servers = ice_servers
        self.clients: dict[str, web.WebSocketResponse] = {}
        self.names: dict[str, str] = {}
        self.calls: dict[str, VoiceRoom] = {}
        self.member_call: dict[str, str] = {}
        self.pending_call: dict[str, str] = {}
        self.lock = asyncio.Lock()
        self.ring_seconds = ring_seconds
        self.pending_auth = 0
        self.chat_limits: dict[str, deque[float]] = {}
        self.cameras_on: set[str] = set()

    def check_token(self, role: str, token: str) -> bool:
        expected = self.hashes.get(role)
        return bool(expected and 30 <= len(token) <= 128 and hmac.compare_digest(digest(token), expected))

    def busy(self, role: str) -> bool:
        return role in self.member_call or role in self.pending_call

    def roster(self) -> list[dict[str, Any]]:
        return [{'role': r, 'online': r in self.clients and not self.clients[r].closed,
                 'name': self.names.get(r) if r in self.clients else None,
                 'busy': self.busy(r)} for r in USER_ROLES if r in self.hashes]

    async def send(self, role: str, data: dict) -> None:
        ws = self.clients.get(role)
        if ws is not None and not ws.closed:
            try:
                await asyncio.wait_for(ws.send_json(data), timeout=2)
            except (ConnectionError, RuntimeError, asyncio.TimeoutError, AssertionError):
                pass

    async def presence(self) -> None:
        roster = self.roster()
        for role in list(self.clients):
            await self.send(role, {'type': 'members', 'people': roster})

    async def authorize(self, ws: web.WebSocketResponse, role: str, token: str, name: Any) -> str | None:
        async with self.lock:
            if not self.check_token(role, token):
                await ws.send_json({'type': 'auth-error', 'message': 'Private QR expired or invalid. Ask for a fresh code.'})
                return None
            clean_name = normalize_name(name)
            if clean_name is None:
                await ws.send_json({'type': 'auth-error', 'message': 'Enter a name of 1–40 characters.'})
                return None
            existing = self.clients.get(role)
            if existing is not None and not existing.closed:
                await ws.send_json({'type': 'auth-error', 'message': 'That QR is already being used on another device.'})
                return None
            self.clients[role] = ws
            self.names[role] = clean_name
            await self.send(role, {'type': 'ready', 'role': role, 'name': clean_name,
                                   'iceServers': self.ice_servers, 'people': self.roster()})
            await self.presence()
        return role

    async def _drop_invitation(self, call: VoiceRoom, target: str, reason: str) -> None:
        inviter = call.pending.pop(target, None)
        self.pending_call.pop(target, None)
        task = call.timeouts.pop(target, None)
        if task and task is not asyncio.current_task():
            task.cancel()
        if inviter:
            await self.send(inviter, {'type': 'invite-result', 'id': call.id, 'target': target, 'reason': reason})
        if target in self.clients and reason not in ('disconnected', 'accepted'):
            await self.send(target, {'type': 'invite-cancelled', 'id': call.id, 'reason': reason})

    async def _finish_if_empty(self, call: VoiceRoom) -> None:
        """Close one-person rooms without pending invites, but keep live group calls."""
        if len(call.members) > 1 or (len(call.members) == 1 and call.pending):
            return
        self.calls.pop(call.id, None)
        for target in list(call.pending):
            await self._drop_invitation(call, target, 'cancelled')
        for member in list(call.members):
            self.member_call.pop(member, None)
            self.cameras_on.discard(member)
            await self.send(member, {'type': 'ended', 'id': call.id, 'reason': 'ended'})
        call.members.clear()

    async def _invite(self, call: VoiceRoom, sender: str, target: Any) -> None:
        if not isinstance(target, str) or target not in self.hashes or target == sender:
            await self.send(sender, {'type': 'error', 'message': 'Choose a different invited person.'})
            return
        if target not in self.clients or self.clients[target].closed:
            await self.send(sender, {'type': 'error', 'message': 'That person is offline.'})
            return
        if self.busy(target):
            await self.send(sender, {'type': 'error', 'message': 'That person is already busy or ringing.'})
            return
        if len(call.members) + len(call.pending) >= 10:
            await self.send(sender, {'type': 'error', 'message': 'This room is full (10 people).'} )
            return
        call.pending[target] = sender
        self.pending_call[target] = call.id
        await self.send(target, {'type': 'incoming', 'id': call.id, 'from': sender,
                                 'fromName': self.names.get(sender), 'members': [
                                   {'role': r, 'name': self.names.get(r)} for r in sorted(call.members)]})
        await self.send(sender, {'type': 'invite-sent', 'id': call.id, 'target': target})
        call.timeouts[target] = asyncio.create_task(self.ring_timeout(call.id, target))
        await self.presence()

    async def ring_timeout(self, call_id: str, target: str) -> None:
        try:
            await asyncio.sleep(self.ring_seconds)
            async with self.lock:
                call = self.calls.get(call_id)
                if call and target in call.pending:
                    await self._drop_invitation(call, target, 'no-answer')
                    await self._finish_if_empty(call)
                    await self.presence()
        except asyncio.CancelledError:
            return

    async def _leave(self, role: str, reason: str = 'left') -> None:
        self.cameras_on.discard(role)
        pending_id = self.pending_call.get(role)
        if pending_id:
            call = self.calls.get(pending_id)
            if call:
                await self._drop_invitation(call, role, reason)
                await self._finish_if_empty(call)
        call_id = self.member_call.pop(role, None)
        if call_id:
            call = self.calls.get(call_id)
            if call:
                call.members.discard(role)
                # Invitations created by someone who has left must not outlive them.
                for invitee, inviter in list(call.pending.items()):
                    if inviter == role:
                        await self._drop_invitation(call, invitee, 'inviter-left')
                await self.send(role, {'type': 'ended', 'id': call.id, 'reason': reason})
                for other in list(call.members):
                    await self.send(other, {'type': 'member-left', 'id': call.id, 'role': role, 'reason': reason})
                if not call.members:
                    for invitee in list(call.pending):
                        await self._drop_invitation(call, invitee, 'cancelled')
                await self._finish_if_empty(call)
        await self.presence()

    async def disconnect(self, role: str, ws: web.WebSocketResponse) -> None:
        async with self.lock:
            if self.clients.get(role) is not ws:
                return
            del self.clients[role]
            self.names.pop(role, None)
            self.chat_limits.pop(role, None)
            await self._leave(role, 'disconnected')

    async def rotate(self, new_hashes: dict[str, str]) -> None:
        async with self.lock:
            old = list(self.clients.values())
            self.clients.clear()
            self.names.clear()
            self.hashes = new_hashes
            for call in self.calls.values():
                for task in call.timeouts.values():
                    task.cancel()
            self.calls.clear()
            self.member_call.clear()
            self.pending_call.clear()
            self.chat_limits.clear()
            self.cameras_on.clear()
        for ws in old:
            try:
                await ws.send_json({'type': 'session-expired', 'message': 'QR invitations refreshed; scan a new code.'})
            except (ConnectionError, RuntimeError):
                pass
            await ws.close(code=4001, message=b'Invites rotated')

    async def handle(self, role: str, ws: web.WebSocketResponse, data: dict) -> None:
        kind = data.get('type')
        async with self.lock:
            if self.clients.get(role) is not ws:
                return
            if kind == 'dial':
                if self.busy(role):
                    await self.send(role, {'type': 'error', 'message': 'You are already in a call or receiving one. Add people to your current call.'})
                    return
                call = VoiceRoom(secrets.token_hex(12), {role})
                self.calls[call.id] = call
                self.member_call[role] = call.id
                await self._invite(call, role, data.get('target'))
                if not call.pending:
                    await self._finish_if_empty(call)
                return
            if kind == 'invite':
                call = self.calls.get(self.member_call.get(role, ''))
                if not call or call.id != data.get('id'):
                    await self.send(role, {'type': 'error', 'message': 'Join a call before adding someone.'})
                    return
                await self._invite(call, role, data.get('target'))
                return
            if kind == 'answer':
                call = self.calls.get(self.pending_call.get(role, ''))
                if not call or call.id != data.get('id') or role not in call.pending:
                    return
                await self._drop_invitation(call, role, 'accepted')
                existing = sorted(call.members)
                call.members.add(role)
                self.member_call[role] = call.id
                people = [{'role': r, 'name': self.names.get(r),
                           'video': r in self.cameras_on} for r in sorted(call.members)]
                await self.send(role, {'type': 'joined', 'id': call.id, 'members': people})
                for member in existing:
                    await self.send(member, {'type': 'member-joined', 'id': call.id,
                                             'role': role, 'name': self.names.get(role), 'video': False})
                await self.presence()
                return
            if kind == 'decline':
                call = self.calls.get(self.pending_call.get(role, ''))
                if call and call.id == data.get('id'):
                    await self._drop_invitation(call, role, 'declined')
                    await self._finish_if_empty(call)
                    await self.presence()
                return
            if kind == 'end':
                if self.member_call.get(role) == data.get('id') or self.pending_call.get(role) == data.get('id'):
                    await self._leave(role, 'left')
                return
            if kind == 'signal':
                call = self.calls.get(self.member_call.get(role, ''))
                target = data.get('target')
                if not call or call.id != data.get('id') or not isinstance(target, str) or target not in call.members or target == role:
                    return
                payload = data.get('data')
                if valid_signal(payload, role, target):
                    await self.send(target, {'type': 'signal', 'id': call.id, 'from': role, 'data': payload})
                return
            if kind == 'video':
                call = self.calls.get(self.member_call.get(role, ''))
                enabled = data.get('enabled')
                if call and call.id == data.get('id') and role in call.members and type(enabled) is bool:
                    if enabled:
                        self.cameras_on.add(role)
                    else:
                        self.cameras_on.discard(role)
                    for member in call.members - {role}:
                        await self.send(member, {'type': 'video', 'id': call.id,
                                                 'from': role, 'enabled': enabled})
                return
            if kind == 'ptt':
                call = self.calls.get(self.member_call.get(role, ''))
                if call and call.id == data.get('id') and type(data.get('active')) is bool:
                    for member in call.members - {role}:
                        await self.send(member, {'type': 'ptt', 'id': call.id, 'from': role, 'active': data['active']})
                return
            if kind == 'chat':
                content = normalize_message(data.get('text'))
                target = data.get('target')
                if content is None:
                    await self.send(role, {'type': 'error', 'message': 'Messages must contain 1–2000 characters.'})
                    return
                window = self.chat_limits.setdefault(role, deque())
                now = time.monotonic()
                while window and now - window[0] > 5:
                    window.popleft()
                if len(window) >= 12:
                    await self.send(role, {'type': 'error', 'message': 'Too many messages. Please slow down.'})
                    return
                window.append(now)
                message = {'type': 'chat', 'from': role, 'fromName': self.names.get(role),
                           'text': content, 'time': int(time.time() * 1000)}
                if target == 'circle':
                    message['target'] = 'circle'
                    for member in list(self.clients):
                        await self.send(member, message)
                elif target == 'room':
                    call = self.calls.get(self.member_call.get(role, ''))
                    if not call or len(call.members) < 2:
                        await self.send(role, {'type': 'error', 'message': 'Join a conversation to message the group.'})
                        return
                    message.update({'target': 'room', 'id': call.id})
                    for member in call.members:
                        await self.send(member, message)
                elif isinstance(target, str) and target in self.clients and target != role:
                    message['target'] = target
                    await self.send(target, message)
                    await self.send(role, message)
                else:
                    await self.send(role, {'type': 'error', 'message': 'Select an online recipient.'})
                return
            await self.send(role, {'type': 'error', 'message': 'Unknown request.'})


def valid_signal(data: Any, sender: str, target: str) -> bool:
    if not isinstance(data, dict):
        return False
    kind = data.get('type')
    if kind in ('offer', 'answer'):
        # Unique caller/callee offerer selection prevents cross-offers and SDP glare.
        if (kind == 'offer') != (sender < target):
            return False
        return isinstance(data.get('sdp'), str) and 1 <= len(data['sdp']) <= 32768
    if kind == 'candidate':
        candidate = data.get('candidate')
        return candidate is None or (isinstance(candidate, dict)
               and isinstance(candidate.get('candidate'), str) and len(candidate['candidate']) <= 4096
               and (candidate.get('sdpMid') is None or isinstance(candidate.get('sdpMid'), str))
               and (candidate.get('sdpMLineIndex') is None or type(candidate.get('sdpMLineIndex')) is int))
    return False


def valid_origin(request: web.Request) -> bool:
    origin = request.headers.get('Origin', '')
    try:
        parsed = urlsplit(origin)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc) and parsed.netloc.lower() == request.host.lower()
    except (ValueError, UnicodeError):
        return False


class ControlState:
    """Server manages everyone; local administrator controls QRs, but never joins calls."""
    def __init__(self, count: int = 10, *, base_url: str = '', ice_servers: list | None = None,
                 ring_seconds: float = 35, settings_path: Path | None = None):
        self.guest_count = count  # retained settings format from earlier releases
        self.settings_path = settings_path
        self.tokens = new_tokens(count)
        self.room = Room({r: digest(t) for r, t in self.tokens.items()},
                         ice_servers if ice_servers is not None else configured_ice_servers(), ring_seconds)
        self.base_url = base_url.rstrip('/')
        self.epoch = 1
        self.reason = 'Application started'
        self.admin_token = secrets.token_urlsafe(32)
        self.tunnel_state = 'Waiting for tunnel' if not self.base_url else 'Active'
        self.changed = asyncio.Lock()

    def snapshot(self) -> dict[str, Any]:
        return {
            'version': '0.6.2', 'baseUrl': self.base_url, 'epoch': self.epoch,
            'reason': self.reason, 'guestCount': self.guest_count,
            'tunnelState': self.tunnel_state,
            'online': [r for r in self.room.clients if not self.room.clients[r].closed],
            'activeCalls': [{'id': c.id, 'members': sorted(c.members), 'ringing': len(c.pending)}
                            for c in self.room.calls.values()],
            'invites': [{'role': r, 'label': f'Person {int(r[-2:]):02d}',
                         'url': make_invite(self.base_url, r, token) if self.base_url else ''}
                        for r, token in self.tokens.items()],
        }

    async def rotate(self, reason: str, *, count: int | None = None) -> None:
        async with self.changed:
            if count is not None:
                if type(count) is not int or not 1 <= count <= 10:
                    raise ValueError('Participant count must be between 1 and 10')
                if self.settings_path:
                    save_guest_settings(self.settings_path, count)
                self.guest_count = count
            replacement = new_tokens(self.guest_count)
            await self.room.rotate({r: digest(t) for r, t in replacement.items()})
            self.tokens = replacement
            self.epoch += 1
            self.reason = reason

    async def set_tunnel(self, base: str, *, restarted: bool = False) -> None:
        if not valid_base_url(base):
            raise ValueError('Invalid tunnel URL')
        base = base.rstrip('/')
        if self.base_url and (self.base_url != base or restarted):
            await self.rotate('Cloudflare connection restarted; all invites refreshed')
        self.base_url = base
        self.tunnel_state = 'Active'


def no_cache(request: web.Request, resp: web.StreamResponse) -> web.StreamResponse:
    resp.headers.update({
        'Cache-Control': 'no-store, max-age=0, private',
        'Pragma': 'no-cache',
        'Expires': '0',
        'X-Robots-Tag': 'noindex, nofollow, noarchive, nosnippet',
        'X-Content-Type-Options': 'nosniff',
        'Referrer-Policy': 'no-referrer',
        'X-Frame-Options': 'DENY',
        'Permissions-Policy': 'microphone=(self), camera=(self), geolocation=()',
        'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:; media-src 'self' blob:; object-src 'none'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
    })
    return resp


@web.middleware
async def security_headers(request: web.Request, handler):
    return no_cache(request, await handler(request))


STATE = web.AppKey('state', ControlState)


async def ws_handler(request: web.Request) -> web.StreamResponse:
    if not valid_origin(request):
        raise web.HTTPForbidden(text='Invalid WebSocket origin')
    room = request.app[STATE].room
    async with room.lock:
        if room.pending_auth >= 16:
            raise web.HTTPServiceUnavailable(text='Too many pending connections')
        room.pending_auth += 1
    pending = True
    ws = web.WebSocketResponse(heartbeat=25, max_msg_size=MAX_MSG_SIZE, compress=False)
    role: str | None = None
    try:
        await ws.prepare(request)
        msg = await asyncio.wait_for(ws.receive(), timeout=10)
        if msg.type != WSMsgType.TEXT:
            return ws
        try:
            data = msg.json()
        except (ValueError, TypeError):
            return ws
        if not isinstance(data, dict) or data.get('type') != 'auth':
            return ws
        role_str, token = data.get('role'), data.get('token')
        if not isinstance(role_str, str) or not isinstance(token, str):
            return ws
        role = await room.authorize(ws, role_str, token, data.get('name'))
        async with room.lock:
            room.pending_auth -= 1
            pending = False
        if role is None:
            return ws
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = msg.json()
                except (ValueError, TypeError):
                    continue
                if isinstance(data, dict):
                    await room.handle(role, ws, data)
            elif msg.type == WSMsgType.ERROR:
                break
    except (asyncio.TimeoutError, ConnectionResetError):
        pass
    finally:
        if pending:
            async with room.lock:
                room.pending_auth -= 1
        if role:
            await room.disconnect(role, ws)
        await ws.close()
    return ws


async def health(_: web.Request) -> web.Response:
    return web.json_response({'ok': True, 'service': 'faco-crumble', 'version': '0.6.2'})


async def static_file(request: web.Request) -> web.Response:
    name = request.match_info.get('asset', '') or 'index.html'
    mime = {'index.html': 'text/html', 'app.js': 'application/javascript',
            'style.css': 'text/css', 'favicon.svg': 'image/svg+xml'}
    if name not in mime:
        raise web.HTTPNotFound()
    kind = mime[name]
    return web.Response(body=(ROOT / 'public' / name).read_bytes(), content_type=kind,
                        charset='utf-8' if kind.startswith('text/') or 'javascript' in kind else None)


def create_app(state: ControlState) -> web.Application:
    app = web.Application(middlewares=[security_headers], client_max_size=MAX_MSG_SIZE)
    app[STATE] = state
    app.router.add_get('/healthz', health)
    app.router.add_get('/socket', ws_handler)
    app.router.add_get('/', static_file)
    app.router.add_get('/{asset}', static_file)
    return app


@web.middleware
async def admin_guard(request: web.Request, handler):
    """Deny reverse-proxy/public attempts, DNS rebinding, and cross-site requests."""
    host = request.headers.get('Host', '').lower()
    if host not in (f'127.0.0.1:{request.app[ADMIN_PORT]}', f'localhost:{request.app[ADMIN_PORT]}'):
        raise web.HTTPForbidden(text='Admin GUI requires localhost')
    if request.remote not in ('127.0.0.1', '::1'):
        raise web.HTTPForbidden(text='Admin GUI requires local computer')
    origin = request.headers.get('Origin')
    if origin and origin.lower() not in (f'http://127.0.0.1:{request.app[ADMIN_PORT]}',
                                          f'http://localhost:{request.app[ADMIN_PORT]}'):
        raise web.HTTPForbidden(text='Cross-site access denied')
    if request.headers.get('Sec-Fetch-Site', 'same-origin') not in ('same-origin', 'none'):
        raise web.HTTPForbidden(text='Cross-site access denied')
    if request.path.startswith('/api/') or request.path.startswith('/qr/'):
        candidate = request.headers.get('X-FACO-Admin', '')
        if not hmac.compare_digest(candidate, request.app[STATE].admin_token):
            raise web.HTTPForbidden(text='Admin authorization required')
    return no_cache(request, await handler(request))


ADMIN_PORT = web.AppKey('admin-port', int)


async def admin_html(request: web.Request) -> web.Response:
    name = request.match_info.get('asset') or 'index.html'
    mime = {'index.html': 'text/html', 'admin.js': 'application/javascript',
            'admin.css': 'text/css', 'favicon.svg': 'image/svg+xml'}
    if name not in mime:
        raise web.HTTPNotFound()
    kind = mime[name]
    path = ROOT / 'admin' / name if name != 'favicon.svg' else ROOT / 'public' / name
    return web.Response(body=path.read_bytes(), content_type=kind,
                        charset='utf-8' if kind.startswith('text/') or 'javascript' in kind else None)


async def admin_state(request: web.Request) -> web.Response:
    return web.json_response(request.app[STATE].snapshot())


async def admin_post(request: web.Request) -> web.Response:
    state = request.app[STATE]
    if request.content_type != 'application/json':
        raise web.HTTPUnsupportedMediaType()
    try:
        data = await request.json()
    except (ValueError, TypeError):
        raise web.HTTPBadRequest(text='Invalid JSON')
    if not isinstance(data, dict):
        raise web.HTTPBadRequest(text='Invalid request')
    action = request.match_info['action']
    if action == 'rotate':
        await state.rotate('All credentials manually reissued')
    elif action == 'guest-count':
        count = data.get('count')
        if type(count) is not int or not 1 <= count <= 10:
            raise web.HTTPBadRequest(text='Participant count must be 1–10')
        if count != state.guest_count:
            await state.rotate('Participant slots updated; credentials refreshed', count=count)
    else:
        raise web.HTTPNotFound()
    return web.json_response(state.snapshot())


async def admin_qr(request: web.Request) -> web.Response:
    state = request.app[STATE]
    role = request.match_info['role']
    if not state.base_url:
        raise web.HTTPServiceUnavailable(text='Tunnel not ready')
    if role == 'landing':
        url = state.base_url + '/'
    elif role in state.tokens:
        url = make_invite(state.base_url, role, state.tokens[role])
    else:
        raise web.HTTPNotFound()
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,
                       box_size=10, border=4, image_factory=SvgPathImage)
    qr.add_data(url)
    qr.make(fit=True)
    svg = qr.make_image().to_string().replace(b'>', b'><rect width="100%" height="100%" fill="white"/>', 1)
    return web.Response(body=svg, content_type='image/svg+xml')


def create_admin_app(state: ControlState, port: int) -> web.Application:
    app = web.Application(middlewares=[admin_guard], client_max_size=4096)
    app[STATE], app[ADMIN_PORT] = state, port
    app.router.add_get('/api/state', admin_state)
    app.router.add_post('/api/{action}', admin_post)
    app.router.add_get('/qr/{role}.svg', admin_qr)
    app.router.add_get('/', admin_html)
    app.router.add_get('/{asset}', admin_html)
    return app
