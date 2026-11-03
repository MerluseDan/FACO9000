#!/usr/bin/env node
/*
SRDE-P1: independent reproduction of the 2026-11-03 FB15k237-V1 prototype.
Requirements: Node 20+; internet for GitHub raw files unless SRDE_DATA_DIR is set.
Does NOT claim to be the installed FACO SRDE runtime.
Uses public GraIL data, training-only mined path weights, zero overlap of entities.
Check the frozen dataset Git blob hashes in real_inductive_results.json.
*/
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const ROOT='https://raw.githubusercontent.com/kkteru/grail/master/';
const FILES=['data/fb237_v1/train.txt','data/fb237_v1_ind/train.txt','data/fb237_v1_ind/valid.txt','data/fb237_v1_ind/test.txt'];
const EXPECTED=['d38ca521bab6fb8daad8255670abaf9d66dc6dc6','0ef0b9eae390e4932a7a33c490209521419c1a0f','4c56465129a66f2df777cac5b02569f2b1072a87','1dcb0a161bcd29c034a54e47a373dc06bd9f6ebe'];
let raw=[];
if (process.argv.includes('--self-test')) {
  const example=(i,n)=>Array.from({length:n},(_,j)=>`n${(j+i)%15}\tr${j%4}\tn${(j*3+5+i)%15}`).join('\n')+'\n';
  raw=[example(0,50),example(1,30),example(2,10),example(3,10)];
} else {
  for(let i=0;i<FILES.length;i++){
    const rel=FILES[i];let s;
    if(process.env.SRDE_DATA_DIR)s=fs.readFileSync(path.join(process.env.SRDE_DATA_DIR,rel),'utf8');
    else {const r=await fetch(ROOT+rel);if(!r.ok)throw Error(`${r.status} downloading ${rel}`);s=await r.text();}
    const blob=Buffer.from(s,'utf8');const hash=crypto.createHash('sha1').update(Buffer.concat([Buffer.from(`blob ${blob.length}\0`),blob])).digest('hex');
    if(hash!==EXPECTED[i])throw Error(`Git blob mismatch in ${rel}: ${hash}; expected ${EXPECTED[i]}`);
    raw.push(s);
  }
}
const E=new Map(),R=new Map();
const index=(m,s)=>{if(!m.has(s))m.set(s,m.size);return m.get(s);};
const parse=s=>s.trim().split(/\r?\n/).filter(Boolean).map(line=>{let p=line.split('\t');if(p.length!==3)throw Error('Bad triple');return {h:index(E,p[0]),r:index(R,p[1]),t:index(E,p[2])};});
const [tr,inf,va,te]=raw.map(parse);
function mkgraph(rows){
 let a=new Map(),deg=new Map(),tails=new Map(),known=new Set();
 function add(n,e){if(!a.has(n))a.set(n,[]);a.get(n).push(e);}
 for(const z of rows){
  add(z.h,{to:z.t,s:2*z.r,h:z.h,r:z.r,t:z.t});add(z.t,{to:z.h,s:2*z.r+1,h:z.h,r:z.r,t:z.t});
  deg.set(z.h,(deg.get(z.h)||0)+1);deg.set(z.t,(deg.get(z.t)||0)+1);
  if(!tails.has(z.r))tails.set(z.r,new Set());tails.get(z.r).add(z.t);known.add(`${z.h}|${z.r}|${z.t}`);
 }
 for(const entries of a.values())entries.sort((x,y)=>x.to-y.to||x.s-y.s);
 return {a,deg,tails,known};
}
const gt=mkgraph(tr),gi=mkgraph(inf);
let walks=0,expansions=0,cutoffs=0;
function walks3(g,h,r,t){
 let p=[],work=0,cut=false;const forbidden=e=>e.h===h&&e.r===r&&e.t===t;
 outer:for(const e1 of g.a.get(h)||[]){
  if(forbidden(e1)||e1.to===h||e1.to===t)continue;
  const x=e1.to;
  for(const e2 of g.a.get(x)||[]){
   if(++work>12000){cut=true;break outer;}
   if(forbidden(e2)||e2.to===h)continue;
   const y=e2.to;
   if(y===t){p.push({len:2,code:`${e1.s}.${e2.s}`,via:x});continue;}
   if(y===x)continue;
   for(const e3 of g.a.get(y)||[]){
    if(++work>12000){cut=true;break outer;}
    if(!forbidden(e3)&&e3.to===t)p.push({len:3,code:`${e1.s}.${e2.s}.${e3.s}`,via:x});
   }
  }
 }
 walks++;expansions+=work;if(cut)cutoffs++;return p;
}
let seed=20261103>>>0;
function rand(){seed^=seed<<13;seed^=seed>>>17;seed^=seed<<5;return(seed>>>0)/4294967296;}
function negatives(g,z,n,forbidden){
 let pool=[...(g.tails.get(z.r)||[])];if(pool.length<3)pool=[...g.a.keys()];let out=[],used=new Set([z.t]),k=0;
 while(out.length<n&&k++<n*140){let u=pool[Math.floor(rand()*pool.length)];if(u===z.h||used.has(u)||forbidden.has(`${z.h}|${z.r}|${u}`))continue;used.add(u);out.push(u);}
 if(out.length<n){pool=[...g.a.keys()];while(out.length<n&&k++<n*450){let u=pool[Math.floor(rand()*pool.length)];if(u===z.h||used.has(u)||forbidden.has(`${z.h}|${z.r}|${u}`))continue;used.add(u);out.push(u);}}
 return out;
}
const totals=new Map(),pattern=new Map();
function count(z,paths,positive){
 if(!totals.has(z.r))totals.set(z.r,{p:0,n:0});totals.get(z.r)[positive?'p':'n']++;
 for(const c of new Set(paths.map(x=>x.code))){const key=`${z.r}|${c}`;if(!pattern.has(key))pattern.set(key,{p:0,n:0});pattern.get(key)[positive?'p':'n']++;}
}
const t0=Date.now();
for(const z of tr){count(z,walks3(gt,z.h,z.r,z.t),true);for(const t of negatives(gt,z,2,gt.known))count(z,walks3(gt,z.h,z.r,t),false);}
const trainingMs=Date.now()-t0;
let W=new Map();
for(const [key,v] of pattern){let r=Number(key.split('|',1)[0]),tot=totals.get(r);if(v.p<2||v.p+v.n<3)continue;let w=Math.log((v.p+1)/(tot.p+2))-Math.log((v.n+1)/(tot.n+2));W.set(key,Math.max(-4,Math.min(4,w)));}
const actual=new Set([...inf,...va,...te].map(z=>`${z.h}|${z.r}|${z.t}`));
const packets=rows=>rows.map(z=>({z,targets:[z.t,...negatives(gi,z,20,actual)]}));
const vp=packets(va),tp=packets(te);
const methods=['CN','AA','Katz','Typed','TypedMax','GraphConsensus','Portal','PortalNoQuorum'];
function score(z,t){
 const p=walks3(gi,z.h,z.r,t);let cn=0,aa=0,k3=0,typed=0,max=0,via=new Map(),via2=new Map();
 for(const v of p){const wt=(W.get(`${z.r}|${v.code}`)||0)/(v.len===2?1:1.6);
  if(v.len===2){cn++;aa+=1/Math.log(2+(gi.deg.get(v.via)||0));}else k3++;
  typed+=wt;max=Math.max(max,wt);
  if(!via.has(v.via)||via.get(v.via)<wt)via.set(v.via,wt);
  if(v.len===2&&(!via2.has(v.via)||via2.get(v.via)<wt))via2.set(v.via,wt);
 }
 function agg(arr,q){let pos=arr.filter(v=>v>0).sort((a,b)=>b-a).slice(0,3),neg=arr.filter(v=>v<0).sort((a,b)=>a-b).slice(0,2);
  return(pos.length>=q?1:pos.length?.33:0)*pos.reduce((a,b)=>a+b,0)+.55*neg.reduce((a,b)=>a+b,0);}
 const all=[...via.values()],two=[...via2.values()],quorum2=two.filter(v=>v>.1).length>=2;
 return {CN:cn,AA:aa,Katz:cn+.07*k3,Typed:typed/Math.sqrt(1+p.length),TypedMax:max,
 GraphConsensus:agg(all,2),Portal:quorum2?agg(two,2):agg(all,2),PortalNoQuorum:agg(all,1),support:p.filter(x=>(W.get(`${z.r}|${x.code}`)||0)>0).length};
}
function rank(s){let gt=0,eq=0,lower=0;for(let i=1;i<s.length;i++){if(s[i]>s[0]+1e-10)gt++;else if(s[i]<s[0]-1e-10)lower++;else eq++;}
 let mrr=0;for(let i=0;i<=eq;i++)mrr+=1/(1+gt+i);mrr/=eq+1;
 return {auc:(lower+.5*eq)/(s.length-1),mrr,hits1:gt===0?1/(eq+1):0,hits10:gt>=10?0:Math.max(0,Math.min(1,(10-gt)/(eq+1)))};
}
function evaluate(packs,keepRows=false){let sums=Object.fromEntries(methods.map(x=>[x,{auc:0,mrr:0,hits1:0,hits10:0}]));let rows=[],supported=0,short=0;
 for(const {z,targets} of packs){if(targets.length!==21)short++;const F=targets.map(t=>score(z,t));if(F[0].support)supported++;let row={};
  for(const m of methods){const r=rank(F.map(x=>x[m]));row[m]=r;for(const metric in r)sums[m][metric]+=r[metric];}
  if(keepRows)rows.push(row);
 }
 for(const m of methods)for(const metric in sums[m])sums[m][metric]/=packs.length;
 return {n:packs.length,supported,short,metrics:sums,rows};
}
const dev=evaluate(vp),test=evaluate(tp,true);
function ci(a,b,metric,n=2000){const d=test.rows.map(x=>x[a][metric]-x[b][metric]),values=[];for(let k=0;k<n;k++){let s=0;for(let i=0;i<d.length;i++)s+=d[Math.floor(rand()*d.length)];values.push(s/d.length);}
 values.sort((a,b)=>a-b);return {difference:d.reduce((a,b)=>a+b,0)/d.length,ci95:[values[Math.floor(.025*n)],values[Math.floor(.975*n)]]};}
