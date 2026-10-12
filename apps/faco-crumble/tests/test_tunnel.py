import asyncio
import tempfile
import unittest
from pathlib import Path
from launcher import run_quick_tunnel
from server import ControlState

class CloudflareRecoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_connection_recovery_and_process_restart_expire_invites(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary=Path(tmp)/'fake-cloudflared'
            binary.write_text('''#!/usr/bin/env python3
import time
print('Tunnel link: https://test-faco-qr.trycloudflare.com', flush=True)
print('Registered tunnel connection',flush=True)
time.sleep(0.12)
print('Unregistered tunnel connection',flush=True)
time.sleep(0.10)
print('Registered tunnel connection',flush=True)
time.sleep(0.22)
''')
            binary.chmod(0o700)
            state=ControlState(2)
            before=state.tokens['user01']
            task=asyncio.create_task(run_quick_tunnel(state,str(binary),30010))
            try:
                for _ in range(100):
                    if state.epoch >= 2: break
                    await asyncio.sleep(.025)
                self.assertEqual(state.epoch,2,'Reconnect must rotate once after connection lost')
                self.assertEqual(state.base_url,'https://test-faco-qr.trycloudflare.com')
                self.assertNotEqual(before,state.tokens['user01'])
                next_token=state.tokens['user01']
                for _ in range(100):
                    if state.epoch >= 3: break
                    await asyncio.sleep(.025)
                self.assertGreaterEqual(state.epoch,3,'Process restart must expire all invites')
                self.assertNotEqual(next_token,state.tokens['user01'])
            finally:
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await task

if __name__=='__main__': unittest.main()
