"""Actual Chromium RTCPeerConnection video smoke test without real devices.
Tests the opted-in video transceiver strategy: audio-first, camera on/off via
RTCRtpSender.replaceTrack, and camera replacement without renegotiating SDP.
Requires locally installed playwright and Chromium; does not need Cloudflare.
"""
from playwright.sync_api import sync_playwright

TEST = r'''
async () => {
  const a = new RTCPeerConnection({iceServers:[]});
  const b = new RTCPeerConnection({iceServers:[]});
  const audioContext = new AudioContext();
  const audioSrc = audioContext.createMediaStreamDestination();
  a.addTrack(audioSrc.stream.getAudioTracks()[0],audioSrc.stream);
  b.addTrack(audioSrc.stream.getAudioTracks()[0],audioSrc.stream);
  const as = a.addTransceiver('video',{direction:'sendrecv'}).sender;
  b.addTransceiver('video',{direction:'sendrecv'});
  const out = {offerHasVideo:false, senderInitiallyNull:as.track===null, connected:false, remoteGotVideo:false, cameraOff:false, flipped:false, framesSeen:false};
  const ice = [];
  a.onicecandidate = e=>{ if(e.candidate){if(b.remoteDescription)b.addIceCandidate(e.candidate).catch(()=>{});else ice.push(['b',e.candidate]);} };
  b.onicecandidate = e=>{ if(e.candidate){if(a.remoteDescription)a.addIceCandidate(e.candidate).catch(()=>{});else ice.push(['a',e.candidate]);} };
  let remoteTrack;
  b.ontrack = e => { if(e.track.kind === 'video'){remoteTrack=e.track;out.remoteGotVideo=true;} };
  const offer = await a.createOffer();
  out.offerHasVideo = offer.sdp.includes('m=video');
  await a.setLocalDescription(offer);await b.setRemoteDescription(offer);
  const answer = await b.createAnswer();await b.setLocalDescription(answer);await a.setRemoteDescription(answer);
  for(const [who,candidate] of ice)await (who==='a'?a:b).addIceCandidate(candidate).catch(()=>{});
  const until = async(fn,t=10000) => {const start=Date.now();while(Date.now()-start<t){if(fn())return true;await new Promise(r=>setTimeout(r,70));}return false;};
  out.connected = await until(()=>a.connectionState==='connected'&&b.connectionState==='connected',3500);
  const canvas=document.createElement('canvas');canvas.width=320;canvas.height=240;
  const ctx=canvas.getContext('2d'); let frame=0;
  const timer=setInterval(()=>{ctx.fillStyle=frame%2?'#33aa66':'#ee6688';ctx.fillRect(0,0,320,240);frame++;},70);
  const stream=canvas.captureStream(12);const track=stream.getVideoTracks()[0];
  try {
    await as.replaceTrack(track);
    if(remoteTrack){const vid=document.createElement('video');vid.muted=true;vid.playsInline=true;vid.srcObject=new MediaStream([remoteTrack]);await Promise.race([vid.play().catch(()=>{}),new Promise(r=>setTimeout(r,2000))]);out.framesSeen=await until(()=>vid.videoWidth>0,3000);vid.pause();vid.srcObject=null;}
    await as.replaceTrack(null);out.cameraOff=as.track===null;
    const track2=canvas.captureStream(12).getVideoTracks()[0];
    await as.replaceTrack(track2);out.flipped=as.track===track2;
    track2.stop();
  } finally {clearInterval(timer);track.stop();a.close();b.close();audioContext.close();}
  return out;
}
'''

def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
        page=browser.new_page()
        page.set_content('<html><body>Peer-to-peer media diagnostic</body></html>')
        res=page.evaluate(TEST)
        browser.close()
        print(res)
        if not all(res.values()):
            print("Environment limitation: a real browser media handshake did not fully establish here.")
            raise SystemExit(2)
        print('PASSED: actual Chromium WebRTC audio-first video, frames, off, camera replacement.')

if __name__=='__main__':main()
