# Historical cognition snapshot — through P4

> Frozen before the C1 contraction. This file preserves the full P2/P3/P4 working ledger; it is historical evidence, not the active decision frontier.

# Runtime Introduction — production cognition

Status: active production decision record
Protocol: [`../../research/expression/protocol.md`](../../research/expression/protocol.md)
Profiles: [`motion-video`](../../research/expression/profiles/motion-video.md) + [`writing`](../../research/expression/profiles/writing.md)

This file records the **current creative judgment needed to continue the work**. It is **not a second Production manifest**. Physical and factual authority remains in the Production, Claim, Asset, TimedText, Receipt, Timeline, archive, and owning Runtime sources.

## FRAME

**Target experience.** A technically literate viewer should understand one bounded proposition: after uncertain response delivery, reliable Agent execution needs durable operation identity, recoverable evidence, and an exact reviewed-state cleanup boundary. Runtime is not presented as a generic command runner or complete autonomous Agent platform.

**Primary proof.** One current live trajectory remains authoritative: exact source → guarded Patch → durable Job and recorded Attempt → observe progress → exact request replay recovers the same recorded Job → inspect bounded terminal evidence and structured diff → compare-and-close the exact reviewed Workspace state.

**Current P2 gate.** The landscape output is no longer missing audio. P2 asks a narrower question: does the exact picture+narration candidate have enough evidence to move from `rendered / review` to `approved`, or is a human-response uncertainty still material?

## BIND

**Runtime authority.** Product claims remain bound to Runtime revision `5dd206c74a2b9151fb0a87579ba2200aaf892633`. [`evidence/runtime-demo.receipt.json`](evidence/runtime-demo.receipt.json), digest `sha256:c612500db2312fc956e0b9dc801853aab3ae31f7f182f3cce6a7649c02ccdbe1`, remains the selected execution proof.

**Narration authority.** [`timed-text/narration.en.json`](timed-text/narration.en.json) owns the current nine English cue texts and timing. [`evidence/narration-sapi.receipt.json`](evidence/narration-sapi.receipt.json) records the selected workstation-local voice materialization: Windows System.Speech, `Microsoft Zira Desktop`, rate `1`, exact cue-fit measurements, repeated exact-output evidence, technical audio facts, and the explicit human-response boundary.

**Byte authority.** Selected picture, narration, and muxed candidate bytes are stored and verified in the local content-addressed cache under `/mnt/d/OrdivonStudio/cache/objects/sha256/...`. P4 additionally retains independently redownload-verified copies in the private Cloudflare R2 bucket `ordivon-artifacts`; [`evidence/r2-replica.receipt.json`](evidence/r2-replica.receipt.json) records the exact object keys and destructive local-loss restore acceptance. An Asset digest without recoverable bytes at the failure boundary being claimed is not sufficient durability evidence.

## EXPRESS

The picture still distinguishes three provenance classes:

- receipt-derived evidence views for selected Runtime proof facts;
- deterministic explanatory motion for structure/replay/close;
- Studio explanatory/current-authority framing for the hook, boundary, and end state.

P2 added real voice pressure. A first Zira `rate=1` duration scan showed that the old 68–75 second Boundary and 75–78 second End timing did not physically fit the intended natural, consistent speech rate. The production did **not** globally accelerate narration to preserve a prior timing assumption. Instead the final 19 seconds were revised to:

```text
59–67  source effect / exact reviewed-state close narration
67–74  Runtime boundary
74–78  end statement
```

The corresponding picture sequence is now 65–67 seconds Diff, 67–74 Boundary, and 74–78 End. Cue wording was narrowed rather than spoken faster.

## RENDER

Three selected exact artifacts now exist and are archived:

1. **Picture master** `runtime-introduction-master-motion`
   - Blob `sha256:77d8eae832a3cac47c641211aa8c9019c04c542faf0ae87a9ae0e82d37acc736`
   - 2,326,600 bytes
   - 78.000 seconds / 2,340 frames
   - 1920×1080, 30 fps, H.264, `yuv420p`, complete BT.709
   - archive key `objects/sha256/77/77d8eae832a3cac47c641211aa8c9019c04c542faf0ae87a9ae0e82d37acc736`

