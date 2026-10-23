"""Headless Chromium integration test of the QR guest UI and video controls.
Run: python qa/test_video_browser.py (requires playwright + chromium).
No real camera/network/account is used; Browser WebRTC sender and signaling are mocked,
while video capture uses real Chromium canvas MediaStreamTrack lifecycle.
"""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / 'public/index.html'
CSS = ROOT / 'public/style.css'
JS = ROOT / 'public/app.js'

MOCK = r'''
(() => {
  const key = 'a'.repeat(44);
  history.replaceState(null, '', '#role=user01&key=' + key);
  const nativeReplace = history.replaceState.bind(history);
  history.replaceState = (state,title,url) => String(url).startsWith('#') ? nativeReplace(state,title,url) : undefined;
  window.__messages = [];
  window.__streams = [];
  window.__pcs = [];
  window.__denied = false;
  window.__videoRequests = [];
  let ws = null;
  class TestSocket extends EventTarget {
    static OPEN = 1;
    static CONNECTING = 0;
    constructor(url) {
      super(); this.url = url; this.readyState = 0; ws = this;
      setTimeout(() => { this.readyState = 1; this.dispatchEvent(new Event('open')); }, 10);
    }
    push(data) { this.dispatchEvent(new MessageEvent('message', {data:JSON.stringify(data)})); }
    send(payload) {
      const msg = JSON.parse(payload);
      window.__messages.push(msg);
      if (msg.type === 'auth') setTimeout(() => this.push({type:'ready',role:'user01',name:msg.name,iceServers:[],people:[
        {role:'user01',name:msg.name,online:true,busy:false},
        {role:'user02',name:'Other',online:true,busy:false},
        {role:'user03',name:'Third',online:true,busy:false},
      ]}), 10);
      if (msg.type === 'dial') setTimeout(() => {
        this.push({type:'invite-sent',id:'room-test',target:msg.target});
        this.push({type:'joined',id:'room-test',members:[
          {role:'user01',name:'Dan',video:false},{role:'user02',name:'Other',video:false}]});
      },10);
      if (msg.type === 'end') setTimeout(() => this.push({type:'ended',id:msg.id}),10);
    }
    close() { this.readyState = 3; this.dispatchEvent(new Event('close')); }
  }
  window.WebSocket = TestSocket;
  window.__server = (data) => ws.push(data);
  class TestPeerConnection {
    constructor() {this.signalingState='stable';this.connectionState='connected';this.senders=[];window.__pcs.push(this);}
    addTransceiver(kind,config) {
      const sender = {kind,track:null,history:[],async replaceTrack(track) {this.track = track;this.history.push(track?.id ?? null)}};
      this.senders.push(sender); this.videoSender = sender;
      return {sender};
    }
    addTrack(track,stream) {const sender={track,kind:track.kind,async replaceTrack(t){this.track=t;}};this.senders.push(sender);return sender;}
    getSenders(){return this.senders;}
    async createOffer(){return {type:'offer',sdp:'v=0\nm=audio\nm=video'};}
    async createAnswer(){return {type:'answer',sdp:'v=0\nm=video'};}
    async setLocalDescription(desc){this.localDescription=desc;this.signalingState='have-local-offer';}
    async setRemoteDescription(desc){this.remoteDescription=desc;}
    async addIceCandidate(){}
    close(){this.connectionState='closed';}
  }
  window.RTCPeerConnection=TestPeerConnection;
  const media = {
    async getUserMedia(config) {
      if (config.video) {
        window.__videoRequests.push(config.video);
        if (window.__denied) { const e=new Error('Permission denied');e.name='NotAllowedError';throw e; }
        const canvas = document.createElement('canvas');canvas.width=640;canvas.height=360;
        const cx = canvas.getContext('2d');cx.fillStyle='#16abdd';cx.fillRect(0,0,640,360);
        const s = canvas.captureStream(12);window.__streams.push(s);return s;
      }
      if (config.audio) {
        const ctx=new AudioContext();const dest=ctx.createMediaStreamDestination();
        window.__streams.push(dest.stream);return dest.stream;
      }
      throw new Error('Invalid constraints');
    },
    async enumerateDevices(){return []},
  };
  Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:media});
})();
'''

