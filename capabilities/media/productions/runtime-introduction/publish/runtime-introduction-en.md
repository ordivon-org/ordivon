# Ordivon Runtime — keep the work when the response disappears

**An archival, evidence-bound technical introduction.** The demonstration and source binding date to August 2026; this release is a historical explanation, not a live status page.

Agent software can propose commands, but a lost API response does not tell a client whether work started, finished, or failed. Blind redispatch can repeat effects, erase context, or strand work without observable evidence.

**Ordivon Runtime owns the physical execution boundary.** An operation is bound to a selected Git Workspace, given a durable Job identity and an observed Attempt, and exposes bounded execution evidence. After uncertain delivery, a client can reconnect with the same request identity and inspect the recorded Job rather than automatically starting a new one.

## The 78-second demonstration

| Time | What happens | What the audience should learn |
| --- | --- | --- |
| 00:00–00:06 | A missing response | Silence is not proof of a failed operation |
| 00:06–00:13 | Runtime workflow | Source, Workspace, Job, Attempt, evidence and recovery have different roles |
| 00:13–00:24 | Exact revision and guarded Patch | Change only the source state actually read |
| 00:24–00:37 | Recorded Job and observed Attempt | Supervised execution remains inspectable |
| 00:37–00:48 | Reconnect and exact replay | Recover the same Job identity |
| 00:48–00:59 | Bounded terminal evidence | Physical execution success is not semantic completion |
| 00:59–01:07 | One-path diff and compare-and-close | Only close the exact Workspace state reviewed |
| 01:07–01:18 | Explicit limitations | Do not mistake local execution guarantees for universal external-effect idempotency |

The footage is a deterministic **receipt-derived explanation**, not an impersonated live terminal recording. All claims are bound to a historical Runtime revision.

## The deliverables

- 78-second English film with narration and separate WebVTT/SRT captions, 1920 × 1080, H.264/AAC.
- 35-second 1080 × 1920 excerpt with synchronized English narration and Chinese on-screen explanations.
- Interactive HTML walk-through, readable from a standalone local file without any external scripts.
- Downloadable portfolio package containing the complete set, source context, and SHA-256 manifest.

## Crucial limits

The historic demonstration concerns owner-trusted local execution. It does **not** prove hostile-code isolation, semantic task completion, distributed scheduling, or exactly-once effects against arbitrary external systems. An identified Job cannot by itself guarantee that a financial transfer or other third-party effect is safe to repeat.

**Source:** Ordivon canonical monorepo, and historical Runtime binding from repository zycxfyh/ordivon-runtime at revision 5dd206c74a2b9151fb0a87579ba2200aaf892633.

**What is verified:** artifact bytes, full decoding, subtitle timing, and publication access are technical facts. No claim of human comprehension, popularity, voice preference or commercial effectiveness follows from those tests.