2. **English narration stem** `runtime-introduction-narration-en-sapi`
   - Blob `sha256:798c8f90f9eeb90d6407d78329e88e71dab6d4aa5d38831568c7e14f445d828d`
   - 11,232,102 bytes
   - exactly 78.000 seconds
   - 48 kHz, mono, PCM 24-bit
   - integrated loudness `-20.5 LUFS`, true peak `-2.2 dBFS`
   - two independent complete builds produced byte-identical output
   - archive key `objects/sha256/79/798c8f90f9eeb90d6407d78329e88e71dab6d4aa5d38831568c7e14f445d828d`

3. **English A/V review candidate** `runtime-introduction-en-av-candidate`
   - Blob `sha256:7d994f80627968f4e64a3a53c08d5241bb8f398e17d52c24080f935e7c716430`
   - 3,369,776 bytes
   - exactly 78.000 seconds
   - picture stream copied without re-encoding; AAC 48 kHz mono narration
   - two independent muxes produced byte-identical output
   - archive key `objects/sha256/7d/7d994f80627968f4e64a3a53c08d5241bb8f398e17d52c24080f935e7c716430`

[`timeline/assembly.v2.otio`](timeline/assembly.v2.otio) is the active A/V review snapshot. v1 remains the prior picture-only milestone; v0 remains historical placeholder assembly evidence.

## AUDIT

### P2 findings

1. **Asset identity was not byte durability.** P1 registered the old picture digest but closed its disposable Workspace before those bytes were copied into any durable local object store. P2 proved the exact old Blob was absent from the documented cache locations. The new `ordivon-studio archive` gate now performs content-addressed copy, temporary-copy verification, no-overwrite admission, exact final rehash, and idempotent reuse.
2. **Voice materialization falsified part of the previous timing lock.** Zira rate `1` was exact-byte repeatable, but the old Boundary/End slots were physically too short. Audio therefore revised picture timing rather than being forced into the prior edit.
3. **Every selected narration cue now fits its assigned slot.** Voice durations are recorded in the narration Receipt; the tightest cue is the 7-second Boundary at `6.927937s`.
4. **Picture+audio mux is mechanically stable.** Two independent muxes produced the same exact MP4 digest. Video QC passes with one audio stream; final audio is 48 kHz mono AAC and retains the source stem's measured `-20.5 LUFS` integrated loudness and `-2.2 dBFS` true peak.
5. **Cue-bound visual inspection is semantically aligned.** Review frames sampled from the actual narration phases show source/Patch, Job observation, recovery, evidence, close, boundary, and end imagery in the same semantic order as the voice cues. A focused 65–78 second review confirms Diff → Boundary → End cut order under the revised timing.
6. **Human voice quality is still genuinely unresolved.** The available Agent surface can inspect exact audio bytes, timing, levels, generation provenance, and corresponding picture states, but it cannot honestly establish whether the synthetic voice sounds natural, appropriately paced, or publication-worthy to a human listener. No such claim is inferred from waveform or metadata.

### P3 findings

1. **Durability survived the disposable-Workspace boundary.** The P2 Workspace and its render paths were absent in a fresh P3 Workspace, while the committed final Output digest still resolved to the exact 3,369,776-byte cache object and retained the expected 78-second H.264 + AAC structure.
2. **Write-only durability was still Agent-hostile.** Before P3, recovery required manually reconstructing `objects/sha256/<prefix>/<digest>` from the digest and copying bytes by hand. `ordivon-studio materialize` now provides the inverse verified primitive: verify cached object → temporary copy → verify working copy → no-overwrite admission. Repeating exact recovery converges; different destination bytes and corrupt cache bytes fail closed.
3. **The human-review model did not require a new approval system.** `Production=review` plus `Output=rendered` already expresses the unresolved auditory claim. The generic Receipt envelope can hold a future actual calibration result by kind, but P3 deliberately does not create a pending human Receipt before a person has supplied a judgment.
4. **The durability rule does not imply universal CAS.** Browser Perception Note provides the materially different falsifier: its approved article Output digest exactly equals the Git-tracked `story.mdx` bytes and the same bytes recovered through `git show HEAD:<path>`, while no media-cache object exists. Git is already the durable byte authority for that exact text artifact.
5. **The exact audition object is now independently materialized for human use.** The current candidate digest is present at `D:\OrdivonStudio\productions\runtime-introduction\review\runtime-introduction-en-7d994f806279.mp4`; this working copy is recoverable evidence, not an approval claim.

### P4 findings

