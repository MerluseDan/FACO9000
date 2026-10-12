"""Real Chromium, network-free application UI verification for FACO's Cloudlight interface.

Incoming calls/media/signaling mocked; this tests transitions and DOM/CSS, not live Android audio.
"""
import shutil
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BROWSER = shutil.which('chromium') or shutil.which('google-chrome')
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


@unittest.skipUnless(HAS_PLAYWRIGHT and BROWSER, 'Chromium or Playwright unavailable')
class FacouxBrowser(unittest.TestCase):
    def test_faco_brand_call_infinity_options_mobile_tabs_and_privacy(self):
        html = (ROOT/'public/index.html').read_text(encoding='utf8')
        css = (ROOT/'public/style.css').read_text(encoding='utf8')
        js = (ROOT/'public/app.js').read_text(encoding='utf8')
        html = html.replace('<link rel="stylesheet" href="/style.css" />', '<style>'+css+'</style>')
        html = html.replace('<script src="/app.js" defer></script>', '')
        with sync_playwright() as pw:
            browser = pw.chromium.launch(executable_path=BROWSER, headless=True,
                                         args=['--no-sandbox', '--disable-dev-shm-usage'])
            try:
                for width,height in ((390,844),(1280,900)):
                    page = browser.new_page(viewport={'width':width,'height':height})
                    errors = []
                    page.on('pageerror',lambda err: errors.append(str(err)))
                    page.goto('about:blank#role=user01&key=AbCdEfGhIjKlMnOpQrStUvWxYz0123456789--')
                    page.set_content(html)
                    page.evaluate('''() => {
                      history.replaceState = (_,__,p) => {window.cleanedHash=p};
                      window.calls=[];
                      class WS {
                        static OPEN=1;static CONNECTING=0;
                        constructor(){this.readyState=0;this.events={};window.ws=this;
                          queueMicrotask(()=>{this.readyState=1;this.emit('open',{})})}
                        addEventListener(type,fn){(this.events[type]??=[]).push(fn)}
                        emit(type,body){for(const cb of this.events[type]||[])cb(type==='message'?{data:JSON.stringify(body)}:{})}
                        send(raw){const msg=JSON.parse(raw); window.calls.push(msg);
                          if(msg.type==='auth') this.emit('message',{type:'ready',role:msg.role,name:msg.name,iceServers:[],
                            people:Array.from({length:10},(_,i)=>{const r='user'+String(i+1).padStart(2,'0');
                              return {role:r,online:i<3,name:i===0?'X':i===1?'Sky':i===2?'Nora':null,busy:false}})});
                          if(msg.type==='dial')queueMicrotask(()=>{
                            this.emit('message',{type:'invite-sent',id:'call-1',target:msg.target});
                            this.emit('message',{type:'member-joined',id:'call-1',role:msg.target,name:'Sky'});
                          });}
                        close(){this.readyState=3;this.emit('close',{})}
                      }
                      window.WebSocket=WS;
                      class Peer {
                        constructor(){this.signalingState='stable';this.remoteDescription=null;this.localDescription=null;this.senders=[];}
                        addTrack(track){const sender={track,replaceTrack:async newTrack=>{sender.track=newTrack}};
                          this.senders.push(sender);}
                        getSenders(){return this.senders}
                        async createOffer(){return {type:'offer',sdp:'test-offer'}}
                        async createAnswer(){return {type:'answer',sdp:'test-answer'}}
                        async setLocalDescription(d){this.localDescription=d;}
                        async setRemoteDescription(d){this.remoteDescription=d;}
                        async addIceCandidate(){}
                        close(){}
                      }
                      window.RTCPeerConnection=Peer;
                      Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{
                        async getUserMedia(){const t={kind:'audio',enabled:false,stop(){this.ended=true}};
                          return {active:true,getAudioTracks:()=>[t],getTracks:()=>[t]};},
                        async enumerateDevices(){return [{kind:'audioinput',deviceId:'mic-1',label:'Mock microphone'}]}
                      }});
                    }''')
                    page.add_script_tag(content=js)
                    self.assertTrue(page.locator('#entryHeading').is_visible())
                    self.assertEqual(page.locator('.brand-mark path').count(),2)
                    self.assertFalse(page.locator('#rememberName').is_checked())
                    self.assertEqual(page.evaluate('window.cleanedHash'),page.evaluate('location.pathname'))
                    if width == 390:
                        page.screenshot(path=str(ROOT/'_qa_entry_390.png'),full_page=True)
                    page.locator('#nameInput').fill('X')
                    page.locator('#nameNext').click()
                    page.wait_for_function('window.calls.some(x=>x.type==="auth")')
                    self.assertTrue(page.locator('#appShell').is_visible())
                    self.assertEqual(page.locator('.person-button').count(),9)
                    self.assertEqual(page.evaluate('getComputedStyle(document.querySelector(".infinity-trace")).animationName'),'none')
                    page.locator('#optionsButton').click()
                    self.assertTrue(page.locator('#optionsPanel').is_visible())
                    page.locator('#doctorButton').click()
                    self.assertIn('WebRTC: Available',page.locator('#doctorResult').inner_text())
                    if width == 390:
                        page.screenshot(path=str(ROOT/'_qa_options_390.png'),full_page=True)
                    page.locator('#motionToggle').uncheck()
                    page.locator('#focusToggle').check()
                    page.locator('#saveOptionsButton').click()
                    self.assertTrue(page.evaluate('document.body.classList.contains("faco-no-motion")'))
                    self.assertTrue(page.evaluate('document.body.classList.contains("faco-focus")'))
                    self.assertFalse(page.locator('#optionsPanel').is_visible())
                    page.locator('#optionsButton').click()
                    page.locator('#resetOptionsButton').click()
                    page.locator('#saveOptionsButton').click()
                    self.assertFalse(page.evaluate('document.body.classList.contains("faco-no-motion")'))
                    self.assertFalse(page.evaluate('document.body.classList.contains("faco-focus")'))
                    page.locator('.person-button[data-role="user02"]').click()
                    page.locator('#callButton').click()
                    page.wait_for_function('document.querySelector("#participants").children.length===2')
                    self.assertEqual(page.evaluate('getComputedStyle(document.querySelector(".infinity-trace")).animationName'),'infinityFlow')
                    self.assertTrue(page.locator('#pttButton').is_visible())
                    if width == 390:
                        page.screenshot(path=str(ROOT/'_qa_call_390.png'),full_page=True)
                        page.locator('#viewChatButton').click()
                        self.assertTrue(page.locator('#chatPanel').is_visible())
                        self.assertTrue(page.locator('#callDock').is_visible())
                        page.locator('#callDock').click()
                        self.assertTrue(page.locator('#callButton').is_visible())
                    else:
                        page.screenshot(path=str(ROOT/'_qa_call_1280.png'),full_page=True)
                    page.locator('#endButton').click()
                    self.assertEqual(page.evaluate('getComputedStyle(document.querySelector(".infinity-trace")).animationName'),'none')
                    page.locator('#leaveButton').click()
                    self.assertTrue(page.locator('#entryHeading').is_visible())
                    self.assertFalse(page.evaluate('document.body.classList.contains("faco-no-motion")'))
                    self.assertEqual(errors, [])
                    self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width+1)
                    page.close()
            finally:
                browser.close()
