# Experimental local Jellyfin bridge

The add-on can expose a local M3U playlist while Kodi is running. It reuses the existing manually supplied Tipsport session and does not initiate browser login or forward that session to Jellyfin.

## Setup

1. Start Kodi with the Tipsport add-on enabled and supply a working session through its existing local form.
2. Add an M3U tuner in Jellyfin, on the same Windows machine, using `http://127.0.0.1:8089/jellyfin/channels.m3u`.
3. Set the simultaneous stream limit to 1 and enable Allow stream sharing. Keep port 8089 restricted to loopback; do not expose the bridge on the network.
4. Open Live TV / Channels in Jellyfin.

The playlist contains a Kometa channel, which chooses only a currently live match whose name contains Kometa, plus an ATP-preferred live tennis test channel. An offline Kometa channel fails explicitly rather than selecting another match. This is a small personal integration, not a complete sports catalogue or EPG.

## Runtime and limitations

- Kodi must remain running. No automatic startup task is installed by this change.
- A valid session and the provider's ordinary viewing eligibility are required. If the session expires, renew it manually through the add-on. No eligibility, regional or DRM restrictions are bypassed.
- The playlist exposes `.ts` byte streams so Jellyfin uses its SharedHttpStream path rather than opening the provider HLS URL for each viewer. The bridge reserves one acquisition at a time, uses the existing Jellyfin FFmpeg at `C:\Program Files\Jellyfin\Server\ffmpeg.exe` to remux with codec copy, and rejects an independent second input. Jellyfin fans that local byte stream out to viewers. No video re-encoding is performed by the bridge. Only existing direct, IMG and TVCOM formats are supported; unfamiliar URL types fail closed.
- Requests are bounded by timeouts. Browser cookies and provider response bodies are not included in bridge errors.
- The optional login-duration endpoint can fail without preventing the program request, matching the existing add-on's behavior.
- Provider changes can break this unofficial integration.

## Validation

Eleven isolated bridge unit tests cover request headers/method, channel selection, offline behavior, supported URL resolution, single-input reservation and disconnect cleanup: `python -m unittest discover -s tests -v`.

A live ATP tennis stream was verified end to end in Jellyfin Web on Windows on 2026-11-01 (960 x 540 video). Old failed tuner sessions required a Jellyfin restart before the clean test. Actual Kometa playback has not yet been verified.

The shared MPEG-TS implementation was verified on 2026-11-01 with Jellyfin Web and Samsung Tizen playing simultaneously. The server reported three consumers of the same SharedHttpStream while the bridge acquisition count remained one. The test used the existing nunak account; separate-account access still depends on each user having Live TV permission. The local `/jellyfin/status` page reports only active/channel/acquisition count, never credentials or media URLs.
