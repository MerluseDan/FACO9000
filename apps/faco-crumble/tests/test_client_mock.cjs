'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const src=fs.readFileSync(path.join(__dirname,'../public/app.js'),'utf8');
class Elem {
 constructor(tag='div'){
  this.tag=tag;this.textContent='';this.value='';this.dataset={};this.children=[];this.disabled=false;this.checked=false;
  this.listeners=new Map();this.set=new Set(['hidden']);this.attrs={};this.srcObject=null;
  this.classList={add:v=>this.set.add(v),remove:v=>this.set.delete(v),contains:v=>this.set.has(v),
    toggle:(v,force)=>{if(force===true||(force===undefined&&!this.set.has(v)))this.set.add(v);else this.set.delete(v)}};
 }
 get options(){return this.children}
 addEventListener(n,fn){let v=this.listeners.get(n)||[];v.push(fn);this.listeners.set(n,v)}
 emit(n,values={}){for(const fn of this.listeners.get(n)||[])fn(values)}
 click(){this.emit('click',{target:this})}
 append(...x){this.children.push(...x)}
 replaceChildren(...x){this.children=x}
 remove(){this.removed=true}
 setAttribute(k,v){this.attrs[k]=v}
 setPointerCapture(){}
 blur(){}
 play(){return Promise.resolve()}
}
const wait=ms=>new Promise(r=>setTimeout(r,ms));
function harness(role='user01',cookies=''){
 const els=new Map(),get=id=>{if(!els.has(id))els.set(id,new Elem());return els.get(id)};
 const outs=[],tracks=[],storage=new Map([['faco-invite','old-QR'],['faco-talk-mode','ptt']]),storageWrites=[];
 const cookieJar=new Map(); if(cookies) cookieJar.set('faco_crumble_name',encodeURIComponent(cookies));
 let sockets=0,sock=null;
 class WS {
  static OPEN=1;static CONNECTING=0;
  constructor(){this.readyState=0;this.handlers=new Map();sockets++;sock=this;
   queueMicrotask(()=>{this.readyState=1;this.emit('open')});}
  addEventListener(n,fn){const a=this.handlers.get(n)||[];a.push(fn);this.handlers.set(n,a)}
  emit(n,data){for(const fn of this.handlers.get(n)||[])fn(n==='message'?{data:JSON.stringify(data)}:{})}
  send(value){outs.push(JSON.parse(value))}
  close(){this.readyState=3;this.emit('close')}
 }
 class RTC {
  constructor(){this.localDescription=null;this.remoteDescription=null;this.connectionState='new';this.signalingState='stable';this.tracks=[]}
  addTrack(x){this.tracks.push(x)}
  createOffer(){return Promise.resolve({type:'offer',sdp:'offer-from-test'})}
  createAnswer(){return Promise.resolve({type:'answer',sdp:'answer-from-test'})}
  async setLocalDescription(d){this.localDescription=d;this.signalingState=d.type==='offer'?'have-local-offer':'stable'}
  async setRemoteDescription(d){this.remoteDescription=d;this.signalingState='stable';this.connectionState='connected';this.onconnectionstatechange?.()}
  async addIceCandidate(){}
  close(){this.connectionState='closed'}
 }
 const listeners=new Map();
 const document={getElementById:get,createElement:tag=>new Elem(tag),
  querySelector:expr=>expr==='.call-panel'?get('callPanel'):null,
  addEventListener(n,fn){let a=listeners.get(n)||[];a.push(fn);listeners.set(n,a)},hidden:false,title:'',
  get cookie(){return Array.from(cookieJar.entries()).map(([a,b])=>a+'='+b).join('; ')},
  set cookie(text){const [pair,...attributes]=text.split(';');const ix=pair.indexOf('=');const k=pair.slice(0,ix),v=pair.slice(ix+1);
   if(attributes.some(x=>x.trim()==='Max-Age=0'))cookieJar.delete(k);else cookieJar.set(k,v)}
 };
 const winListeners=new Map();
 const window={sessionStorage:{getItem:k=>storage.get(k),setItem:(k,v)=>{storageWrites.push(k);storage.set(k,v)},removeItem:k=>storage.delete(k)},
  addEventListener(n,fn){let a=winListeners.get(n)||[];a.push(fn);winListeners.set(n,a)}};
 const location={hash:role?'#role='+role+'&key=AbCdEfGhIjKlMnOpQrStUvWxYz0123456789--':'',pathname:'/',protocol:'https:',host:'www.test.app'};
 const history={replaceState(a,b,url){this.url=url}};
 const navigator={mediaDevices:{async getUserMedia(){const track={enabled:false,stop(){this.stopped=true}};tracks.push(track);
    return {active:true,getAudioTracks:()=>[track],getTracks:()=>[track]}}},vibrate:()=>{}};
 const ctx={window,sessionStorage:window.sessionStorage,document,location,history,navigator,WebSocket:WS,RTCPeerConnection:RTC,MediaStream:class{},
  URLSearchParams,Promise,console,setTimeout,clearTimeout};
 vm.runInNewContext(src,ctx);
 return {get,outs,tracks,storage,storageWrites,cookieJar,history,get sock(){return sock},get sockets(){return sockets},
   server:data=>sock.emit('message',data),
   entry:(name,remember=false)=>{get('nameInput').value=name;get('nameInput').emit('input');get('rememberName').checked=remember;
     get('nameForm').emit('submit',{preventDefault(){}})},
   roster:(onlineRoles=['user02','user03'])=>Array.from({length:10},(_,i)=>{const r=`user${String(i+1).padStart(2,'0')}`;
     return {role:r,online:onlineRoles.includes(r)||r===role,name:r===role?'A':r==='user02'?'Sky':r==='user03'?'Nora':null,busy:false}}),
   leave:()=>get('leaveButton').click(),
   userSelect:role=>{const item=get('contacts').children.find(x=>x.dataset.role===role);assert.ok(item,'selectable target');item.click()},
   pagehide:()=>{for(const fn of winListeners.get('pagehide')||[])fn({})},
   cookieChange:checked=>{get('rememberName').checked=checked;get('rememberName').emit('change')}
 };
}
async function nameAndCookie(){
 const h=harness('user01');
 assert.equal(h.sockets,0,'No socket before Next');
 assert.equal(h.get('rememberName').checked,false,'Opt-in off by default');
 assert.equal(h.history.url,'/','Sensitive QR fragment disappears from visible URL');
 assert.equal(h.storageWrites.length,0);assert.equal(h.storage.size,0);
 h.entry(' ');assert.equal(h.sockets,0);
 assert.match(h.get('entryError').textContent,/1/);
 h.entry('X'); await wait(10);
 assert.equal(h.outs[0].role,'user01');assert.equal(h.outs[0].name,'X');assert.equal(h.cookieJar.size,0);
 h.server({type:'ready',role:'user01',name:'X',people:h.roster(),iceServers:[]});
 assert.equal(h.get('selfName').textContent,'X');
 assert.equal(h.get('contacts').children.length,9);
 assert.ok(h.get('chatRecipient').children.some(c => c.value==='circle'),'Broadcast available without a call');
 h.leave(); assert.equal(h.sock.readyState,3);
 assert.equal(h.get('selfName').textContent,'You'); assert.equal(h.get('contacts').children.length,0);
 assert.equal(h.get('chatHistory').children.length,0);assert.equal(h.cookieJar.size,0);
 assert.equal(h.storageWrites.length,0);
 const remember=harness('user02');remember.entry('Z',true);await wait(10);
 assert.equal(decodeURIComponent(remember.cookieJar.get('faco_crumble_name')),'Z');
 remember.leave();assert.equal(remember.cookieJar.has('faco_crumble_name'),true,'Opted-in name persists');
 const formerly=harness('user02','Sam');assert.equal(formerly.get('nameInput').value,'Sam');
 assert.equal(formerly.get('rememberName').checked,true);
 formerly.cookieChange(false);assert.equal(formerly.cookieJar.size,0,'Unchecking deletes cookie');
 const landing=harness('');landing.entry('Name');assert.equal(landing.sockets,0);
 console.log('PASS name/consent: no pre-login socket, QR removed, optional cookie only, zero browser storage, leave wipes UI');
}
async function directAndGroup(){
 const h=harness('user01');h.entry('A');await wait(10);
 h.server({type:'ready',role:'user01',name:'A',people:h.roster(),iceServers:[]});
 h.userSelect('user02');
 assert.equal(h.get('callButton').disabled,false);
 h.get('callButton').click();await wait(10);
 assert.equal(h.outs.at(-1).type,'dial'); assert.equal(h.outs.at(-1).target,'user02');
 const cid='call-id';
 h.server({type:'invite-sent',id:cid,target:'user02'});
 h.server({type:'member-joined',id:cid,role:'user02',name:'Sky'});
 await wait(12);
 assert.equal(h.outs.at(-1).type,'signal');
 assert.equal(h.outs.at(-1).target,'user02');
 assert.equal(h.outs.at(-1).data.type,'offer');
 h.server({type:'signal',id:cid,from:'user02',data:{type:'answer',sdp:'answer'}});
 await wait(8);
 h.get('pttButton').emit('pointerdown',{button:0,pointerId:1,preventDefault(){}});
 assert.equal(h.tracks[0].enabled,true);h.get('pttButton').emit('pointerup');
 assert.equal(h.tracks[0].enabled,false);
 h.get('handsfreeMode').click();assert.equal(h.tracks[0].enabled,true);
 h.userSelect('user03');
 assert.equal(h.get('callButton').textContent,'Add selected to call +');
 h.get('callButton').click();await wait(8);
 assert.equal(h.outs.at(-1).type,'invite');assert.equal(h.outs.at(-1).target,'user03');
 h.server({type:'member-joined',id:cid,role:'user03',name:'Nora'});
 await wait(12);
 const peerOffers=h.outs.filter(x=>x.type==='signal' && x.data.type==='offer');
 assert.deepEqual(peerOffers.map(x=>x.target),['user02','user03']);
 assert.equal(h.get('participants').children.length,3);
 h.get('chatRecipient').value='room';h.get('chatRecipient').emit('change',{target:{value:'room'}});
 h.get('chatInput').value='Hello group';h.get('chatInput').emit('input');
 h.get('chatForm').emit('submit',{preventDefault(){}});
 assert.deepEqual({type:h.outs.at(-1).type,target:h.outs.at(-1).target,text:h.outs.at(-1).text},
   {type:'chat',target:'room',text:'Hello group'});
 h.server({type:'chat',id:cid,target:'room',from:'user02',fromName:'Sky',text:'<img src=x onerror=alert(1)>',time:123});
 const bubble=h.get('chatHistory').children[0];
 assert.equal(bubble.children[1].textContent,'<img src=x onerror=alert(1)>','Untrusted chat rendered only as text');
 h.get('endButton').click();
 assert.equal(h.tracks[0].stopped,true);
 assert.equal(h.get('chatHistory').children.length,1,'Group history cleared with call');
 assert.equal(h.storageWrites.length,0);
 console.log('PASS calls/chat: call anyone, group invite, per-peer SDP, hold-to-talk, handsfree, group message, XSS-safe, cleanup');
}
async function incomingAndDirect(){
 const h=harness('user05');h.entry('Mira');await wait(8);
 h.server({type:'ready',role:'user05',name:'Mira',people:h.roster(['user01','user02','user05']),iceServers:[]});
 h.server({type:'incoming',id:'call-x',from:'user01',fromName:'Ash',members:[{role:'user01',name:'Ash'}]});
 assert.match(h.get('callDetail').textContent,/Ash/);
 h.get('answerButton').click();await wait(10);
 assert.equal(h.outs.at(-1).type,'answer');
 h.server({type:'joined',id:'call-x',members:[{role:'user01',name:'Ash'},{role:'user05',name:'Mira'}]});
 await wait(10);
 h.server({type:'signal',id:'call-x',from:'user01',data:{type:'offer',sdp:'sdp'}});
 await wait(10);
 assert.equal(h.outs.at(-1).type,'signal');assert.equal(h.outs.at(-1).data.type,'answer');
 h.userSelect('user02');
 h.get('chatInput').value='Hey';h.get('chatInput').emit('input');
 h.get('chatForm').emit('submit',{preventDefault(){}});
 assert.equal(h.outs.at(-1).target,'user02');
 h.get('chatRecipient').value='circle';h.get('chatRecipient').emit('change',{target:{value:'circle'}});
 h.get('chatInput').value='Everyone online';h.get('chatInput').emit('input');
 h.get('chatForm').emit('submit',{preventDefault(){}});
 assert.equal(h.outs.at(-1).target,'circle');
 h.get('chatRecipient').value='user02';h.get('chatRecipient').emit('change',{target:{value:'user02'}});
 h.server({type:'chat',from:'user02',fromName:'Sky',target:'user05',text:'Hi Mira'});
 assert.equal(h.get('chatHistory').children[0].children[1].textContent,'Hi Mira');
 h.server({type:'session-expired'});
 assert.equal(h.get('entryScreen').classList.contains('hidden'),false);
 assert.equal(h.get('selfName').textContent,'You');
 console.log('PASS incoming: accept, answer SDP, one-to-one messages during call, rotation clears session');
}
Promise.resolve().then(nameAndCookie).then(directAndGroup).then(incomingAndDirect)
 .catch(e=>{console.error(e);process.exitCode=1});
