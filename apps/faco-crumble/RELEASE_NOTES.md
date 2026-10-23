# FACO Crumble Desktop v0.6.2

- Ported v0.6.1 video-enabled Android browser client to Linux/Windows/macOS standalone desktop host.
- Added room-scoped `video` status and late-join camera state in Python signaling backend.
- Enabled opt-in camera use in browser Permissions-Policy. Rejected forged room / outsider video status updates.
- Reused existing QR invitation admin screen, ephemeral sessions, per-identity credentials, direct/group calls, chat, audio/PTT, animated FACO infinity and audio Options.
- Added cross-platform configuration/log directories, browser-open logic and Cloudflare client detection for Windows and macOS.
- Added CI-native executable packing and service smoke tests. Android remains an optional separate host implementation.
- macOS and Windows native packages are unsigned test builds; real network/device behavior is not yet certified.
- Corrected Intel macOS packaging to use `macos-15-intel`, x64 Python and an explicit PyInstaller `x86_64` target; verify host/Python and bundled executable architecture before publishing. Earlier `macos-14` artifacts mislabeled as Intel are ARM64 and are not valid Intel releases. Native execution of the corrected configuration must be confirmed in the Actions run for its commit.
