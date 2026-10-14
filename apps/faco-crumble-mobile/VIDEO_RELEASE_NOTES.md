# FACO Crumble Mobile Host 0.6.1: Opt-in Video Calling

This release extends the existing Android-phone-hosted FACO Crumble system without requiring an Ubuntu server. The Android host runs the session coordinator and manages ephemeral private QR credentials. Each participant opens their invitation in a phone browser with WebRTC support.

## Video call controls

- Audio-only is the default. Cameras are **off** until tapped on a live call.
- **Start video / Stop video** switches the local camera without ending the voice conversation, losing the group call, or altering push-to-talk and chat.
- **Flip camera** requests the front or rear camera when the phone/browser supports it. A failed request does not intentionally end an otherwise functioning voice call.
- On-screen, labelled video tiles represent the participants, with a local preview and a 10-person-capable scrollable grid. The FACO animated infinity remains part of the live call interface.
- When a new participant joins an existing call, the coordinator includes each current participant's camera status in the join event.
- Camera streams are released when disabled, when calls end, when the guest leaves the page, or when the host rotates/ends the session. The app contains no call recorder or video uploads.

## Security and network

The Android server's `Permissions-Policy` now authorizes its **own** page to request camera access (`camera=(self)`), instead of globally denying camera use. No camera capture starts from this policy alone; camera permission remains an explicit browser action. Room membership checks govern camera-state events. Audio/video data uses browser-to-browser WebRTC DTLS-SRTP when peers establish connectivity; the phone-hosted server coordinates only signaling, participant status and message forwarding. Message content is WSS-protected in transit but not end-to-end encrypted from the hosting phone.

As before, Internet mode needs a configured Cloudflare **named tunnel** with token/hostname; this release does not provide account-free ephemeral tunnel provisioning. Direct group video mesh can be demanding on cellular uplinks. TURN is not bundled, and there is no guarantee every network pair can connect. On same-Wi-Fi HTTP, Chromium blocks camera/microphone access to non-loopback origins unless appropriately secured with HTTPS.

## Verification boundaries

- Chromium simulated-WebSocket/peer integration test validates QR name entry, audio-first call, opt-in video, stopping camera, flipping camera, group addition, camera-status handling, denial recovery, exit cleanup, and 320–1280px layouts.
- Dart coordinator tests cover invitation credentials, authorization, call signaling, messages, new room-scoped video state, joining an established video call, camera state reset across calls and no-store/camera security headers.
- CI compiles an **arm64 debug-signed APK**, including Dart tests and JS syntax checks. It does not operate a real Android phone or a live Cloudflare tunnel.
- The optional `qa/test_real_webrtc_video.py` test needs host networking capable of local ICE connectivity. This environment blocks that full media handshake, so remote frames and real group-video quality remain **Needs Testing** on physical devices.

## Two-phone acceptance test

1. Install the APK on one Android phone and start an Internet session using your named Cloudflare tunnel credentials.
2. Share two private QR invites. Open them on two devices with a current Chromium-based browser. Enter names.
3. Call person-to-person with video OFF. Confirm audio/push-to-talk and direct chat still function.
4. Tap Start video on one phone. Confirm only that phone's camera permission is requested and its frame appears remotely. Tap Start video on the second phone.
5. Flip the camera front/rear while both videos run. Stop video and verify the local camera indicator turns off while voice continues.
6. Join a third participant into the existing call, test video and room messages, then leave/rejoin.
7. Crumble the session on the host and confirm every guest is disconnected and old QR credentials fail.
8. Repeat over cellular / Wi-Fi and with host screen locked to measure network/service longevity. Check battery impact and whether TURN is needed before wider deployment.
