# FACO Crumble v0.5.1 | Standard Linux Installation + Cloudlight Infinity

**Speak. Disconnect. Crumble.**

An Ubuntu-hosted, invite-only, browser-based voice-and-messaging app for **up to ten equal participants**. Nobody is a privileged "host" caller. The **Ubuntu server coordinates** access, online presence, call rooms, invitations and live text delivery. The **media runs between browsers using encrypted WebRTC**, not an Ubuntu audio mixer. The separate localhost-only Ubuntu dashboard is solely for administration and sharing QR codes.

## Interface and features (retained from v0.5.0)

**Cloudlight Electric** is the new interface throughout: white/cloud-blue integrated surfaces, electric-blue focal accents, restrained borders, proper branded vector FACO infinity logo and mobile-first screen density. Neither public participants nor Ubuntu administrators need external fonts, images, icons or JavaScript CDNs. The full brand logo is included in `assets/FACO_Crumble_Full_Logo.svg`.

**The infinity becomes a live call indicator:** idle is still, incoming/ringing animates quickly, and an active call runs a small bright tracer around the same thick ribbon in a continuous loop. Ending/leaving the call stops the animation; reduced-motion operating-system preference or the app toggle stops it too. FACO's lightweight inline infinity replaces interruptive blocking “Working” overlays for short operations.

**FACO Options** is intentionally tucked away from the main calling interface. It includes microphone selection and quick access test, speaker selection where browser-supported and a speaker test, animated infinity toggle, Focus view (hide chat), optional incoming sound, **Quick Doctor**, and **Reset / Cancel / Apply**. Options live only in this open page's memory and are erased on exit. This does not change the optional display-name-only cookie preference. Some Android browsers may not expose output device selection; system output remains available.

**Mobile simplicity:** Name → Next, nearby people, then a Call/Messages switch. A mini return-to-call strip appears when viewing messages during a live call. The entire layout fits a 390px Android viewport without horizontal scrolling. Desktop shows people, live infinity call, and messages side by side.

Core v0.4 capabilities retained unchanged: **ten invite slots; equal participant permissions; independent direct/group WebRTC calls; invite more members during a call; private, room, and circle messaging; optional name cookie defaulting off; per-tunnel credential rotation; local-only Ubuntu QR control panel**.

## Installation on Ubuntu and other Linux desktops (v0.5.1)

FACO Crumble now uses **the standard Linux per-user XDG directories** by default. No sudo, no private FACO drive, no hardcoded usernames and no required `/opt` system-wide folder. Existing settings are preserved. Stop any older instance before upgrading; each restart rotates the QR credentials.

From the [source ZIP](./) or a checkout, open a terminal inside the extracted repository:

```bash
./install.sh --check-only                  # FAST preflight; makes no installation changes
./install.sh --standard --check-only       # Run server + browser-mock + real-process tests
./install.sh --full-audit --check-only     # Full Doctor / SVG / privacy / Linux checks
./install.sh --no-launch                   # Install into the standard Linux per-user location
faco-crumble --quick                       # Start the Ubuntu server and share the generated QR invites
```

For first installation, `./install.sh` installs the application, prompts for Enter in an interactive terminal and launches it automatically. On a terminal where `~/.local/bin` is not in `PATH`, use `~/.local/bin/faco-crumble --quick`. You can alternatively click the **FACO Crumble** application entry in your desktop launcher. No system service or autostart is installed without your action.

**OS-default directories:**

| Purpose | Linux location (defaults) |
|---|---|
| Application source | `~/.local/share/faco-crumble/app/` |
| Launcher command | `~/.local/bin/faco-crumble` |
| Desktop entry | `~/.local/share/applications/faco-crumble.desktop` |
| Python runtime environment (only if needed) | `~/.local/share/faco-crumble/venv/` |
| Saved guest-count configuration | `~/.config/faco-crumble/settings.json` |
| Logs | `~/.local/state/faco-crumble/tunnel.log` |
| Cache | `~/.cache/faco-crumble/` |

