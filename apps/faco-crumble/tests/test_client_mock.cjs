const fs=require('fs'),assert=require('assert'),path=require('path');
const base=path.resolve(__dirname,'..');
const index=fs.readFileSync(path.join(base,'public','index.html'),'utf8');
const js=fs.readFileSync(path.join(base,'public','app.js'),'utf8');
const css=fs.readFileSync(path.join(base,'public','style.css'),'utf8');
for(const id of ['nameNext','callInfinityStage','videoGallery','videoControls','cameraButton','flipCameraButton','videoCount','chatInput','optionsPanel','leaveButton'])
  assert(index.includes(`id="${id}"`),`Missing functional UI ${id}`);
for(const s of ['getUserMedia','addTransceiver','replaceTrack','sendCameraState','cameraOn','cameraOff','cameraGeneration','RTCPeerConnection','WebSocket','closePeer'])
  assert(js.includes(s),`Missing video/call logic ${s}`);
assert(!js.includes('localStorage.setItem') && !js.includes('sessionStorage.setItem'),'Guest credentials must not be saved in web storage');
assert(css.includes('infinityFlow'),'No live FACO infinity');
console.log('PASS video-capable FACO guest UI contract, privacy storage and existing call assets');
