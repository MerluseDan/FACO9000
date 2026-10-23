"""Smoke-test a packaged native launcher on its actual OS runner."""
import argparse,json,os,signal,socket,subprocess,sys,time,urllib.request

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));return s.getsockname()[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('program');a=p.parse_args()
    pub,adm=free_port(),free_port()
    env={**os.environ,'FACO_NO_GUI':'1','FACO_PORT':str(pub),'FACO_ADMIN_PORT':str(adm)}
    proc=subprocess.Popen([a.program,'--local','--no-open'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    try:
        deadline=time.monotonic()+35
        while time.monotonic()<deadline:
            if proc.poll() is not None: raise RuntimeError(f'Native process exited: {proc.returncode}')
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{pub}/healthz',timeout=.4) as r:
                    info=json.load(r)
                    assert info['version']=='0.6.2',info
                with urllib.request.urlopen(f'http://127.0.0.1:{pub}/',timeout=.4) as r:
                    assert 'camera=(self)' in r.headers.get('Permissions-Policy','')
                    assert b'videoGallery' in r.read()
                with urllib.request.urlopen(f'http://127.0.0.1:{adm}/',timeout=.4) as r:
                    assert b'FACO' in r.read()
                print('PASS native packaged Desktop server, audio/video client, admin isolation and version')
                return
            except (OSError,TimeoutError): time.sleep(.25)
        raise RuntimeError('Native desktop process not reachable')
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill();proc.wait(timeout=5)
        if proc.stdout: proc.stdout.close()
if __name__=='__main__':main()
