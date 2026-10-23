# FACO Crumble Desktop v0.6.2

**Speak. Disconnect. Crumble.**

Self-hosted temporary QR-invite communications for **Linux, Windows and macOS**, with no Android device or account required. The desktop OS is the **server**; guests use normal HTTPS browsers on any phone or computer. Included client has **encrypted WebRTC voice + opt-in video**, push-to-talk, group conversations and live text messaging. Two independent HTTPS listeners: the public calling website on `127.0.0.1:8787` (exposed only via your chosen HTTPS tunnel), and the private administrator QR dashboard on **127.0.0.1:8788** (never exposed by FACO).

## Editions, not dependencies

- **Desktop host**: Linux, Windows or macOS runs the Python/aiohttp communication coordinator; no Android APK or Android phone is needed.
- **Mobile host**: separate FACO Crumble Android APK v0.6.1 hosts the communication coordinator on an Android phone. Both desktop and mobile share the same QR/browser client protocol.
- A member joining as a guest needs **no FACO software**: scan an individual private QR in a standard mobile/desktop browser.

## Install and start

### Linux (standard user installation)

```sh
./install.sh --check-only
./install.sh --no-launch
~/.local/bin/faco-crumble --quick
```

The Linux per-user app installs under `~/.local/share/faco-crumble/app`. Optional custom mount paths require `--prefix` with a real writable parent folder. Standard settings use `~/.config/faco-crumble` (or `$XDG_CONFIG_HOME/faco-crumble`). In an interactive terminal `./install.sh` also starts the program.

### Windows

Open the Windows release ZIP, extract the **whole** `FACO Crumble` folder anywhere and run **`FACO Crumble.exe`**. A small terminal console displays launch diagnostics and the local admin URL, and the control panel opens automatically in the browser. The Python runtime and dependencies are bundled. Default participant-count setting: `%APPDATA%\FACO\Crumble\settings.json`.

### macOS

Extract the macOS ZIP, open **`FACO Crumble.app`**, and the localhost QR panel opens in your browser. It bundles Python dependencies. Mac test builds are unsigned/unnotarized: macOS may initially block launch; review and use your system's **Open Anyway** option if you trust the package. Default participant-count setting: `~/Library/Application Support/FACO/Crumble/settings.json`. An Intel-only build requires Rosetta on Apple Silicon Macs.

**Native ZIP build verification:** GitHub Actions compiles the executables and runs the program on corresponding hosted OS runners. Physical microphone/camera tests across consumer networks remain required.

### Cross-platform source (without native binary)

If native builds are unavailable: install Python 3.10+ and `pip install -r requirements.txt`, then run `python launcher.py --quick` inside this folder.

## Hosting a session

- `--quick` (default): You must separately install **Cloudflare `cloudflared`**. This runs a temporary quick tunnel and generates the HTTPS public QR address, then up to ten individual credential-bearing QR invitations.
- `--domain https://your.domain`: Uses an independently configured HTTPS reverse proxy/tunnel to public port 8787. Never expose the admin port.
- `--local --no-open`: Loopback-only test; browser audio/video normally require HTTPS when not on localhost.
- `--public-port 8787 --admin-port 8788`: Change local port numbers if needed.

The private admin control panel opens automatically on a desktop with a browser. For headless systems, copy the **LOCAL CONTROL CENTER** URL from console on that same desktop. `cloudflared` may be installed in your PATH, standard macOS Homebrew locations, Linux user bin, or Windows program directory; optionally set `FACO_CLOUDFLARED` to its actual executable path.

1. Start a session. Every start generates fresh cryptographically random QR credentials; each QR grants a single live identity.
2. Share only the individual member QR with its intended recipient. The general landing QR is not a credential.
3. Each member enters a display name (1–40 characters) and can call, video-call (camera off until manually enabled), or message other online members. Up to ten people can join one call. Message delivery is live only.
4. End/restart the host or click **Rotate All** to invalidate current invitations. Closing the guest tab releases microphone/camera tracks and local app state. The optional remember-name cookie stores **only the guest's name**; it is off by default.

## Privacy, security, limitations

- Voice/video use encrypted browser WebRTC peer connections, subject to network connectivity. Strict NATs may require a correctly configured TURN relay via `FACO_ICE_SERVERS_JSON`.
- Messages travel over HTTPS/WSS; **they are not end-to-end encrypted from the coordinating desktop server**.
- No account registration, retained chat database or recorded calls are implemented. Cloudflare, ISPs and browsers may retain connection metadata or browsing history. `cloudflared` connection diagnostics can be logged on the host.
- QR invites grant bearer access and are invalidated on restart/rotation; do not publish private QR codes.
- Browser-tab closure is not equivalent to operating-system process termination; close/stop the desktop host to end everyone’s session.
- This release is not a signed/notarized production build. Physical Windows/macOS calling, camera handling, VPN/TURN and browser shutdown remain to be verified beyond CI tests.

## Developer verification

```sh
python -m unittest discover -s tests -p 'test_signaling.py'
python -m unittest discover -s tests -p 'test_video_signaling.py'
python -m unittest discover -s tests -p 'test_tunnel.py'
node --check public/app.js
node tests/test_client_mock.cjs
node tests/test_admin_mock.cjs
# Optional with Playwright + Chromium:
python qa/test_video_browser.py
```