1. **Local CAS was still one failure domain.** P3 proved recovery after Workspace loss, but the selected media still depended on the workstation/D: volume. P4 therefore tested the stronger claim rather than relabeling local storage as redundancy.
2. **A real private R2 replica now exists.** The selected picture master, narration stem, and final A/V candidate were copied into the existing private `ordivon-artifacts` bucket under their exact `objects/sha256/...` keys. `r2.dev` was disabled and no custom domain was attached during acceptance. Every object was independently downloaded and SHA-256 verified.
3. **Destructive local-loss restore is proven through the productized path.** The picture-master CAS object was quarantined, ordinary local `materialize` failed, then `ordivon-studio r2 restore` reconstructed the local CAS object from R2 alone. The restored CAS and working MP4 both matched `sha256:77d8ea…` and the 78-second H.264 BT.709 structure remained intact.
4. **Remote replication justified a provider adapter, not a storage platform.** Hand-written curl was real operational friction only after the destructive experiment succeeded. Studio now exposes the narrow `r2 replicate/restore` pair while Blob/Production identity remains provider-independent.
5. **The exercised Account Object API is not an atomic multi-writer admission boundary.** Sending `If-None-Match: *` while PUTting an already-existing exact object returned HTTP 200. The accepted adapter is therefore explicitly single-writer: preflight GET, PUT only when absent, then mandatory redownload/hash verification. Concurrent create-only semantics remain unproven.
6. **Off-machine durability does not change the creative decision.** Storage recovery evidence closes a different failure class; it provides no evidence about whether Zira sounds natural or publication-worthy.

### Audit routing

```text
wrong Runtime fact/currentness      → BIND
wrong claim / narration meaning     → FRAME or EXPRESS
cue overflow / bad cut / bad level  → RENDER
voice naturalness / human response  → conditional human audition
```

## DECIDE

**Current decision for `runtime-film-en-landscape`: keep `rendered / review`; do not promote to `approved` or `published`.**

This is materially stronger than P1. The current output digest now identifies a complete, recoverable picture+narration candidate rather than a silent picture master. Selected picture, narration stem, and final mux are archived locally by exact digest and independently redownload-verified from private R2; destructive local-CAS-loss restore is proven for the picture master. Cue fit, A/V structure, color/video facts, audio stream facts, loudness/peak, and deterministic rebuild/mux behavior are also established.

Promotion is withheld for one precise reason only: the remaining uncertainty is a real **human auditory-response claim** about the selected synthetic voice. Static pixels, hashes, ffprobe, loudness analysis, and knowledge of the input text do not prove that claim. P3 has already materialized the exact candidate at `D:\OrdivonStudio\productions\runtime-introduction\review\runtime-introduction-en-7d994f806279.mp4`; the next gate is therefore a bounded human audition of **that exact digest**, not another Studio architecture project. No human-review Receipt exists until an actual judgment is supplied.

## LEARNING

Retain the P2/P3/P4 learning at the narrowest justified scope:

- **production-system, promoted and narrowed by cross-medium falsification:** a digest identifies selected bytes but does not establish recoverability. Selected payloads need an exact durable byte authority appropriate to their medium: verified CAS for large/binary media intentionally outside Git, while exact Git-tracked text/code may use Git itself. For CAS-backed media, the durability boundary must support verified recovery as well as archive;
- **production-system, promoted by destructive failure testing:** local CAS proves Workspace/process recovery but not workstation/volume-loss tolerance. When that stronger failure boundary matters, selected bytes outside Git need at least one independently verified replica and a proven restore from that replica after the local object is unavailable;
- **provider-local:** the accepted Cloudflare Account Object API adapter is a single-writer verified replica path, not an atomic multi-writer content store. Do not generalize its preflight/PUT/redownload protocol into a universal storage law;
- **production-system:** media-specific materialization may legitimately revise a previously locked abstract timing plan. “Locked text/timing” means the current editorial decision, not immunity from physical evidence produced by the medium itself;
- **production-local:** Windows System.Speech / Zira rate `1` is an exact-byte-repeatable local candidate generator on this workstation. That does not make it a universal Studio voice provider or quality default;
- **Motion/Audio:** cue-bound temporal sampling can establish semantic ordering and slot fit, but it does not establish voice naturalness or audience preference;
- **no new aesthetic Core law is promoted.** The P2 structural gains concern byte durability and evidence boundaries, not a universal style or voice prior.
