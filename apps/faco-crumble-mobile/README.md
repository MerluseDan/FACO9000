# FACO Crumble Mobile Host v0.6.0 (Android)

**Speak. Disconnect. Crumble.**

This is a new Android phone-hosted edition of FACO Crumble. It contains the actual HTTP/WebSocket coordination server in a Dart background Android foreground-service isolate. The other participants use the **existing v0.5.1 browser client** over an HTTPS tunnel, or this APK's Join QR scanner. No Ubuntu server is necessary.

> **Status:** Source implementation and build pipeline. Real-phone calls, native tunnel service behavior and this APK build must be checked before a production claim. GitHub Actions builds a DEBUG/test-signed APK; this is **not** a Play Store release. A Cloudflare *named tunnel with token and public hostname* is needed for Internet calls. Free, anonymous Quick Tunnels are not bundled into this release.

## User experience

1. Open APK. Choose **Host session** or **Join session**.
2. Host picks 1–10 person slots. For Internet, provide an existing Cloudflare tunnel connector token and hostname (HTTPS URL). For local Wi-Fi, message using LAN links; browser microphones generally require a trusted HTTPS origin so voice is not promised on LAN HTTP.
3. Host taps **Start session**. Android foreground service runs the HTTP and WebSocket coordinator on the **host phone** (`0.0.0.0:8787`). Tunnel plugin exposes that phone's port to Cloudflare. Neither signaling nor chat is coordinated by a second FACO server.
4. Phone generates a landing-page QR and 1–10 distinct private invitation QR codes containing ephemeral credentials. The host can join using Person 01. Guests use ordinary Android/iOS browsers with microphone permission and HTTPS.
5. Any participant can call, invite others, send direct/group messages, or talk hands-free/push-to-talk. Actual voice media uses browser-to-browser DTLS-SRTP WebRTC. Turn servers can be required on restricted networks, especially cellular; this version includes STUN only.
6. Select **Crumble session** to tear down phone server, close sockets, destroy invitation keys, and stop the tunnel. QR access is rotated by Restart/Rotate and on tunnel reconnection. The server does not write participant credentials, message content or call recordings to disk.

**Privacy:** The mobile app does **not** save the Cloudflare connector token, chat messages, or QR credentials to preferences/files. The website's optional opt-in *display name cookie* is unchanged from v0.5.1. Android, browsers, QR scanners, and Cloudflare may retain metadata. Copying/sharing a QR through another app may leave traces there. No software can promise complete erasure of all third-party records.

## How Cloudflare is configured (one-time)

1. Create a named tunnel in your own [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) dashboard. Set its public hostname, e.g. `voice.example.com`, to `http://127.0.0.1:8787`. This routes the public HTTPS URL **to the Android phone's local server**, not to Ubuntu.
2. Copy the **tunnel connector token**. On your phone choose Host, enter `https://voice.example.com`, paste the token, and Start.
3. When connected, participant QR codes become available. Token is not saved by FACO; paste it again when hosting a new session. External DNS and existing Cloudflare setup are outside the APK.

Cloudflare's own network and potential relay services participate in transport. Named tunnel token remains valid in Cloudflare until revoked even after Crumble stops; FACO destroys only per-session invitation keys. A per-session fresh Cloudflare tunnel would require API provisioning and deletion not present here.

## Android foreground service and limitations

- Uses `flutter_background_service` Android `connectedDevice` foreground-service type, notification, and a separate server FlutterEngine. No autostart on boot. Stops on explicit Crumble.
- Uses `cloudflared_tunnel` plugin for the outbound named connector. Its own native service handles the Cloudflare connection. Android restrictions, OEM battery policies, network handoffs and force-stop can still terminate hosting; physical-device QA is mandatory.
- Host joins its own conversation in the phone browser using loopback `127.0.0.1` (a secure context in Chromium). Any LAN device using plain `http://192.168...` cannot reliably access microphones; use HTTPS Internet mode for voice.
- Phones connected over restrictive cellular NAT may need a TURN server. This build only configures public STUN, and cannot guarantee connectivity between all providers.
- Group audio uses WebRTC mesh, so large calls consume substantial phone uplink data.
- This is a sideload/test APK build, not a secure production update channel. Install over an older APK signed by a different key requires uninstalling the old one.

## Build APK

The repository workflow [`.github/workflows/android-apk.yml`](../../.github/workflows/android-apk.yml) runs automatically after the source lands on `main`, or from GitHub **Actions → FACO Crumble Mobile Host APK → Run workflow**. Download its APK artifact after a successful run.

Locally with Flutter SDK installed:

```bash
bash build_apk.sh
```

It will generate the Android platform, patch required permissions, run Dart tests, and compile `build/app/outputs/flutter-apk/app-debug.apk`.

Source dependencies: Flutter stable/Dart ≥3.5, `cloudflared_tunnel` 1.0.1, `flutter_background_service` 5.1.0, `qr_flutter` 4.1.0, `mobile_scanner` 7.4.2, `url_launcher`, `crypto`. Native `cloudflared_tunnel` Android binaries are packaged by that third-party plugin. Review its supply chain and licenses before public distribution.

## Privacy and security details

- Cryptographically secure 32-byte random credentials, 10 independent role slots. Credential hashes checked on auth. One active device per invitation.
- Rate-limited messages and basic WebSocket authentication timing guard. Origin and room membership checks on calls/signals, including offerer ordering.
- No participant admin endpoint. QR tokens live in host phone's session memory only. Web client strips URL fragments from address bar after read, though browser history and third-party traces cannot be guaranteed absent.
- Security headers use no-store and CSP; no analytics or CDN scripts.
- Messaging is WSS-encrypted to the mobile host, **not** end-to-end encrypted. The host coordinator can read forwarded text in memory. Voice media uses WebRTC DTLS-SRTP between participant browsers when connected.

## QA expectations

Run automated protocol tests, APK compilation, and at least two physical Android devices with real Cloudflare named tunnel. For offline Wi-Fi tests verify text signaling only until proper HTTPS is implemented. Test 1-to-1 and 3-person audio, microphone permissions, standby/lock, leave/rejoin, rotation, tunnel reconnect, cellular-to-Wi-Fi transitions, and explicit Crumble clearing.
