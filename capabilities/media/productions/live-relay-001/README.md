# Live Relay 001 — Archive / Object / Constellation

`Live Relay 001` is Ordivon's first retained Broadcast Work: a real OBS episode rather than an offline slideshow pretending to be live media.

The programme starts on a minimal `LIVE RELAY 001` signal, then switches live through three exact registered Works — **Archive Archipelago 001**, **CONVERGENCE OBJECT 001**, and **System Constellation Poster 001** — before returning to signal. After independent Broadcast peer review, the final rhythm was revised from equal interior holds to approximately 3s SIGNAL → 6s ARCHIVE → 4s OBJECT → 6s CONSTELLATION → 3s SIGNAL so denser works receive more reading time without adding effects. The programme rail deliberately preserves the source boundaries: the Archive remains conceptual cartography, the Object remains a registered render, and the Constellation remains composition-only rather than geography, hierarchy or runtime dependency.

## Why silent?

The first broadcast isolates the new medium: live scene/state orchestration. Both observable OBS audio inputs were temporarily muted for the episode, then restored and re-read. The complete AAC stream in the retained source capture measures digital silence (`-inf` peak and RMS). This is a privacy/scope decision, not a permanent aesthetic rule.

## Carrier roles

- `render/live-relay-001-source.mp4` — the real OBS H.264/AAC event-source and convenient replay carrier.
- `render/live-relay-001-master.mkv` — video-only Matroska v4 / FFV1 3.4 preservation/interchange derivative under Artifact profile `moving-image-matroska-ffv1-v3-r1`.
- `render/live-relay-001-poster.png` — dedicated whole-program hero assembled only from five frames decoded from the actual final recording; no reused child still is allowed to impersonate the Broadcast Work.

The preservation master is not merely decodable: the existing Artifact verifier reports PASS with 718 Matroska implementation checks, zero failures/warnings, MediaInfo/FFprobe agreement, and exact decoded rawvideo identity. The master decoded to `yuv422p` is byte-identical to the final OBS source capture decoded through the same normalization.

## Recovery is part of the medium

Earlier takes exposed three real control-plane frictions: persistent state was initially modified before the recovery domain; PowerShell pipeline-unrolled `ArraySegment<byte>` values used by `ClientWebSocket`; and OBS record-stop state converged asynchronously rather than in 500 ms. A fourth false negative came from a polarity-insensitive final cleanup gate. These are retained as friction evidence rather than hidden.

The final episode authenticates locally to obs-websocket, fences audio inputs, creates four temporary scenes, records and switches the programme, waits for record-stop convergence, restores the original program scene and input mute states, removes the temporary scenes, closes OBS through normal GUI `WM_CLOSE`, restores four OBS state files byte-for-byte, and leaves no process or 4455 listener.

## Non-claims

This Work does **not** claim public streaming, audience reach, 24/7 broadcast stability, universal OBS lifecycle closure, or current-system authority for any source artwork.
