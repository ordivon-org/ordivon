# Runtime introduction

This is the first real Ordivon Studio motion production and the primary acceptance case for source-bound multi-medium production.

## Bound source

Runtime facts remain bound in `production.json` to:

```text
ordivon-runtime
5dd206c74a2b9151fb0a87579ba2200aaf892633
```

`claims.json` limits what Studio may say. Studio never becomes a second Runtime authority.

## Current production sources

- [`cognition.md`](cognition.md) — current FRAME/BIND/EXPRESS/RENDER/AUDIT/DECIDE/LEARNING judgment;
- [`plan.md`](plan.md) — current proof and A/V construction;
- `claims.json` — bounded Runtime claims;
- `timed-text/narration.en.json` — nine locked English voice cues covering exactly 0–78 seconds;
- `evidence/runtime-demo.receipt.json` — selected current live MCP proof;
- `evidence/narration-sapi.receipt.json` — exact local narration generation, cue-fit, repeatability, audio facts, archive identity, and human-response boundary;
- `assets.json` — selected picture, narration, A/V candidate and historical media identities;
- `timeline/assembly.v2.otio` — active picture+narration review snapshot;
- `timeline/assembly.v1.otio` — previous picture-only milestone;
- `timeline/assembly.v0.otio` — historical placeholder skeleton;
- `../../apps/motion-remotion/` — deterministic picture source;
- `../../scripts/build_sapi_narration.py` + `../../scripts/synthesize-sapi-cues.ps1` — workstation-local narration adapter.

## Proof shown

```text
exact source
→ guarded Patch
→ durable Job + recorded Attempt
→ observe bounded progress
→ replay exact request identity and recover the same recorded Job
→ inspect bounded evidence and one-path diff
→ compare-and-close the exact reviewed Workspace state
```

The film does not claim universal external-effect idempotency, semantic Task completion, or hostile multi-tenant isolation.

## Current selected bytes

All three current selected artifacts are now copied to and reverified from the local content-addressed cache under `D:\OrdivonStudio\cache\objects\sha256\...`.

```text
Picture master
sha256:77d8eae832a3cac47c641211aa8c9019c04c542faf0ae87a9ae0e82d37acc736
78.000 s · 2340 frames · 1920×1080 · 30 fps · H.264/yuv420p · complete BT.709

English narration stem
sha256:798c8f90f9eeb90d6407d78329e88e71dab6d4aa5d38831568c7e14f445d828d
78.000 s · 48 kHz · mono · PCM 24-bit · -20.5 LUFS · -2.2 dBFS true peak

English A/V review candidate
sha256:7d994f80627968f4e64a3a53c08d5241bb8f398e17d52c24080f935e7c716430
78.000 s · picture stream copied · AAC 48 kHz mono
```

The narration stem was independently built twice with exact-byte equality. The final mux was also independently produced twice with exact-byte equality.

## What P2 changed

Voice materialization was allowed to challenge the edit. At the selected Zira rate `1`, the old 68–75 second Boundary and 75–78 second End slots did not fit. Rather than globally speed the voice up, the final tail was revised to 59–67 / 67–74 / 74–78 narration timing and 65–67 / 67–74 / 74–78 picture phases for Diff / Boundary / End.

P2 also found that P1 had committed the picture Asset digest without moving the selected bytes into durable storage before its Workspace closed. `ordivon-studio archive` now provides the minimum verified local content-addressed durability gate.

## Current output decision

`runtime-film-en-landscape` remains **`rendered / review`**, not approved or published. The current Output digest now points to a complete, archived picture+narration candidate rather than a silent picture.

Machine evidence now covers source/claim binding, exact selected bytes, archive recoverability, cue fit, picture sequence semantics, video/color structure, audio stream structure, loudness/peak, and deterministic local rebuild/mux behavior.

One material uncertainty remains: whether the selected synthetic voice is natural and publication-worthy to a human listener. The current Agent surface cannot truthfully establish that auditory-response claim. The next gate is therefore a bounded audition of this exact candidate Blob—not another architecture cycle.