def run():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,has_touch=True)
        # Page navigation is disallowed in this test environment. Self-contained DOM + identical static scripts.
        html=HTML.read_text().replace('<link rel="stylesheet" href="/style.css" />','').replace('<script src="/app.js" defer></script>','')
        page.set_content(html,wait_until='domcontentloaded')
        page.add_style_tag(content=CSS.read_text())
        page.evaluate(MOCK)
        page.add_script_tag(content=JS.read_text())
        assert page.locator('#entryScreen').is_visible()
        assert page.locator('#cameraButton').is_hidden()
        page.locator('#nameInput').fill('Dan')
        page.locator('#nameNext').click()
        page.wait_for_function("document.querySelector('#socketText').textContent === 'Connected privately'")
        page.locator('#callButton').click()
        page.wait_for_function("document.querySelector('#callStatus').textContent.includes('Connected with')")
        assert page.locator('#videoGallery').is_visible()
        assert page.locator('#videoControls').is_visible()
        assert page.locator('.video-tile').count()==2
        assert page.locator('.video-tile.has-video').count()==0
        assert page.locator('#cameraButton').get_attribute('aria-pressed')=='false'
        assert page.locator('#flipCameraButton').is_disabled()
        assert page.evaluate('window.__videoRequests.length')==0
        assert page.evaluate('window.__pcs.length')==1
        assert page.evaluate('window.__pcs[0].senders.some(s=>s.kind === "video")')
        page.locator('#cameraButton').click()
        page.wait_for_function("document.querySelector('#cameraButton').getAttribute('aria-pressed') === 'true'")
        assert page.locator('#flipCameraButton').is_enabled()
        assert page.locator('.video-tile.self-preview.has-video video').count()==1
        assert page.evaluate('window.__pcs[0].videoSender.track?.kind')=='video'
        assert page.evaluate('window.__messages.filter(m=>m.type==="video").at(-1)?.enabled') is True
        track_one=page.evaluate('window.__pcs[0].videoSender.track.id')
        page.locator('#flipCameraButton').click()
        page.wait_for_function("document.querySelector('#cameraHint').textContent.includes('Rear')")
        assert page.evaluate('window.__pcs[0].videoSender.track.id')!=track_one
        assert page.evaluate('window.__streams.filter(s=>s.getVideoTracks().length).at(-2).getVideoTracks()[0].readyState')=='ended'
        page.evaluate("window.__server({type:'member-joined',id:'room-test',role:'user03',name:'Third',video:false})")
        page.wait_for_function("document.querySelectorAll('.video-tile').length === 3")
        assert page.evaluate('window.__pcs.length')==2
        page.wait_for_function("window.__pcs[1].videoSender.track?.kind==='video'")
        page.evaluate("window.__server({type:'video',id:'room-test',from:'user02',enabled:true})")
        page.wait_for_function("document.querySelector('.video-tile[data-role=user02]').classList.contains('has-video')")
        for width in (320,390,700,1280):
            page.set_viewport_size({'width':width,'height':900})
            page.wait_for_timeout(60)
            sizes=page.evaluate('({doc:document.documentElement.scrollWidth,viewport:document.documentElement.clientWidth})')
            assert sizes['doc'] <= sizes['viewport']+1,(width,sizes)
        page.set_viewport_size({'width':390,'height':844})
        if os.getenv('FACO_SCREENSHOT_DIR'):
            out = Path(os.environ['FACO_SCREENSHOT_DIR']);out.mkdir(parents=True,exist_ok=True)
            page.screenshot(path=str(out/'FACO_Crumble_v0.6.1_VIDEO_Mobile_QA.png'),full_page=True)
            page.set_viewport_size({'width':1280,'height':900})
            page.screenshot(path=str(out/'FACO_Crumble_v0.6.1_VIDEO_Desktop_QA.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
        page.locator('#cameraButton').click()
        page.wait_for_function("document.querySelector('#cameraButton').getAttribute('aria-pressed') === 'false'")
        assert page.evaluate('window.__pcs.every(pc => pc.videoSender.track === null)')
        assert page.evaluate('window.__messages.filter(m=>m.type==="video").at(-1)?.enabled') is False
        assert page.evaluate('document.querySelector(".video-tile.self-preview video").srcObject === null')
        assert page.evaluate('window.__streams.filter(s=>s.getVideoTracks().length).at(-1).getVideoTracks()[0].readyState')=='ended'
        page.evaluate('window.__denied = true')
        page.locator('#cameraButton').click()
        page.wait_for_function("document.querySelector('#errorMessage').textContent.includes('Camera unavailable')")
        assert page.locator('#callStatus').inner_text().startswith('Connected with')
        assert page.evaluate('window.__messages.filter(m=>m.type==="video").at(-1)?.enabled') is False
        page.locator('#leaveButton').click()
        assert page.locator('#entryScreen').is_visible()
        assert page.locator('.video-tile').count()==0
        assert page.evaluate('window.__streams.filter(s=>s.getVideoTracks().length).every(s=>s.getVideoTracks()[0].readyState==="ended")')
        # Screenshot mobile in a live call with synthetic camera feed / no faces
        page.reload() if False else None
        browser.close()
        print('PASSED: browser QR entry, audio-first call, opt-in video, flip, group, state, privacy teardown, denied camera.')

if __name__=='__main__':run()
