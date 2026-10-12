'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('node:assert/strict');
const source=fs.readFileSync(path.join(__dirname,'../admin/admin.js'),'utf8');
class E {
 constructor(){this.textContent='';this.value='';this.dataset={};this.children=[];this.disabled=false;this.listeners={};this.attrs={};
  this.classSet=new Set();this.classList={add:x=>this.classSet.add(x),remove:x=>this.classSet.delete(x),
   contains:x=>this.classSet.has(x),toggle:(x,y)=>{if(y===true||(y===undefined&&!this.classSet.has(x)))this.classSet.add(x);else this.classSet.delete(x)}};
  this.lastElementChild={textContent:''};}
 addEventListener(n,fn){(this.listeners[n]??=[]).push(fn)}click(){for(let fn of this.listeners.click||[])fn({target:this})}
 setAttribute(k,v){this.attrs[k]=v}removeAttribute(k){delete this.attrs[k]}
 append(...els){this.children.push(...els)}replaceChildren(...els){this.children=els}
 focus(){}select(){}
}
async function go(){
 const map=new Map(),el=k=>{if(!map.has(k))map.set(k,new E());return map.get(k)};
 const landing=new E();landing.dataset.role='landing';landing.querySelector=()=>new E();
 const document={getElementById:el,createElement:()=>new E(),querySelectorAll:()=>[landing]};
 const history={replaceState(a,b,url){this.url=url}};
 const storage=new Map(),sessionStorage={getItem:k=>storage.get(k)||null,setItem:(k,v)=>storage.set(k,v)};
 const calls=[],copied=[],objectURLs=[];let confirms=0;
 const state={epoch:1,guestCount:10,baseUrl:'https://voice.trycloudflare.com',tunnelState:'Active',
  online:['user01','user03'],reason:'Started',invites:Array.from({length:10},(_,i)=>{const role=`user${String(i+1).padStart(2,'0')}`;
   return {role,label:`Person ${String(i+1).padStart(2,'0')}`,url:`https://voice.trycloudflare.com/#role=${role}&key=BB${i}`}})};
 const fetch=async(url,args={})=>{
  calls.push({url,args});assert.equal(args.headers['X-FACO-Admin'],'PRIVATEADMINKEYPRIVATEADMINKEYPRIVATEADMINKEY');
  if(url.startsWith('/qr/'))return {ok:true,blob:async()=>new Blob(['<svg></svg>'],{type:'image/svg+xml'})};
  if(url==='/api/rotate'){state.epoch++;state.reason='Rotated';}
  if(url==='/api/guest-count'){state.guestCount=JSON.parse(args.body).count;state.epoch++;
   state.invites=state.invites.slice(0,state.guestCount);}
  return{ok:true,json:async()=>JSON.parse(JSON.stringify(state))};
 };
 const URL={createObjectURL:b=>{const u=`blob:fake-${objectURLs.length}`;objectURLs.push(u);return u},revokeObjectURL() {}};
 const context={document,history,sessionStorage,location:{hash:'#admin=PRIVATEADMINKEYPRIVATEADMINKEYPRIVATEADMINKEY',pathname:'/'},
  fetch,URL,URLSearchParams,navigator:{clipboard:{writeText:async v=>copied.push(v)}},window:{addEventListener(){}},
  Blob,console,setTimeout:()=>1,clearTimeout:()=>{},setInterval:()=>1,confirm:()=>{confirms++;return true}};
 vm.runInNewContext(source,context);
 async function flush(){for(let i=0;i<24;i++)await Promise.resolve()}
 await flush();
 assert.equal(el('guestSlots').children.length,10);
 assert.equal(el('onlineCount').textContent,'2 participant(s) online');
 assert.equal(el('inviteUrl').value,'https://voice.trycloudflare.com/');
 assert.equal(history.url,'/');
 el('guestSlots').children[0].click();await flush();
 assert.equal(el('selectionTitle').textContent,'Person 01');
 assert.equal(el('inviteUrl').value,state.invites[0].url);
 el('guestSlots').children[7].click();await flush();
 assert.equal(el('selectionTitle').textContent,'Person 08');
 assert.equal(el('inviteUrl').value,state.invites[7].url);
 el('copyButton').click();await flush();assert.equal(copied.at(-1),state.invites[7].url);
 el('shareButton').click();await flush();assert.equal(copied.at(-1),state.invites[7].url);
 el('saveButton').click();await flush();assert.ok(objectURLs.length>=3);
 el('removeGuest').click();await flush();assert.equal(state.guestCount,9);assert.equal(state.epoch,2);
 el('rotateButton').click();await flush();assert.equal(state.epoch,3);
 assert.ok(confirms>=2);
 assert.ok(calls.some(x=>x.url==='/qr/user08.svg'));
 assert.ok(calls.every(x=>x.args.headers['X-FACO-Admin']));
 assert.ok(!state.invites.some(x=>x.role==='owner'));
 el('doctorToggle').click();await flush();
 assert.equal(el('doctorToggle').attrs['aria-expanded'],'true');
 assert.match(el('doctorResults').textContent,/Public tunnel: Active/);
 assert.match(el('doctorResults').textContent,/Invitations: 9 separate credentials/);
 assert.ok(!el('doctorResults').textContent.includes('PRIVATEADMINKEY'),'Doctor must not leak its key');
 el('doctorToggle').click();assert.equal(el('doctorToggle').attrs['aria-expanded'],'false');
 console.log('PASS QR dashboard: 10 equal people, landing, select, copy/share/save, capacity, rotation, local admin auth');
}
go().catch(e=>{console.error(e);process.exitCode=1});
