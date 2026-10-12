"""Start the actual bash launcher twice, exercise local admin API, and prove token expiry.
Runs without Cloudflare or browser and without downloading dependencies when aiohttp/qrcode are present.
"""
import contextlib
import json
import os
import re
import select
import signal
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def reserve_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]


def request(url, token=None, data=None):
    headers={'X-FACO-Admin':token} if token else {}
    if data is not None: headers['Content-Type']='application/json'
    req=urllib.request.Request(url,headers=headers,data=json.dumps(data).encode() if data is not None else None,
                               method='POST' if data is not None else 'GET')
    with urllib.request.urlopen(req,timeout=3) as resp:
        return json.load(resp)


def spawn(env, public_port, admin_port):
    args=['./run.sh','--local','--no-open']
    child=subprocess.Popen(args,cwd=ROOT,env={**env,'FACO_PORT':str(public_port),'FACO_ADMIN_PORT':str(admin_port)},
                           stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,start_new_session=True)
    output=b''
    try:
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            if child.poll() is not None:
                raise AssertionError('Launcher exited early: '+repr(output.decode(errors='replace')))
            readable,_,_=select.select([child.stdout],[],[],.3)
            if readable:
                block=os.read(child.stdout.fileno(),8192)
                if block: output+=block
            match=re.search(rb'http://127\.0\.0\.1:\d+/#admin=([A-Za-z0-9_-]+)',output)
            if match:
                base=f'http://127.0.0.1:{public_port}/healthz'
                try:
                    if request(base)['ok']: return child,match.group(1).decode()
                except (OSError,ValueError):
                    pass
        raise AssertionError('Launcher did not expose health+admin token: '+repr(output.decode(errors='replace')))
    except Exception:
        child.terminate()
        child.wait(timeout=3)
        raise


def stop(child):
    if child.poll() is None:
        child.terminate()
        try: child.wait(timeout=4)
        except subprocess.TimeoutExpired:
            child.kill();child.wait(timeout=4)
    child.stdout.close()


class ProcessStartTests(unittest.TestCase):
    def test_actual_launcher_and_participant_config_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            public_port,admin_port=reserve_port(),reserve_port()
            env={**os.environ,'XDG_CONFIG_HOME':tmp,'FACO_NO_GUI':'1'}
            one, token1=spawn(env,public_port,admin_port)
            try:
                base=f'http://127.0.0.1:{admin_port}/api'
                initial=request(base+'/state',token1)
                self.assertEqual(initial['guestCount'],10)
                invite1=initial['invites'][0]['url']
                changed=request(base+'/guest-count',token1,{'count':4})
                self.assertEqual(changed['guestCount'],4)
                self.assertEqual(changed['epoch'],2)
                self.assertNotEqual(invite1,changed['invites'][0]['url'])
                invite1=changed['invites'][0]['url']
            finally:
                stop(one)
            two,token2=spawn(env,public_port,admin_port)
            try:
                self.assertNotEqual(token1,token2,'Admin key must regenerate on every app start')
                after=request(base+'/state',token2)
                self.assertEqual(after['guestCount'],4,'Guest configuration must persist')
                self.assertEqual(len(after['invites']),4,'Four equal participants')
                self.assertNotEqual(after['invites'][0]['url'],invite1,'Invite must change on every restart')
                saved=json.loads((Path(tmp)/'faco-crumble'/'settings.json').read_text())
                self.assertEqual(saved,{'guestCount':4})
                self.assertNotIn('key',str(saved).lower())
            finally:
                stop(two)

    def test_legacy_private_talk_capacity_migrates_without_reusing_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            legacy=Path(tmp)/'faco-private-talk'/'settings.json'
            legacy.parent.mkdir(parents=True)
            legacy.write_text(json.dumps({'guestCount':6}),encoding='utf8')
            public_port,admin_port=reserve_port(),reserve_port()
            env={**os.environ,'XDG_CONFIG_HOME':tmp,'FACO_NO_GUI':'1'}
            child,admin_token=spawn(env,public_port,admin_port)
            try:
                base=f'http://127.0.0.1:{admin_port}/api'
                state=request(base+'/state',admin_token)
                self.assertEqual(state['guestCount'],6)
                self.assertEqual(len(state['invites']),6)
                request(base+'/guest-count',admin_token,{'count':5})
                new=Path(tmp)/'faco-crumble'/'settings.json'
                self.assertEqual(json.loads(new.read_text()),{'guestCount':5})
                self.assertEqual(json.loads(legacy.read_text()),{'guestCount':6},'Do not mutate legacy install')
                self.assertNotIn('token',new.read_text().lower(),'Tokens must never persist')
            finally:
                stop(child)

if __name__=='__main__':unittest.main()
