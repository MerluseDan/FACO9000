/// FACO Crumble mobile session coordinator. All credentials, names, rooms and
/// messages are RAM-only. No sqlite, SharedPreferences, local files or logging.
/// Browser protocol is compatible with FACO Crumble v0.5.1 (Ubuntu).
import 'dart:async';
import 'dart:collection';
import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:crypto/crypto.dart';

const defaultIceServers = <Map<String, dynamic>>[
  {'urls': <String>['stun:stun.l.google.com:19302']},
];

String? normalName(dynamic name) {
  if (name is! String) return null;
  final clean = name.trim();
  if (clean.runes.isEmpty || clean.runes.length > 40) return null;
  for (final ch in clean.runes) {
    if (ch < 32 || (ch >= 0x7f && ch < 0xa0) || ch == 0x2028 || ch == 0x2029) return null;
  }
  return clean;
}

String? normalMessage(dynamic text) {
  if (text is! String || text.length > 2032) return null;
  final cleaned = text.trim();
  if (cleaned.isEmpty || cleaned.runes.length > 2000) return null;
  if (cleaned.runes.contains(0) || cleaned.runes.contains(127)) return null;
  return cleaned;
}

String generateToken() {
  final rand = Random.secure();
  return base64UrlEncode(Uint8List.fromList(List.generate(32, (_) => rand.nextInt(256)))).replaceAll('=', '');
}

