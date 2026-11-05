"""Room-scoped video signaling and camera state regression for desktop hosts."""
import unittest
from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
from server import ControlState, create_app

class VideoSignalingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.state=ControlState(base_url='https://test.faco.example',ring_seconds=.5)
        self.server=TestServer(create_app(self.state))
        await self.server.start_server()
        self.session=ClientSession()
        self.sockets={}
    async def asyncTearDown(self):
        for ws in self.sockets.values(): await ws.close()
        await self.session.close(); await self.server.close()
    async def get(self,role):
        ws=await self.session.ws_connect(str(self.server.make_url('/socket')),origin=str(self.server.make_url('/')).rstrip('/'))
        await ws.send_json({'type':'auth','role':role,'token':self.state.tokens[role],'name':role})
        msg=await self.recv(ws,'ready')
        assert msg['role']==role
        self.sockets[role]=ws
        return ws
    async def recv(self,ws,kind):
        import asyncio
        async def wait():
            while True:
                msg=await ws.receive_json()
                if msg.get('type')==kind:return msg
        return await asyncio.wait_for(wait(),2)
    async def call(self,a,b):
        await self.sockets[a].send_json({'type':'dial','target':b})
        invitation=await self.recv(self.sockets[b],'incoming')
        await self.sockets[b].send_json({'type':'answer','id':invitation['id']})
        return await self.recv(self.sockets[b],'joined')
    async def test_video_room_membership_and_late_join(self):
        for r in ('user01','user02','user03','user04'):
            await self.get(r)
        joined=await self.call('user01','user02')
        room=joined['id']
        self.assertEqual([m.get('video') for m in joined['members']],[False,False])
        await self.sockets['user01'].send_json({'type':'video','id':room,'enabled':True})
        self.assertTrue((await self.recv(self.sockets['user02'],'video'))['enabled'])
        await self.sockets['user02'].send_json({'type':'invite','id':room,'target':'user03'})
        await self.recv(self.sockets['user03'],'incoming')
        await self.sockets['user03'].send_json({'type':'answer','id':room})
        new=await self.recv(self.sockets['user03'],'joined')
        states={m['role']:m['video'] for m in new['members']}
        self.assertEqual(states,{'user01':True,'user02':False,'user03':False})
        # Reject a forged room id and a participant who is not in the call.
        await self.sockets['user01'].send_json({'type':'video','id':'forged','enabled':False})
        await self.sockets['user04'].send_json({'type':'video','id':room,'enabled':True})
        self.assertEqual(self.state.room.cameras_on,{'user01'})
        await self.sockets['user01'].send_json({'type':'end','id':room})
        await self.recv(self.sockets['user01'],'ended')
        self.assertNotIn('user01',self.state.room.cameras_on)
        await self.sockets['user02'].send_json({'type':'video','id':room,'enabled':'true'})
        self.assertEqual(self.state.room.cameras_on,set())
        await self.sockets['user02'].send_json({'type':'video','id':room,'enabled':True})
        await self.recv(self.sockets['user03'],'video')
        self.assertEqual(self.state.room.cameras_on,{'user02'})
        await self.state.rotate('test end')
        self.assertEqual(self.state.room.cameras_on,set())
    async def test_camera_allowed_on_invited_page(self):
        async with self.session.get(str(self.server.make_url('/'))) as resp:
            self.assertEqual(resp.status,200)
            self.assertEqual(resp.headers.get('Permissions-Policy'),'microphone=(self), camera=(self), geolocation=()')
            self.assertIn('videoGallery',await resp.text())
        async with self.session.get(str(self.server.make_url('/healthz'))) as resp:
            self.assertEqual((await resp.json())['version'],'0.6.2')
if __name__=='__main__':unittest.main()
