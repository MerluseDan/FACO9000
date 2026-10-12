"""Optional actual QR decoding audit when image/scanner libraries are present."""
import importlib.util
import socket
import unittest

from aiohttp import ClientSession
from aiohttp.test_utils import TestServer
from server import ControlState, create_admin_app

CAN_SCAN = all(importlib.util.find_spec(name) for name in ('pyzbar','PIL','cairosvg'))

@unittest.skipUnless(CAN_SCAN, 'QR image decoding dependencies not installed (optional QA)')
class QRScanTests(unittest.IsolatedAsyncioTestCase):
    async def test_qr_images_decode_to_exact_credentials(self):
        from pyzbar.pyzbar import decode
        from PIL import Image
        from io import BytesIO
        import cairosvg
        state=ControlState(base_url='https://test-qr-codes.trycloudflare.com')
        s=socket.socket();s.bind(('127.0.0.1',0));p=s.getsockname()[1];s.close()
        server=TestServer(create_admin_app(state,p),port=p,host='127.0.0.1')
        await server.start_server()
        async with ClientSession() as session:
            try:
                for role in ('landing','user01','user05','user10'):
                    url=str(server.make_url('/qr/'+role+'.svg'))
                    async with session.get(url,headers={'X-FACO-Admin':state.admin_token}) as response:
                        self.assertEqual(response.status,200)
                        svg=await response.read()
                        self.assertIn(b'fill="white"',svg)
                        png=cairosvg.svg2png(bytestring=svg,output_width=800,output_height=800)
                        codes=decode(Image.open(BytesIO(png)))
                        decoded=codes[0].data.decode('utf8') if codes else ''
                        expected=state.base_url+'/' if role=='landing' else next(x['url'] for x in state.snapshot()['invites'] if x['role']==role)
                        self.assertEqual(decoded,expected, 'QR scanner failed to decode '+role)
            finally:
                await server.close()

if __name__=='__main__':unittest.main()