String generateId() {
  final rand = Random.secure();
  return List.generate(12, (_) => rand.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
}

String tokenDigest(String token) => sha256.convert(utf8.encode(token)).toString();

bool constantTimeEqual(String a, String b) {
  if (a.length != b.length) return false;
  var delta = 0;
  for (var i = 0; i < a.length; i++) {
    delta |= a.codeUnitAt(i) ^ b.codeUnitAt(i);
  }
  return delta == 0;
}

class VoiceRoom {
  VoiceRoom(this.id, this.origin) { members.add(origin); }
  final String id;
  final String origin;
  final Set<String> members = {};
  final Map<String, String> pending = {};
  final Map<String, Timer> timers = {};
}

class CrumbleServer {
  CrumbleServer({
    required this.assetLoader,
    this.port = 8787,
    this.ringDuration = const Duration(seconds: 35),
    this.iceServers = defaultIceServers,
  });

  final Future<Uint8List> Function(String name) assetLoader;
  final int port;
  final Duration ringDuration;
  final List<Map<String, dynamic>> iceServers;
  HttpServer? _http;
  final Map<String, WebSocket> _clients = {};
  final Map<String, String> _names = {};
  final Map<String, VoiceRoom> _rooms = {};
  final Map<String, String> _memberRoom = {};
  final Set<String> _camerasOn = <String>{};
  final Map<String, String> _pendingRoom = {};
  final Map<String, Queue<DateTime>> _chatTimes = {};
  final Map<String, String> _tokenHashes = {};
  final Map<String, String> _tokens = {};
  final Set<WebSocket> _pendingAuth = {};
  final Map<WebSocket, Timer> _authTimeouts = {};
  String _publicBaseUrl = '';
  String _reason = 'No session';
  int _epoch = 0;
  int _participantCount = 10;
  int _authAttempts = 0;
  bool _closed = false;
  final StreamController<Map<String, dynamic>> _events = StreamController.broadcast();

  Stream<Map<String, dynamic>> get events => _events.stream;
  bool get isRunning => _http != null;
  int get actualPort => _http?.port ?? port;
  int get participantCount => _participantCount;
  int get epoch => _epoch;
  String get publicBaseUrl => _publicBaseUrl;
  int get onlineCount => _clients.length;
  int get activeCallCount => _rooms.values.where((r) => r.members.length >= 2).length;

  String _roleAt(int i) => 'user${(i + 1).toString().padLeft(2, '0')}';
  Map<String, String> get invitationTokens => Map.unmodifiable(_tokens);
  String get localBaseUrl => 'http://127.0.0.1:$actualPort';
  String get shareBaseUrl => _publicBaseUrl.isNotEmpty ? _publicBaseUrl : localBaseUrl;

  String invitation(int index, {String? baseUrl}) {
    if (index < 0 || index >= _participantCount) throw RangeError.index(index, _tokens);
    final role = _roleAt(index);
    final token = _tokens[role]!;
    return '${(baseUrl ?? shareBaseUrl).replaceAll(RegExp(r"/$"), "")}/#role=$role&key=$token';
  }

  Future<void> start({int participantCount = 10}) async {
    if (_http != null) throw StateError('Session is already running.');
    if (participantCount < 1 || participantCount > 10) throw RangeError.range(participantCount, 1, 10);
    _closed = false;
    _participantCount = participantCount;
    _epoch = 0;
    _publicBaseUrl = '';
    _reason = 'Session started';
    _issueTokens();
    try {
      _http = await HttpServer.bind(InternetAddress.anyIPv4, port, shared: false);
      _http!.listen(_handleRequest, onError: (Object e) => _notify({'type': 'error', 'message': 'Server failure: $e'}));
      _notify({'type': 'started', 'port': actualPort});
    } catch (_) {
      _tokens.clear();
      _tokenHashes.clear();
      rethrow;
    }
  }

  void _issueTokens() {
    _tokens.clear();
    _tokenHashes.clear();
    for (var i = 0; i < _participantCount; i++) {
      final role = _roleAt(i);
      final token = generateToken();
      _tokens[role] = token;
      _tokenHashes[role] = tokenDigest(token);
    }
    _epoch++;
  }

  void _notify(Map<String, dynamic> data) {
    if (!_events.isClosed) _events.add(data);
  }

  Map<String, dynamic> snapshot() => {
    'epoch': _epoch,
    'baseUrl': shareBaseUrl,
    'publicUrl': _publicBaseUrl,
    'port': actualPort,
    'count': _participantCount,
    'reason': _reason,
    'online': _clients.length,
    'activeCalls': activeCallCount,
    'invites': List.generate(_participantCount, (i) => {
      'role': _roleAt(i), 'url': invitation(i), 'label': 'Person ${(i + 1).toString().padLeft(2, '0')}',
    }),
  };

  void setPublicUrl(String url, {bool reconnected = false}) {
    final parsed = Uri.tryParse(url);
    if (parsed == null || parsed.scheme != 'https' || parsed.host.isEmpty ||
        parsed.userInfo.isNotEmpty || parsed.hasQuery || parsed.hasFragment ||
        (parsed.path.isNotEmpty && parsed.path != '/')) {
      throw ArgumentError('Public URL must be a bare HTTPS origin.');
    }
    final base = parsed.origin;
    if ((_publicBaseUrl.isNotEmpty && base != _publicBaseUrl) || reconnected) {
      rotate('Public tunnel reconnected');
    }
    _publicBaseUrl = base;
    _notify({'type': 'url', 'url': _publicBaseUrl, 'epoch': _epoch});
  }

  void rotate([String reason = 'Invitations refreshed']) {
    if (!isRunning) throw StateError('Session not started.');
    _reason = reason;
    for (final socket in _clients.values.toList()) {
      _safeSend(socket, {'type': 'session-expired', 'message': 'QR invitations refreshed; scan a new code.'});
      socket.close(4001, 'Invites rotated');
    }
    for (final socket in _pendingAuth.toList()) { socket.close(4001, 'Session reset'); }
    for (final room in _rooms.values) { for (final timer in room.timers.values) { timer.cancel(); } }
    for (final timer in _authTimeouts.values) { timer.cancel(); }
    _clients.clear(); _names.clear(); _rooms.clear(); _memberRoom.clear();
    _pendingRoom.clear(); _chatTimes.clear(); _pendingAuth.clear(); _authTimeouts.clear();
    _camerasOn.clear();
    _issueTokens();
    _notify({'type': 'rotated', 'epoch': _epoch, 'reason': reason});
  }

  Future<void> stop() async {
    if (_closed) return;
    _closed = true;
    for (final socket in _clients.values.toList()) {
      _safeSend(socket, {'type': 'session-expired', 'message': 'The host ended this session.'});
      socket.close(4001, 'Host ended session');
    }
    for (final socket in _pendingAuth.toList()) { socket.close(4001, 'Session ended'); }
    for (final timer in _authTimeouts.values) { timer.cancel(); }
    for (final room in _rooms.values) { for (final timer in room.timers.values) { timer.cancel(); } }
    _clients.clear(); _names.clear(); _rooms.clear(); _memberRoom.clear();
    _pendingRoom.clear(); _chatTimes.clear(); _pendingAuth.clear(); _authTimeouts.clear();
    _tokenHashes.clear(); _tokens.clear(); _camerasOn.clear(); _publicBaseUrl = '';
    final http = _http;
    _http = null;
    await http?.close(force: true);
    _notify({'type': 'stopped'});
    await _events.close();
  }

  static const securityHeaders = <String, String>{
    'Cache-Control': 'no-store, max-age=0, private',
    'Pragma': 'no-cache',
    'Expires': '0',
    'X-Robots-Tag': 'noindex, nofollow, noarchive, nosnippet',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'no-referrer',
    'X-Frame-Options': 'DENY',
    'Permissions-Policy': 'microphone=(self), camera=(self), geolocation=()',
    'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; connect-src 'self' ws: wss:; media-src 'self' blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
  };

  bool _validOrigin(HttpRequest request) {
    final raw = request.headers.value('origin') ?? '';
    final uri = Uri.tryParse(raw);
    if (uri == null || !['http', 'https'].contains(uri.scheme)) return false;
    if (uri.userInfo.isNotEmpty || uri.host.isEmpty) return false;
    final originHost = uri.authority.toLowerCase();
    final requestedHost = (request.headers.value(HttpHeaders.hostHeader) ?? '').toLowerCase();
    final isLocal = uri.host == '127.0.0.1' || uri.host == 'localhost';
    return (originHost == requestedHost) ||
        (isLocal && uri.port == actualPort) ||
        (_publicBaseUrl.isNotEmpty && uri.origin == _publicBaseUrl);
  }

  Future<void> _handleRequest(HttpRequest request) async {
    final response = request.response;
    securityHeaders.forEach(response.headers.set);
    response.headers.set('X-FACO-Mobile', '0.6.1');
    try {
      if (request.method != 'GET' || _closed) {
        response.statusCode = HttpStatus.methodNotAllowed;
        await response.close();
        return;
      }
      if (request.uri.path == '/socket') {
        if (!_validOrigin(request) || !WebSocketTransformer.isUpgradeRequest(request)) {
          response.statusCode = HttpStatus.forbidden;
          await response.close();
          return;
        }
        if (_pendingAuth.length >= 16 || _authAttempts > 200) {
          response.statusCode = HttpStatus.serviceUnavailable;
          await response.close();
          return;
        }
        final socket = await WebSocketTransformer.upgrade(request, compression: CompressionOptions.compressionOff);
        _attach(socket);
        return;
      }
      if (request.uri.path == '/healthz') {
        response.headers.contentType = ContentType.json;
        response.write(jsonEncode({'ok': true, 'service': 'faco-crumble-mobile', 'version': '0.6.1'}));
        await response.close();
        return;
      }
      final file = switch (request.uri.path) {
        '/' => 'index.html',
        '/index.html' => 'index.html',
        '/app.js' => 'app.js',
        '/style.css' => 'style.css',
        '/favicon.svg' => 'favicon.svg',
        _ => '',
      };
      if (file.isEmpty) {
        response.statusCode = HttpStatus.notFound;
        await response.close();
        return;
      }
      final bytes = await assetLoader(file);
      response.headers.contentType = switch (file) {
        'index.html' => ContentType('text', 'html', charset: 'utf-8'),
        'app.js' => ContentType('application', 'javascript', charset: 'utf-8'),
        'style.css' => ContentType('text', 'css', charset: 'utf-8'),
        _ => ContentType('image', 'svg+xml'),
      };
      response.add(bytes);
      await response.close();
    } catch (_) {
      try { response.statusCode = HttpStatus.internalServerError; await response.close(); } catch (_) {}
    }
  }

  bool _authorized(String role, String token) {
    if (token.length < 30 || token.length > 128) return false;
    final expected = _tokenHashes[role];
    return expected != null && constantTimeEqual(tokenDigest(token), expected);
  }

  bool _busy(String role) => _memberRoom.containsKey(role) || _pendingRoom.containsKey(role);
  List<Map<String, dynamic>> _roster() => _tokenHashes.keys.map((role) => <String, dynamic>{
    'role': role,
    'online': _clients.containsKey(role),
    'name': _names[role],
    'busy': _busy(role),
  }).toList();

  void _safeSend(WebSocket socket, Map<String, dynamic> payload) {
    try { socket.add(jsonEncode(payload)); } catch (_) {}
  }

  void _send(String role, Map<String, dynamic> payload) {
    final ws = _clients[role];
    if (ws != null) _safeSend(ws, payload);
  }

  void _presence() {
    final roster = _roster();
    for (final r in _clients.keys.toList()) { _send(r, {'type': 'members', 'people': roster}); }
    _notify({'type': 'presence', 'online': _clients.length, 'activeCalls': activeCallCount});
  }

  void _attach(WebSocket ws) {
    ws.pingInterval = const Duration(seconds: 25);
    _pendingAuth.add(ws);
    _authAttempts++;
    Timer(const Duration(minutes: 1), () { if (_authAttempts > 0) _authAttempts--; });
    _authTimeouts[ws] = Timer(const Duration(seconds: 10), () {
      if (_pendingAuth.contains(ws)) ws.close(4001, 'Authentication timed out');
    });
    String? role;
    ws.listen((dynamic message) {
      if (message is! String || message.length > 65536) {
        ws.close(4003, 'Invalid message');
        return;
      }
      dynamic decoded;
      try { decoded = jsonDecode(message); } catch (_) { ws.close(4003, 'Invalid JSON'); return; }
      if (decoded is! Map<String, dynamic>) { ws.close(4003, 'Invalid message'); return; }
      if (role == null) {
        if (decoded['type'] != 'auth' || decoded['role'] is! String || decoded['token'] is! String) {
          ws.close(4003, 'Authentication required');
          return;
        }
        final newRole = decoded['role'] as String;
        final token = decoded['token'] as String;
        final name = normalName(decoded['name']);
        if (!_authorized(newRole, token)) {
          _safeSend(ws, {'type': 'auth-error', 'message': 'Private QR expired or invalid. Ask for a fresh code.'});
          ws.close(4003, 'Unauthorized'); return;
        }
        if (name == null) {
          _safeSend(ws, {'type': 'auth-error', 'message': 'Enter a name of 1–40 characters.'});
          ws.close(4003, 'Bad name'); return;
        }
        if (_clients.containsKey(newRole)) {
          _safeSend(ws, {'type': 'auth-error', 'message': 'That QR is already being used on another device.'});
          ws.close(4003, 'In use'); return;
        }
        role = newRole;
        _pendingAuth.remove(ws);
        _authTimeouts.remove(ws)?.cancel();
        _clients[newRole] = ws;
        _names[newRole] = name;
        _send(newRole, {'type': 'ready', 'role': newRole, 'name': name, 'iceServers': iceServers, 'people': _roster()});
        _presence();
        return;
      }
      if (_clients[role] == ws) _handle(role!, decoded);
    }, onError: (_) {}, onDone: () {
      _pendingAuth.remove(ws);
      _authTimeouts.remove(ws)?.cancel();
      if (role != null && identical(_clients[role], ws)) {
        _clients.remove(role);
        _names.remove(role);
        _chatTimes.remove(role);
        _leave(role!, 'disconnected');
      }
    }, cancelOnError: true);
  }

  void _dropInvite(VoiceRoom call, String target, String reason) {
    final inviter = call.pending.remove(target);
    _pendingRoom.remove(target);
    call.timers.remove(target)?.cancel();
    if (inviter != null) _send(inviter, {'type': 'invite-result', 'id': call.id, 'target': target, 'reason': reason});
    if (_clients.containsKey(target) && reason != 'disconnected' && reason != 'accepted') {
      _send(target, {'type': 'invite-cancelled', 'id': call.id, 'reason': reason});
    }
  }

  void _finishIfEmpty(VoiceRoom room) {
    if (room.members.length > 1 || (room.members.length == 1 && room.pending.isNotEmpty)) return;
    _rooms.remove(room.id);
    for (final target in room.pending.keys.toList()) { _dropInvite(room, target, 'cancelled'); }
    for (final member in room.members.toList()) {
      _memberRoom.remove(member);
      _send(member, {'type': 'ended', 'id': room.id, 'reason': 'ended'});
      _camerasOn.remove(member);
    }
    room.members.clear();
  }

  void _invite(VoiceRoom call, String sender, dynamic target) {
    if (target is! String || !_tokenHashes.containsKey(target) || target == sender) {
      _send(sender, {'type': 'error', 'message': 'Choose a different invited person.'}); return;
    }
    if (!_clients.containsKey(target)) {
      _send(sender, {'type': 'error', 'message': 'That person is offline.'}); return;
    }
    if (_busy(target)) {
      _send(sender, {'type': 'error', 'message': 'That person is already busy or ringing.'}); return;
    }
    if (call.members.length + call.pending.length >= 10) {
      _send(sender, {'type': 'error', 'message': 'This room is full (10 people).'}); return;
    }
    call.pending[target] = sender;
    _pendingRoom[target] = call.id;
    _send(target, {'type': 'incoming', 'id': call.id, 'from': sender, 'fromName': _names[sender],
      'members': (call.members.toList()..sort()).map((r) => {'role': r, 'name': _names[r]}).toList()});
    _send(sender, {'type': 'invite-sent', 'id': call.id, 'target': target});
    call.timers[target] = Timer(ringDuration, () {
      if (_rooms[call.id] == call && call.pending.containsKey(target)) {
        _dropInvite(call, target, 'no-answer');
        _finishIfEmpty(call);
        _presence();
      }
    });
    _presence();
  }

  void _leave(String role, String reason) {
    final waiting = _pendingRoom[role];
    if (waiting != null) {
      final call = _rooms[waiting];
      if (call != null) { _dropInvite(call, role, reason); _finishIfEmpty(call); }
    }
    _camerasOn.remove(role);
    final callId = _memberRoom.remove(role);
    if (callId != null) {
      final call = _rooms[callId];
      if (call != null) {
        call.members.remove(role);
        for (final target in call.pending.keys.toList()) {
          if (call.pending[target] == role) _dropInvite(call, target, 'inviter-left');
        }
        _send(role, {'type': 'ended', 'id': call.id, 'reason': reason});
        for (final other in call.members.toList()) {
          _send(other, {'type': 'member-left', 'id': call.id, 'role': role, 'reason': reason});
        }
        if (call.members.isEmpty) {
          for (final target in call.pending.keys.toList()) { _dropInvite(call, target, 'cancelled'); }
        }
        _finishIfEmpty(call);
      }
    }
    _presence();
  }

  bool _validSignal(dynamic data, String sender, String target) {
    if (data is! Map<String, dynamic>) return false;
    final type = data['type'];
    if (type == 'offer' || type == 'answer') {
      if ((type == 'offer') != (sender.compareTo(target) < 0)) return false;
      return data['sdp'] is String && (data['sdp'] as String).isNotEmpty && (data['sdp'] as String).length <= 32768;
    }
    if (type == 'candidate') {
      final candidate = data['candidate'];
      if (candidate == null) return true;
      if (candidate is! Map<String, dynamic>) return false;
      return candidate['candidate'] is String && (candidate['candidate'] as String).length <= 4096 &&
        (candidate['sdpMid'] == null || candidate['sdpMid'] is String) &&
        (candidate['sdpMLineIndex'] == null || candidate['sdpMLineIndex'] is int);
    }
    return false;
  }

  void _handle(String role, Map<String, dynamic> data) {
    switch (data['type']) {
      case 'dial':
        if (_busy(role)) { _send(role, {'type': 'error', 'message': 'Already in a call or receiving one.'}); return; }
        final call = VoiceRoom(generateId(), role);
        _rooms[call.id] = call;
        _memberRoom[role] = call.id;
        _invite(call, role, data['target']);
        if (call.pending.isEmpty) _finishIfEmpty(call);
        break;
      case 'invite':
        final call = _rooms[_memberRoom[role]];
        if (call == null || call.id != data['id']) {
          _send(role, {'type': 'error', 'message': 'Join a call before adding someone.'}); return;
        }
        _invite(call, role, data['target']);
        break;
      case 'answer':
        final call = _rooms[_pendingRoom[role]];
        if (call == null || call.id != data['id'] || !call.pending.containsKey(role)) return;
        _dropInvite(call, role, 'accepted');
        final existing = call.members.toList()..sort();
        call.members.add(role);
        _memberRoom[role] = call.id;
        final people = call.members.map((r) => {'role': r, 'name': _names[r], 'video': _camerasOn.contains(r)}).toList()..sort((a, b) => (a['role']?.toString() ?? '').compareTo(b['role']?.toString() ?? ''));
        _send(role, {'type': 'joined', 'id': call.id, 'members': people});
        for (final member in existing) {
          _send(member, {'type': 'member-joined', 'id': call.id, 'role': role, 'name': _names[role], 'video': false});
        }
        _presence();
        break;
      case 'decline':
        final call = _rooms[_pendingRoom[role]];
        if (call != null && call.id == data['id']) {
          _dropInvite(call, role, 'declined'); _finishIfEmpty(call); _presence();
        }
        break;
      case 'end':
        if (_memberRoom[role] == data['id'] || _pendingRoom[role] == data['id']) _leave(role, 'left');
        break;
      case 'signal':
        final call = _rooms[_memberRoom[role]];
        final target = data['target'];
        if (call != null && call.id == data['id'] && target is String && target != role &&
            call.members.contains(target) && _validSignal(data['data'], role, target)) {
          _send(target, {'type': 'signal', 'id': call.id, 'from': role, 'data': data['data']});
        }
        break;
      case 'video':
        final call = _rooms[_memberRoom[role]];
        if (call != null && call.id == data['id'] && call.members.contains(role) && data['enabled'] is bool) {
          if (data['enabled'] == true) {
            _camerasOn.add(role);
          } else {
            _camerasOn.remove(role);
          }
          for (final member in call.members.where((r) => r != role)) {
            _send(member, {'type': 'video', 'id': call.id, 'from': role, 'enabled': data['enabled']});
          }
        }
        break;
      case 'ptt':
        final call = _rooms[_memberRoom[role]];
        if (call != null && call.id == data['id'] && data['active'] is bool) {
          for (final member in call.members.where((r) => r != role)) {
            _send(member, {'type': 'ptt', 'id': call.id, 'from': role, 'active': data['active']});
          }
        }
        break;
      case 'chat':
        final text = normalMessage(data['text']);
        if (text == null) { _send(role, {'type': 'error', 'message': 'Messages must contain 1–2000 characters.'}); return; }
        final queue = _chatTimes.putIfAbsent(role, () => Queue<DateTime>());
        final now = DateTime.now();
        while (queue.isNotEmpty && now.difference(queue.first).inMilliseconds > 5000) { queue.removeFirst(); }
        if (queue.length >= 12) { _send(role, {'type': 'error', 'message': 'Too many messages.'}); return; }
        queue.addLast(now);
        final message = <String, dynamic>{'type': 'chat', 'from': role, 'fromName': _names[role], 'text': text,
          'time': DateTime.now().millisecondsSinceEpoch};
        final target = data['target'];
        if (target == 'circle') {
          message['target'] = 'circle';
          for (final user in _clients.keys.toList()) { _send(user, message); }
        } else if (target == 'room') {
          final call = _rooms[_memberRoom[role]];
          if (call == null || call.members.length < 2) {
            _send(role, {'type': 'error', 'message': 'Join a conversation to message the group.'}); return;
          }
          message['target'] = 'room'; message['id'] = call.id;
          for (final user in call.members) { _send(user, message); }
        } else if (target is String && target != role && _clients.containsKey(target)) {
          message['target'] = target;
          _send(target, message); _send(role, message);
        } else {
          _send(role, {'type': 'error', 'message': 'Select an online recipient.'});
        }
        break;
      default:
        _send(role, {'type': 'error', 'message': 'Unknown request.'});
    }
  }
}