`XDG_DATA_HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, and `XDG_CACHE_HOME` are respected when configured. On a typical Ubuntu install, **the OS drive is now the default**. `~/.local/share` is the per-user standard and does not need administrator elevation. An optional shared FACO Python runtime can be selected by explicitly setting `FACO_SHARED_ROOT`; it is not a required installation path.

**Optional custom app directory:** `./install.sh --prefix "/path/to/mounted-drive/faco-crumble" --no-launch`. The **parent folder must exist and be writable** before installation. If the custom drive is missing, interactive installation offers exactly **Use OS Default Location** or **Cancel Installation**. Noninteractive mode aborts instead of silently installing somewhere else. The app's config, logs and environment remain at the OS-standard user paths unless their XDG variables are explicitly customized.

Requirements: Linux with Python 3.10+ (`python3-venv` if a virtual environment is needed), `aiohttp`, `qrcode`, and `cloudflared` for a temporary public HTTPS tunnel. Runtime checks reuse compatible system/selected shared dependencies before attempting a user-scope pip install. Cloudflare itself must already be installed separately.

Other run modes:

```bash
faco-crumble --local --no-open                # Local-only testing (remote mic needs HTTPS)
faco-crumble --domain https://talk.example.com # Your existing HTTPS reverse proxy
```

`--domain` requires an independently configured HTTPS reverse proxy/tunnel. `--quick` runs a managed Cloudflare Quick Tunnel; its URL can change and is not designed for guaranteed uptime. The Ubuntu control panel stays bound to `127.0.0.1:8788`.

### QR console

The local Ubuntu browser opens the redesigned Cloudlight control panel automatically when a desktop is available. Otherwise use the **LOCAL CONTROL CENTER** URL printed in your terminal on **that same Ubuntu computer**.

- Local public website: `127.0.0.1:8787` (Cloudflare tunnels this **only**).
- Local QR/admin dashboard: `127.0.0.1:8788` (never exposed through Cloudflare).
- First QR: **Cloudflare public link**. Opens the welcome page but **does not grant entry**.
- Remaining QRs: **Person 01** through **Person 10**, each with a different cryptographically generated credential embedded in the QR and shareable URL.
- Optional 1–10 participant count, save/copy/share QR, Rotate All, and inline administrator Quick Doctor. Each new application start, rotated set, and managed tunnel restart/reconnection invalidates all older QR credentials and disconnects current calls.

The dashboard itself uses an admin token printed in the local terminal and locally stored in that **localhost-admin tab’s** `sessionStorage` for its own convenience. The public participant page does not save invites or preferences. This is **separate from the public phone-facing app**.

### Each participant

1. Scan the private **Person 01–10** QR. A **name-first** welcome screen opens.
2. Enter a name with **1–40 characters**. The optional checkbox **“Remember my name on this device”** is **off unless that person previously opted in**. When checked, FACO saves a 30-day `SameSite=Strict` browser cookie containing **only the chosen display name**. No credentials, chat content or call history are saved in this cookie. Unchecking deletes it.
3. Tap **Next**. The page shows available people. Any online participant may **call any other** online participant, regardless of who issued their QR.
4. When already in a call, tap another available person and **Add selected to call**. You can build a conversation of up to ten people (browser WebRTC mesh). Each person accepts or declines their own invitation.
5. Voice can be **Push to talk** (mic muted until held) or **Hands-free** (live mic). Hold-to-talk is also available with the Space key on desktop.
6. Under **Messages**, select a person for direct chat, **Everyone online** for a broadcast, or **Everyone in call** for a current-call group message. Text is delivered immediately to recipients who are online and is never queued for offline delivery.
7. **Leave & clear session** or close the browser to drop local login, names, messages, audio tracks, and peer connections from the app's active memory. Your name cookie remains **only if you opted in**. Access requires a private QR each session even if you remember the name.

## Voice topology and important limits

- Signaling, presence, room membership and messages run through the Ubuntu-hosted server over HTTPS/WSS. **There is no persistent message database and no message logging in the app.** The server sees each message in memory while relaying it, as do Cloudflare TLS endpoints. **Chat messages are not end-to-end encrypted.**
- WebRTC audio uses DTLS-SRTP between browser peers. Audio does **not** get saved, mixed or routed through FACO's Python HTTP server. Depending on network conditions, some peers need a separately configured TURN relay, which transports encrypted packets.
- **Mesh topology:** with N participants in one group, each browser talks to N-1 others; there are N×(N−1)/2 browser connections in that call. Large groups (especially ten participants) may be demanding on phone battery, CPU and mobile bandwidth. For production-quality ten-way calling, an SFU such as LiveKit is a sensible next step.
- Calls can exist independently in different groups simultaneously. Each person can join **one voice room at a time** and is unavailable for another incoming voice invitation while busy. Existing call members can invite free participants into their group. Messaging still works while in a call.
- Keep the browser page active to receive incoming call invites. Android browser tabs closed, suspended, or on the lock screen are **not guaranteed to ring**. True push notifications require an additional native/browser push service.
- The service does **not** create accounts, recordings, persistent message history, analytics, or public-side cookies unless the user explicitly saves their name. It responds with `Cache-Control: no-store`, a no-index header and a strict content-security policy.
- **No website can guarantee zero traces:** OS/phone microphone-permission settings, browser/QR-scanner history, network metadata, screenshots, device backups and Cloudflare/provider records are out of FACO's control. QR bearer links may be captured in browser or QR-scanner history even though the page removes the hash fragment from the visible URL.
- A QR remains valid until its issuing slot is rotated or its tunnel/app restarts. Anyone who possesses the QR can sign in as that slot when nobody else is connected with it. Do not share codes publicly.

### Optional TURN setup for mobile networks

```bash
export FACO_ICE_SERVERS_JSON='[{"urls":["stun:stun.l.google.com:19302"]},{"urls":["turn:turn.example.net:3478?transport=udp","turn:turn.example.net:3478?transport=tcp"],"username":"TURN_USER","credential":"TURN_PASS"}]'
./run.sh --quick
```

TURN host, credentials and service are **not** provisioned by this package.

## FACO deployment conventions

- `install.sh` performs a FAST installation preflight and installs into the OS-standard user directory; `--check-only` is non-destructive, and interactive setup pauses for Enter before launching. `run.sh` launches directly without installing an always-on service.
- `scripts/doctor.py` validates runtime, file inventory, ports, required interface actions and the animation/reduced-motion contract on every start. Standard/full regression tests remain available via commands below.
- Reuse-scan checks the standard Linux Python environment and an explicitly selected `FACO_SHARED_ROOT` runtime before downloading. No workstation-specific mount is required.
- Runtime tunnel diagnostics go under `~/.local/state/faco-crumble/tunnel.log` (or `XDG_STATE_HOME`). The phone interface itself has **no call transcript/recording or message persistence**.
- The Ubuntu control panel itself remains on `127.0.0.1:8788`, separate from the public call service at `127.0.0.1:8787`. Do not expose the admin port through Cloudflare.

## Testing & readiness

```bash
./install.sh --check-only
python3 -m unittest discover -s tests -v
node tests/test_client_mock.cjs
node tests/test_admin_mock.cjs
python3 -m unittest tests.test_facoux_optional -v    # Optional Chromium + Playwright visual regression
```

Tests cover the new live infinity animation, name-first splash, FACO Options/Doctor controls, focus and reduced-motion settings, responsive mobile tabs and leave cleanup, along with ten authenticated participants, multiple independent voice rooms, adding people, group chat inside/outside calls, private chat, role/signaling authentication, name validation, rate limiting, credential rotation, origin/admin protection, two full client mock suites, actual Chromium mobile/desktop DOM layouts, QR image decode to exact private URLs, and actual Ubuntu `run.sh --local` restart with refreshed credentials.

**Honest verification boundary:** All these server, simulated-client, QR, offline browser and launcher tests run in the build environment. Actual Android-to-Android WebRTC audio, a **real** Cloudflare connection from your Ubuntu machine and 10-way mobile performance are **not yet verified**. This is a feature-complete installable browser-app candidate, not a guarantee of production-grade audio reliability.
