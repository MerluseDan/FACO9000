"""End-to-end aiohttp websocket test suite: 10 people, rooms, messages and isolation."""
import asyncio
import json
from collections import deque
import socket
import unittest

from aiohttp import ClientSession, WSServerHandshakeError
from aiohttp.test_utils import TestServer
from server import (ControlState, create_app, create_admin_app, make_invite,
                    normalize_name, normalize_message, new_tokens, valid_base_url, valid_signal)


def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


class SignalingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state = ControlState(base_url='https://faco.example', ring_seconds=.25)
        self.public = TestServer(create_app(self.state))
        await self.public.start_server()
        self.admin_port = port()
        self.admin = TestServer(create_admin_app(self.state,self.admin_port),port=self.admin_port,host='127.0.0.1')
        await self.admin.start_server()
        self.session = ClientSession()
        self.base = str(self.public.make_url('/')).rstrip('/')
        self.clients = {}
        self.extra = []

    async def asyncTearDown(self):
        for ws in list(self.clients.values()) + self.extra:
            await ws.close()
        await self.session.close()
        await self.admin.close()
        await self.public.close()

    async def join(self, role, *, name=None, token=None):
        ws = await self.session.ws_connect(self.base + '/socket',origin=self.base)
        self.extra.append(ws)
        await ws.send_json({'type':'auth','role':role,'token':token if token is not None else self.state.tokens[role],
                            'name':name if name is not None else role})
        return ws

    async def connected(self, role, *, name=None):
        ws = await self.join(role,name=name)
        msg = await self.recv(ws,'ready')
        self.assertEqual(msg['role'],role)
        self.clients[role] = ws
        return ws

    async def recv(self, ws, kind, timeout=1.5):
        async def loop():
            while True:
                data = await ws.receive_json()
                if data.get('type') == kind:
                    return data
        return await asyncio.wait_for(loop(),timeout=timeout)

    async def call(self, caller, recipient):
        await self.clients[caller].send_json({'type':'dial','target':recipient})
        invite = await self.recv(self.clients[recipient],'incoming')
        self.assertEqual(invite['from'],caller)
        await self.clients[recipient].send_json({'type':'answer','id':invite['id']})
        joined = await self.recv(self.clients[recipient],'joined')
        self.assertEqual(joined['id'], invite['id'])
        arrival = await self.recv(self.clients[caller],'member-joined')
        self.assertEqual(arrival['role'],recipient)
        return invite['id']

    async def test_ten_equal_participants_and_cross_call(self):
        self.assertEqual(list(self.state.tokens),[f'user{i:02d}' for i in range(1,11)])
        self.assertNotIn('owner',self.state.tokens)
        for i in range(1,11):
            await self.connected(f'user{i:02d}',name=f'P{i}')
        call = await self.call('user09','user02')
        self.assertEqual(self.state.room.member_call['user09'],call)
        self.assertEqual(self.state.room.member_call['user02'],call)
        self.assertTrue(all(item['online'] for item in self.state.room.roster()))
        self.assertIn('user07',self.state.tokens)

    async def test_ten_person_conference_membership_and_group_broadcast(self):
        for i in range(1, 11):
            await self.connected(f'user{i:02d}')
        cid = await self.call('user01','user02')
        for i in range(3, 11):
            role=f'user{i:02d}'
            await self.clients['user01'].send_json({'type':'invite','id':cid,'target':role})
            invitation=await self.recv(self.clients[role],'incoming')
            self.assertEqual(invitation['id'],cid)
            await self.clients[role].send_json({'type':'answer','id':cid})
            joined=await self.recv(self.clients[role],'joined')
            self.assertEqual(len(joined['members']),i)
        self.assertEqual(len(self.state.room.calls[cid].members),10)
        await self.clients['user10'].send_json({'type':'chat','target':'room','text':'Full house'})
        for i in range(1,11):
            role=f'user{i:02d}'
            received=await self.recv(self.clients[role],'chat')
            self.assertEqual(received['text'],'Full house')

    async def test_call_two_other_users_while_other_room_exists(self):
        for r in ('user01','user02','user03','user04'):
            await self.connected(r)
        one = await self.call('user01','user02')
        two = await self.call('user03','user04')
        self.assertNotEqual(one,two)
        self.assertEqual(len(self.state.room.calls),2)
        await self.clients['user01'].send_json({'type':'end','id':one})
        self.assertEqual((await self.recv(self.clients['user01'],'ended'))['id'],one)
        self.assertEqual(len(self.state.room.calls),1)
        self.assertIn(two,self.state.room.calls)

    async def test_add_members_to_existing_room_group_chat(self):
        for r in ('user01','user02','user03','user04'):
            await self.connected(r)
        call = await self.call('user01','user02')
        await self.clients['user02'].send_json({'type':'invite','id':call,'target':'user03'})
        new = await self.recv(self.clients['user03'],'incoming')
        self.assertEqual(new['id'],call)
        self.assertEqual(new['from'],'user02')
        self.assertEqual(len(new['members']),2)
        await self.clients['user03'].send_json({'type':'answer','id':call})
        ready = await self.recv(self.clients['user03'],'joined')
        self.assertEqual({x['role'] for x in ready['members']},{'user01','user02','user03'})
        await self.recv(self.clients['user01'],'member-joined')
        await self.recv(self.clients['user02'],'member-joined')
        await self.clients['user03'].send_json({'type':'chat','target':'room','text':'Everyone hear me?'})
        for role in ('user01','user02','user03'):
            m = await self.recv(self.clients[role],'chat')
            self.assertEqual(m['text'],'Everyone hear me?')
            self.assertEqual(m['target'],'room')
        self.assertEqual(len(self.state.room.calls[call].members),3)
        await self.clients['user03'].send_json({'type':'end','id':call})
        left = await self.recv(self.clients['user01'],'member-left')
        self.assertEqual(left['role'],'user03')
        self.assertEqual(self.state.room.calls[call].members,{'user01','user02'})
        await self.clients['user01'].send_json({'type':'invite','id':call,'target':'user04'})
        self.assertEqual((await self.recv(self.clients['user04'],'incoming'))['id'],call)

    async def test_targeted_direct_messages_and_input_limits(self):
        a=await self.connected('user01',name='X')
        b=await self.connected('user02',name='<svg onload=evil()>')
        c=await self.connected('user03')
        await a.send_json({'type':'chat','target':'user02','text':'  Hello from X  '})
        echo=await self.recv(a,'chat')
        rx=await self.recv(b,'chat')
        self.assertEqual(rx['text'],'Hello from X')
        self.assertEqual(rx['fromName'],'X')
        self.assertEqual(echo['text'],rx['text'])
        with self.assertRaises(asyncio.TimeoutError):
            await self.recv(c,'chat', timeout=.06)
        await a.send_json({'type':'chat','target':'user02','text':' '})
        self.assertIn('2000',(await self.recv(a,'error'))['message'])
        await a.send_json({'type':'chat','target':'user01','text':'self'})
        self.assertIn('online recipient',(await self.recv(a,'error'))['message'])
        self.assertIsNone(normalize_message('x'*2001))
        self.assertIsNone(normalize_message('\0'))

    async def test_circle_broadcast_without_call_and_ephemeral_delivery(self):
        for role in ('user01','user02','user03'):
            await self.connected(role)
        await self.clients['user02'].send_json({'type':'chat','target':'circle','text':'Hi all'})
        for role in ('user01','user02','user03'):
            message=await self.recv(self.clients[role],'chat')
            self.assertEqual(message['text'],'Hi all')
            self.assertEqual(message['target'],'circle')
            self.assertEqual(message['from'],'user02')
        await self.clients['user03'].close()
        await asyncio.sleep(.02)
        returned=await self.connected('user03')
        self.assertEqual((await self.recv(returned,'members'))['type'],'members')
        self.assertEqual(self.state.room.chat_limits['user03'],deque()) if 'user03' in self.state.room.chat_limits else None
        self.assertNotIn('Hi all',json.dumps(self.state.snapshot()))

    async def test_inviter_departure_cancels_unaccepted_invite(self):
        for role in ('user01','user02','user03'):
            await self.connected(role)
        cid=await self.call('user01','user02')
        await self.clients['user02'].send_json({'type':'invite','id':cid,'target':'user03'})
        await self.recv(self.clients['user03'],'incoming')
        await self.clients['user02'].send_json({'type':'end','id':cid})
        cancel=await self.recv(self.clients['user03'],'invite-cancelled')
        self.assertEqual(cancel['reason'],'inviter-left')
        self.assertNotIn('user03',self.state.room.pending_call)
        await self.clients['user03'].send_json({'type':'answer','id':cid})
        await asyncio.sleep(.02)
        self.assertNotIn('user03',self.state.room.member_call)

    async def test_security_reject_cross_room_audio_and_stranger_control(self):
        for role in ('user01','user02','user03','user04'):
            await self.connected(role)
        cid=await self.call('user01','user02')
        self.assertFalse(valid_signal({'type':'offer','sdp':'x'},'user02','user01'))
        self.assertTrue(valid_signal({'type':'offer','sdp':'x'},'user01','user02'))
        self.assertFalse(valid_signal({'type':'answer','sdp':'x'},'user01','user02'))
        self.assertTrue(valid_signal({'type':'answer','sdp':'x'},'user02','user01'))
        await self.clients['user03'].send_json({'type':'signal','id':cid,'target':'user02',
                                                'data':{'type':'offer','sdp':'BAD'}})
        await self.clients['user03'].send_json({'type':'end','id':cid})
        await self.clients['user03'].send_json({'type':'invite','id':cid,'target':'user04'})
        await asyncio.sleep(.05)
        self.assertEqual(self.state.room.calls[cid].members,{'user01','user02'})
        await self.clients['user01'].send_json({'type':'signal','id':cid,'target':'user02',
                                                'data':{'type':'offer','sdp':'legit'}})
        rx=await self.recv(self.clients['user02'],'signal')
        self.assertEqual(rx['from'],'user01')
        await self.clients['user02'].send_json({'type':'signal','id':cid,'target':'user01',
                                                'data':{'type':'answer','sdp':'fine'}})
        self.assertEqual((await self.recv(self.clients['user01'],'signal'))['data']['sdp'],'fine')

    async def test_busy_while_ringing_and_auto_expiry(self):
        for r in ('user01','user02','user03'):
            await self.connected(r)
        await self.clients['user01'].send_json({'type':'dial','target':'user02'})
        invite=await self.recv(self.clients['user02'],'incoming')
        await self.clients['user03'].send_json({'type':'dial','target':'user02'})
        self.assertIn('busy',(await self.recv(self.clients['user03'],'error'))['message'].lower())
        await self.recv(self.clients['user02'],'invite-cancelled',timeout=2)
        self.assertEqual(self.state.room.calls,{})
        self.assertEqual(self.state.room.member_call,{})
        self.assertEqual(self.state.room.pending_call,{})
        self.assertNotIn(invite['id'],self.state.room.calls)

    async def test_disconnect_and_group_remains(self):
        for role in ('user01','user02','user03'):
            await self.connected(role)
        call=await self.call('user01','user02')
        await self.clients['user01'].send_json({'type':'invite','id':call,'target':'user03'})
        await self.recv(self.clients['user03'],'incoming')
        await self.clients['user03'].send_json({'type':'answer','id':call})
        await self.recv(self.clients['user03'],'joined')
        await self.clients['user02'].close()
        await self.recv(self.clients['user01'],'member-left')
        self.assertNotIn('user02',self.state.room.names)
        self.assertEqual(self.state.room.calls[call].members,{'user01','user03'})
        await self.clients['user03'].close()
        await self.recv(self.clients['user01'],'ended')
        self.assertEqual(self.state.room.calls,{})
        self.assertNotIn('user03',self.state.room.names)

    async def test_duplicate_invalid_keys_names_and_rotation(self):
        a = await self.connected('user01',name='Z')
        duplicate = await self.join('user01')
        self.assertIn('already',(await self.recv(duplicate,'auth-error'))['message'])
        invalid = await self.join('user02',token='A'*43)
        self.assertEqual((await self.recv(invalid,'auth-error'))['type'],'auth-error')
        for name in ('','  ','\n','x'*41,'a\0b','a\u202eb'):
            self.assertIsNone(normalize_name(name))
        old=self.state.tokens['user01']
        await self.state.rotate('regenerate')
        self.assertNotEqual(self.state.tokens['user01'],old)
        self.assertEqual((await self.recv(a,'session-expired'))['type'],'session-expired')
        former=await self.join('user01',token=old)
        self.assertEqual((await self.recv(former,'auth-error'))['type'],'auth-error')
        self.assertEqual(self.state.room.names,{})

    async def test_tunnel_renewal_and_no_server_stored_messages(self):
        before = self.state.tokens['user02']
        await self.state.set_tunnel('https://faco.example')
        self.assertEqual(self.state.tokens['user02'],before)
        await self.state.set_tunnel('https://else.trycloudflare.com')
        self.assertNotEqual(self.state.tokens['user02'],before)
        current=self.state.tokens['user02']
        await self.state.set_tunnel('https://else.trycloudflare.com',restarted=True)
        self.assertNotEqual(current,self.state.tokens['user02'])
        self.assertNotIn('messages',repr(self.state.room.__dict__))
        self.assertEqual(len(self.state.snapshot()['invites']),10)
        self.assertNotIn('owner',json.dumps(self.state.snapshot()))

    async def test_admin_access_separate_and_no_cookies_set(self):
        private={'X-FACO-Admin':self.state.admin_token}
        async with self.session.get(self.public.make_url('/api/state')) as r:
            self.assertEqual(r.status,404)
        async with self.session.get(self.admin.make_url('/api/state')) as r:
            self.assertEqual(r.status,403)
        async with self.session.get(self.admin.make_url('/api/state'),headers={'Host':'bad.test',**private}) as r:
            self.assertEqual(r.status,403)
        async with self.session.get(self.admin.make_url('/api/state'),headers=private) as r:
            self.assertEqual(r.status,200)
            self.assertEqual((await r.json())['guestCount'],10)
        async with self.session.get(self.public.make_url('/')) as r:
            self.assertEqual(r.status,200)
            self.assertNotIn('Set-Cookie',r.headers)
            self.assertIn('no-store',r.headers['Cache-Control'])
            self.assertIn('noindex',r.headers['X-Robots-Tag'])
            html=await r.text()
            self.assertNotIn(self.state.tokens['user01'],html)
            self.assertIn('rememberName',html)
        with self.assertRaises(WSServerHandshakeError):
            await self.session.ws_connect(self.base+'/socket',origin='https://evil.example')
        self.assertTrue(valid_base_url('http://localhost:8787'))
        self.assertFalse(valid_base_url('http://public.test'))

if __name__=='__main__':
    unittest.main()
