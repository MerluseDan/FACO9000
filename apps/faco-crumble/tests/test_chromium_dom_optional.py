"""Actual offline Chromium UI smoke. Network is mocked because sandbox blocks localhost."""
import os
import shutil
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BROWSER=shutil.which('chromium') or shutil.which('google-chrome')
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT=True
except ImportError:
    PLAYWRIGHT=False

@unittest.skipUnless(PLAYWRIGHT and BROWSER, 'Optional Playwright or Chromium is not installed')
class BrowserUI(unittest.TestCase):
    def test_mobile_name_cookie_ui_and_full_call_chat_layout(self):
        html=(ROOT/'public/index.html').read_text()
        css=(ROOT/'public/style.css').read_text()
        js=(ROOT/'public/app.js').read_text()
        html=html.replace('<link rel="stylesheet" href="/style.css" />','<style>'+css+'</style>')
        html=html.replace('<script src="/app.js" defer></script>','')
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=BROWSER,headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
            try:
                for width,height in ((390,844),(1280,880)):
                    page=browser.new_page(viewport={'width':width,'height':height})
                    errors=[]
                    page.on('pageerror',lambda e:errors.append(str(e)))
                    page.goto('about:blank#role=user01&key=AbCdEfGhIjKlMnOpQrStUvWxYz0123456789--')
                    page.set_content(html)
                    page.evaluate('''() => {
                       history.replaceState = (_, __, url) => { window.removedHash = url };
                       window.sent = [];
                       class WS {
                         static OPEN=1;static CONNECTING=0;
                         constructor(){this.handlers={};this.readyState=0;window.lastSocket=this;
                           queueMicrotask(()=>{this.readyState=1;this.emit('open',{})});}
                         addEventListener(n,fn){(this.handlers[n]??=[]).push(fn)}
                         emit(n,msg){for(const fn of this.handlers[n]||[])fn(n==='message'?{data:JSON.stringify(msg)}:{})}
                         send(raw){const msg=JSON.parse(raw);window.sent.push(msg);
                           if(msg.type==='auth')this.emit('message',{type:'ready',role:msg.role,name:msg.name,
                             iceServers:[], people:Array.from({length:10},(_,i)=>{
                               const r='user'+String(i+1).padStart(2,'0');
                               return {role:r,online:i<3,name:i===0?'X':i===1?'Sky':i===2?'Nora':null,busy:false};})});
                           if(msg.type==='dial') queueMicrotask(() => {this.emit('message',{type:'invite-sent',id:'call1',target:msg.target});
                             this.emit('message',{type:'member-joined',id:'call1',role:msg.target,name:'Sky'});});
                         }
                         close(){this.readyState=3;this.emit('close',{})}
                       }
                       window.WebSocket=WS;
                       class RTCP {constructor(){this.signalingState='stable';this.remoteDescription=null;this.localDescription=null;}
                          addTrack(){} async createOffer(){return {type:'offer',sdp:'a'}}
                          async createAnswer(){return {type:'answer',sdp:'b'}}
                          async setLocalDescription(desc){this.localDescription=desc}
                          async setRemoteDescription(desc){this.remoteDescription=desc}
                          async addIceCandidate(){} close(){} }
                       window.RTCPeerConnection=RTCP;
                       try {Object.defineProperty(navigator,'mediaDevices',{configurable:true,value:{
                         async getUserMedia(){const track={enabled:false,stop(){}};
                           return {active:true,getAudioTracks:()=>[track],getTracks:()=>[track]};}}
                       });} catch(_){}
                    }''')
                    page.add_script_tag(content=js)
                    self.assertTrue(page.locator('#entryHeading').is_visible())
                    self.assertFalse(page.locator('#appShell').is_visible())
                    self.assertFalse(page.locator('#rememberName').is_checked())
                    self.assertFalse(page.evaluate('Boolean(window.lastSocket)'))
                    page.locator('#nameInput').fill('X')
                    page.locator('#nameNext').click()
                    page.wait_for_function('Boolean(window.lastSocket) && window.sent.some(x=>x.type==="auth")')
                    self.assertEqual(page.evaluate('window.sent[0].name'),'X')
                    self.assertTrue(page.locator('#appShell').is_visible())
                    self.assertEqual(page.locator('.person-button').count(),9)
                    page.locator('.person-button[data-role="user02"]').click()
                    page.locator('#callButton').click()
                    page.wait_for_function('window.sent.some(x=>x.type==="dial")')
                    page.wait_for_function('document.querySelector("#participants").children.length===2', timeout=4000)
                    self.assertTrue(page.locator('#pttButton').is_visible())
                    self.assertTrue(page.locator('#chatRecipient').locator('option[value="room"]').count()==1)
                    self.assertTrue(page.locator('#chatRecipient').locator('option[value="circle"]').count()==1)
                    page.screenshot(path=str(ROOT/f'_qa_chromium_{width}.png'),full_page=True)
                    if width==390:
                        self.assertLessEqual(page.evaluate('document.documentElement.scrollWidth'),width+1,
                                             'Mobile horizontal overflow not allowed')
                    self.assertEqual(errors,[])
                    page.close()
            finally:
                browser.close()

if __name__=='__main__':unittest.main()
