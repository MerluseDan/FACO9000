# FACO Crumble v0.5.1 | Linux Standard Install + GitHub Distribution

- Installs by default to `~/.local/share/faco-crumble/app/` (XDG_DATA_HOME).
- Adds an executable `~/.local/bin/faco-crumble` and desktop entry.
- Settings, cache, runtime, and logs now use Linux-standard XDG paths rather than the source folder or a private `/media/owner` mount.
- Explicit custom install directory supported; missing custom mount offers **Use OS Default Location** or **Cancel Installation**, never silently falls back.
- Reuses existing Linux Python dependencies or a separately configured shared FACO environment; does not require a FACO drive.
- Includes an actual install/upgrade smoke test from a fresh disposable home and custom drive failure testing.
- The GitHub source archive includes **source and tests, never generated QR credentials, persisted names, or local admin tokens**.
- No changes to the v0.5.0 WebRTC signaling/chat/visual runtime beyond update/version and log path.

## Previous v0.5.0 changes

# FACO Crumble v0.5.0 | Cloudlight Electric Infinity

## Cumulative release based on v0.4.0

### Brand & UI

- Replaced placeholder star/lightning iconography with a new FACO infinity-ribbon identity throughout the name gate, web calling interface, Ubuntu QR control center, and favicon.
- Released editable vector logo (`assets/FACO_Crumble_Full_Logo.svg`) and a standalone animated infinity (`assets/FACO_Infinity_Active_Animation.svg`). No proprietary fonts or external asset downloads.
- Cloudlight Electric is the default: soft cloudy white surfaces, restrained electric-blue glow, clear navigation, simple main actions, useful Options panel.
- Live calling animates a bright loop tracer in the infinity icon. Ringing accelerates it, ending the call stops it. User/OS reduced-motion disables animated effects.
- Added nonblocking inline infinity progress for connection/microphone preparation. No disruptive Working overlay.
- Phone-sized interface has Calls/Messages tabs and a contextual Return to call strip. Desktop displays people, call and messages side by side.
- Rebuilt local-only Ubuntu QR dashboard with consistent brand, simplified controls and a real status/Doctor disclosure.

### FACO default app features

- Session-only Options: microphone & speaker selection (where browser supports it), microphone permission test, speaker test, Focus view, infinity-motion toggle, incoming call alert toggle, Quick Doctor, Reset/Cancel/Apply.
- Settings never persist to cookies, sessionStorage or localStorage. **Only** a participant's optional display-name cookie persists if explicitly checked.
- Programme installer Doctor supports FAST (`--check-only`), STANDARD (`--standard --check-only`) and FULL (`--full-audit --check-only`). Every run launches an independent FAST read-only preflight.
- Reuses already-installed Python dependencies in FACO shared roots, retaining legacy FACO Private Talk runtime compatibility. New application settings go under `~/.config/faco-crumble`, while existing participant-count settings are read from the previous folder if needed.
- Ubuntu admin Doctor exposes safe operational status and does not display its admin token in diagnostics.

### Cumulative features retained from v0.4.0

- Ten role-based QR invitations; cloud public landing QR does not grant sign-in.
- No privileged phone host; any online member can call any other. Browser-managed WebRTC encrypted audio with optional TURN relay.
- Independent direct and group call rooms; up to ten members, with group invitations and hold-to-talk / hands-free mode.
- Direct, current-room and everyone-online text messaging; no saved or queued server-side conversation history.
- Cookie consent default off, name-first entry and Leave & clear, invitation rotation and administrator-only localhost QR management.

### QA and restrictions

- 20 Python tests: signaling, security validation, QR decode, process launch/restart, simulated tunnel recovery, responsive Chromium web/admin layouts, mock call flow, session settings and active-call infinity animation.
- Two Node simulated app/Ubuntu-admin test suites for input, messages, calling, cookie consent, WebRTC offer/answer and QR controls.
- Validated SVG syntax, JS/Python syntax, Linux POSIX launch permissions, installer modes and manifest integrity.
- Actual two/ten-phone audio, Android speaker switching and a live Cloudflare tunnel on the owner's Ubuntu machine are **not verified in this sandbox**. TURN remains optional and may be required for restrictive mobile carrier networks.
- Browsers, QR scanners, providers and phone operating systems may independently retain metadata/history. Zero traces beyond FACO's app-level storage cannot be promised.