const summary={dataset:'GraIL FB15k237-V1',paths:FILES,protocol:'Training-only relation-path coefficients; 2 train negatives, 20 inductive evaluation negatives; 3 hops max, 12000 expansions; paired AUC/MRR.',
 train_edges:tr.length,inference_edges:inf.length,validation_edges:va.length,test_edges:te.length,relations:R.size,
 train_entity_count:new Set(tr.flatMap(z=>[z.h,z.t])).size,inference_entity_count:new Set(inf.flatMap(z=>[z.h,z.t])).size,
 entity_overlap:[...new Set(tr.flatMap(z=>[z.h,z.t]))].filter(x=>new Set(inf.flatMap(z=>[z.h,z.t])).has(x)).length,
 pattern_types:pattern.size,learned_rules:W.size,trainingMs,walks,expansions,cutoffs,
 validation:{n:dev.n,supported:dev.supported,metrics:dev.metrics},test:{n:test.n,supported:test.supported,metrics:test.metrics},
 bootstraps:{portal_vs_katz:ci('Portal','Katz','auc'),portal_vs_consensus:ci('Portal','GraphConsensus','auc'),portal_vs_typed:ci('Portal','Typed','auc')},short_packets:dev.short+test.short};
fs.writeFileSync(path.join(process.cwd(),process.argv.includes('--self-test')?'real_inductive_self_test.json':'real_inductive_rerun.json'),JSON.stringify(summary,null,2));
console.log(JSON.stringify({protocol:summary.protocol,train_edges:summary.train_edges,test_edges:summary.test_edges,entity_overlap:summary.entity_overlap,validation:summary.validation.metrics.Portal,test_portal:summary.test.metrics.Portal,test_katz:summary.test.metrics.Katz,test_graph:summary.test.metrics.GraphConsensus,cutoffs,short_packets:summary.short_packets},null,2));
