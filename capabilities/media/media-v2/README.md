# Media v2 — external-first substrate

Media v2 is intentionally **not** a new media engine. It is a thin control/evidence plane over mature external media tools.

## R1 rule

The R1 AV path must not import or call `ordivon_studio.assets`, `ordivon_studio.qc`, `ordivon_studio.video`, `ordivon_studio.perception`, or `ordivon_studio.rich_perception`.

The first slice delegates media inspection to FFprobe, keeps the raw machine output as evidence, evaluates only an explicit output profile, and emits a small digest-bound evidence receipt. Mechanical acceptance must not be promoted to semantic, aesthetic, rights, accessibility, review, publication, or destination truth.

## Run

```bash
bash media-v2/tests/smoke.sh
bash media-v2/bin/probe-av.sh <artifact.mp4> media-v2/profiles/av-sdr-web-1080p30-noaudio.json <evidence-dir>
```

## Planned external replacements

- MediaInfo: second independent technical metadata source.
- VMAF / QCTools: perceptual/signal QC where a comparison or signal profile actually requires it.
- OpenTimelineIO: canonical editorial interchange; custom NLE code only for proven private deltas.
- IMSC/TTML/WebVTT tooling: timed-text interchange and conformance.
- DVC: working large-asset versioning when needed.
- ORAS/OCI: immutable release packages when needed.
- xSTUDIO/OpenRV/Kitsu: review surfaces; Media retains only digest-bound ReviewDecision evidence.
- provider-native APIs/OpenAPI clients: distribution capability and effects; no static provider-policy database in Media.

R1 intentionally does not install every candidate dependency. New dependencies require a concrete consumer/falsifier.
