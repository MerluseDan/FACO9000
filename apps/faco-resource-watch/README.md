# FACO Resource Watch

**Standalone, free Linux resource monitor.** This directory is the FACO9000 staging location for the public standalone distribution.

## Functionality

- GNOME top-panel readout for CPU, RAM, GPU/VRAM and thermal sensors.
- Click-through local dashboard with historical charts.
- Separate CPU, RAM, GPU, VRAM, thermal, encoder and decoder views.
- Linux process snapshots and NVIDIA process telemetry when supported.
- Sampling and history at 1s, 1m, 30m, 1h, 6h, 24h and 7d.
- Persistent local SQLite history; background user systemd service.
- Standard Linux/XDG defaults; never depends on developer-specific removable drives.

## Deployment

**Release under review:** v1.0.3

The public standalone repository is intended to be `MerluseDan/FACO-Resource-Watch`. This existing FACO9000 repository is private and is **not** the public standalone distribution. The source package is being verified separately before public release.

Normal public installation target:
`~/.local/share/faco-resource-watch/app`

Historical data:
`~/.local/share/faco-resource-watch/data/history.sqlite3`

Configuration:
`~/.config/faco-resource-watch/`

A default Linux path is mandatory. An external drive is allowed only as an explicitly chosen custom path, never as the default. Preserve historical data on upgrades.

## Status

The user has reported a failure with the v1.0.3 release/publishing workflow. Do not advertise this staged directory as a working public release before the problem is resolved and host verification is performed.

Copyright (c) FACO contributors. MIT licensed where source files specify.
