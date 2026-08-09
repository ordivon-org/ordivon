# Runtime Introduction — production cognition

Status: active production decision record  
Protocol: [`../../research/expression/protocol.md`](../../research/expression/protocol.md)  
Profiles: [`motion-video`](../../research/expression/profiles/motion-video.md) + [`writing`](../../research/expression/profiles/writing.md)

This file records the **current creative judgment needed to continue the work**. It is deliberately not a second Production manifest, Claim set, Asset inventory, Timeline, or evidence store. When a physical or factual value differs, the owning source wins.

## FRAME

**Target experience.** A technically literate viewer should leave with a concrete model of why reliable Agent execution requires durable operation identity and recoverable evidence after uncertain delivery, rather than thinking Runtime is merely a command runner.

**Primary proof.** Use one complete trajectory already defined in [`plan.md`](plan.md#the-one-proof): exact source → guarded Patch → durable Job → recover the same Job → inspect evidence/diff → compare-and-close the reviewed Workspace state.

**Audience.** The canonical audience list remains in [`production.json`](production.json). The first film favors the shared need among those audiences: understand one real failure boundary quickly, then see executable proof rather than a feature catalogue.

**Non-goals.** Do not turn the first film into a Runtime feature montage, generic Agent-platform overview, security sandbox claim, or universal idempotency claim. The specific excluded claims remain authoritative in [`claims.json`](claims.json) and [`plan.md`](plan.md#what-the-first-film-should-not-show).

**Why this production still warrants work.** The proof substrate exists, but the public outputs in `production.json` remain `planned`; the current assembly still contains editorial placeholders that must be replaced or deliberately resolved before promotion.

## BIND

**Fact authority.** [`production.json`](production.json) owns the exact `runtime` source binding. [`claims.json`](claims.json) owns what the production may say about that binding and which implications must be avoided. [`evidence/runtime-demo.receipt.json`](evidence/runtime-demo.receipt.json) owns the selected executable proof identities and dispositions.

**Focalization.** Present the work from the position of an external technical observer who is allowed to see the selected demonstration, receipt-derived proof events, source effect, and declared Runtime boundaries. The work is not entitled to private host state, unrelated Runtime history, bearer material, or stronger claims than the selected evidence supports.

**Semantic boundary.** `avoid` entries in `claims.json` are **must-not-imply constraints, not banned words**. Boundary language may need to name a false interpretation in order to negate it explicitly. A lexical match therefore cannot by itself establish a violation.

**Promotion freshness.** The bound Runtime revision is intentionally frozen production evidence. Before any output is promoted as a statement about *current* Runtime capability, current Runtime authority must be rechecked and any drift classified as compatible, requiring revision, or historical framing.

## EXPRESS

This production composes two current medium profiles:

```text
Writing Profile
argument / narration / claim order / verbal boundaries
        +
Motion / Video Profile
sequence / duration / reveal / motion / image / eventual sound
        ↓
one technical film and its related written material
```

**Film strategy.** Preserve the [`plan.md`](plan.md#film-structure) 78-second master as the current editorial hypothesis. Real product capture should carry the core executable proof. Programmatic motion may establish the problem, explain durable relations, stage exact replay/close concepts, and present boundaries, but must not impersonate the real terminal demonstration.

**Writing strategy.** Lead with the execution/recovery problem before Runtime vocabulary; keep the core boundary adjacent to the proof; distinguish admitted-operation identity from semantic Task success and external-world idempotency. [`story.mdx`](story.mdx) and narration files remain editable sources, not published authority.

**Distribution labels are not yet durable profiles.** `youtube-upwork-1080p`, `douyin-1080x1920`, `web-en`, and `upwork-portfolio` in `production.json` identify intended outputs. Their platform-specific conventions remain context/encounter work until real delivery pressure earns a profile.

## RENDER

The current real artifact boundary is distributed across existing production sources:

- [`assets.json`](assets.json) owns selected rendered and placeholder media byte identities;
- the three Runtime Remotion compositions referenced by `production.json` are deterministic editable motion sources;
- [`timeline/assembly.v0.otio`](timeline/assembly.v0.otio) is the canonical assembly review skeleton;
- Resolve native conform evidence is retained under `docs/resolve-compatibility/` and proves the current workstation's accepted assembly mechanism;
- [`evidence/runtime-demo.receipt.json`](evidence/runtime-demo.receipt.json) is executable source evidence, not a visual render;
- delivery Outputs remain unpromoted in `production.json`.

Current physical inventory must be read from those sources rather than copied here. At the time of this C3 audit, the inventory contains real rendered motion **and** deliberate editorial placeholders; therefore a successful technical conform is not equivalent to a finished film.

For expressive judgment, inspect motion over time. A valid frame, OTIO layout, digest, or ffprobe result proves only its own technical fact.

## AUDIT

### Current findings

1. **Production-state prose had drifted from physical truth.** `README.md` still described `assets.json` as empty and OTIO as future work although selected Assets and the assembly already exist. C3 corrects that entry document rather than creating a second asset count here.
2. **Must-not-imply is semantic, not lexical.** The automated audit found exact `avoid` phrases in `plan.md` and narration because they are used in explicit negations. A banned-phrase validator would therefore reject correct boundary communication.
3. **Placeholder visibility is the main current semantic risk.** Placeholder clips are valid assembly artifacts but must not be mistaken for recorded Runtime evidence or a publication-ready output.
4. **Programmatic motion must remain explanatory.** It may express uncertain delivery, identity continuity, and exact close, but must not fabricate the core real demonstration.
5. **No population-level aesthetic claim is needed at this stage.** The unresolved work is capture replacement, playback/semantic inspection, narration lock, and actual delivery composition. Human calibration should be requested only if a consequential human-response uncertainty survives those steps.
6. **C4 tightened the replay wording at the actual render source.** `runtime-request-replay` now says “Exact replay returns the recorded Job. It does not admit a second Job.” This keeps the claim at Runtime admission identity instead of inviting a broader external-effect interpretation.
7. **The first fast-loop attempt exposed a network-dependent renderer prerequisite.** Remotion attempted browser acquisition when no local executable was declared. The supported configuration is now local-browser-first and fails closed unless browser download is explicitly allowed.
8. **The second attempt exposed a generated-source prerequisite.** A fresh Workspace could not resolve `@ordivon/identity/tokens.css`; supported motion entrypoints now build tokens before render instead of relying on Agent memory.
9. **The third attempt completed a real local render/review pass.** The 180-frame replay composition rendered, passed the then-observed structural video QC, and produced exact keyframe/source evidence in a disposable review packet. The packet intentionally leaves semantic audit pending rather than promoting technical correctness into expressive correctness.
10. **A repeated pass exposed H.264 signalling drift.** Raw Remotion output retained BT.709 matrix/range but could omit transfer/primaries. The supported render entrypoint now normalizes H.264 VUI by stream copy before QC. Two consecutive complete loops then produced identical final MP4/keyframe digests and passed complete BT.709 checks.

### Audit routing

```text
wrong Runtime claim / currentness → BIND
wrong proof or audience target    → FRAME
misleading sequence / language    → EXPRESS
bad capture / render / timing      → RENDER
```

## DECIDE

**Current decision: `revise`.** Continue the existing production through the concrete gate below; no public Output is ready to promote and no architectural redesign is justified.

The next gate is concrete:

1. replace the real-evidence placeholders with selected capture derived from a Receipt-valid demonstration;
2. visually/playback-audit the complete 78-second sequence for readability, temporal implication, and source/animation distinction;
3. lock the narration/timing only after it still matches the rendered proof;
4. run technical QC on the actual master;
5. recheck Runtime current authority before deciding whether the film is current capability, historically bound proof, or requires factual revision;
6. then choose `revise`, `no-op`, or `promote` for the intended outputs.

The assembly skeleton, Resolve adapter, and Production schema are already adequate for this gate. Do not add a creative workflow engine or approval state machine.

## LEARNING

Retain these findings at the narrowest current scope:

- **production-local:** a thin cognition record is useful because the existing physical/factual authorities are sufficient but the current creative decision was scattered across them;
- **production-local:** source/asset/timeline state should be referenced, not duplicated into cognition, because physical production can outrun descriptive prose;
- **candidate Writing/Profile observation:** must-not-imply constraints cannot safely be implemented as lexical bans because explicit negation often needs the same vocabulary;
- **candidate production-system observation:** one artifact can compose multiple medium profiles without merging their authorities;
- **production-local C4 observation:** deterministic render prerequisites should be self-satisfied or fail fast; hidden setup and network acquisition directly reduce Agent inner-loop frequency;
- **production-local C4 observation:** a disposable review packet can combine artifact identity, technical QC, source digests, and exact review frames without becoming a second Production authority;
- **Motion/technical-baseline observation:** renderer color intent is not sufficient evidence of complete encoded VUI metadata; supported output should be normalized/verified at the byte boundary before downstream editorial use;
- **no new Art & Expression Core prior promoted by C3/C4.** These production-system findings do not constitute a universal aesthetic law.

If later unrelated productions repeatedly need the same record fields, promote only those repeated semantics into a stronger machine schema. Until then, this Markdown record plus the existing Production source pointer is sufficient.
