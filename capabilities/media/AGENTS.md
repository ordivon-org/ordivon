# Ordivon Media — Agent entry

Scope: `capabilities/media/`. Inherit the monorepo `AGENTS.md`; follow this Owner's actual source and interfaces. Media owns medium-specific projection and Studio creative/technical semantics. It **does not** own Runtime Jobs, Workstation installations, source facts, Artifact bytes, external publication or human preference.

## Start from the consumer, not the tool

1. Name the final consumer, source revision/SourceCut, intended audience and what outcome needs to change. Decide if this is an ordinary source-native projection or an authored Media responsibility. If Media adds no needed semantic transformation, stop and use the source Owner directly.
2. If Studio work is needed, discover the current action schema with `python3 scripts/studio-agent-surface.py` from this directory. This imports only `agent_surface_contracts.py` (the one authoritative schema), not the implementation adapters; it needs no `.venv` or `node_modules`. Import the `agent_surface.py` executor only after a selected action names a real consumer.
3. For production-specific work call `studio_production_standing` and ground **one** `productionId` in caller/owner intent before `studio_production_context`. Never infer current intent from directory sort, Git timestamps or Output status.
4. Select existing LEGO by required postcondition, exact inputs, tool read-back and source/version. The current `planning/lego-plan-r1.json` and `processing/profiles/*.json` supply the native Media planning/profile evidence; **do not** duplicate them into a new registry or invent an extra broker.
5. Only after selection, materialize relevant dependencies or submit the compiled physical effect through Runtime. Parameterized Python-only context queries may use `mise exec -- python3 scripts/materialize-python.py` and `.venv/bin/python scripts/studio-agent-surface.py`; do not install renderer dependencies for discovery. Bind resulting receipt/bytes to the **real consuming Production/Output/Claim** before declaring a result.

## Route to existing capability

| Consumer needs | Existing Media entry / Owner boundary |
| --- | --- |
| Representation for an observer, no creative Production | `research/media/engineering-consumption/OMPC-v0.md`, source Owner retains truth |
| Existing Production and allowed source claims | `studio_production_standing` → selected `studio_production_context`; `production_context.py` |
| Existing creative assets and works | `studio_creative_index_query` / `creative_index.py`; derived navigation only |
| Native inspection: video, audio, OTIO or timed text | `studio_processing_profiles` → `studio_processing_probe_plan` → Runtime → raw evidence; use `media-native-processing` Skill |
| Physical editing/render/capture capability | `studio_equipment_propose`; `equipment_discovery.py` → `equipment_capabilities.py` → `equipment_plan.py` (creative) / `equipment_plan_delivery.py` (cross-domain native producers); Workstation/Runtime own readiness/effect |
| Reuse empirical creative judgment | `studio_learning_context` and `research/expression/`; hypotheses do not become human-response facts |
| Installed dependencies | `studio_dependencies_status` → `studio_dependencies_propose`; no implicit installation |
| Selected bytes and recovery | `assets.py`, Production Asset/Blob records and Artifact/byte authority; no automatic second store |
| External distribution | Destination/provider Owner; output approval and physical publication are distinct |

The [consumer-grounded directory audit](docs/directory-audit.md) records current directory responsibilities, retention boundaries, naming decisions, and implementation seams. It is navigation, not a substitute for real source/consumer inspection.

The [per-LEGO capability reference](docs/capability-reference.md) maps current implementations, Human tasks, Agent inputs and evidence boundaries. It is navigation only, never a new registry.

The `agent_surface_contracts.tool_definitions()` schema is the wire contract; directory names, doc prose, `README` tables and Skill descriptions are discovery aids, not alternate API authorities. Don't parse arbitrary narrative files to reconstruct existing action contracts.

## Composition and evidence

Use the existing R2.1 definition `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)` when a LEGO is formally admitted. For an actual selected composition, check at least:

- `pre`: source identity/currentness, chosen input bytes, compatible profile and installed tool or explicitly UNKNOWN readiness.
- `post`: exact output/receipt observed by the selected consumer; do not upgrade process exit to consumer acceptance.
- `inv`: source facts stay with source Owner; Production/Claim/Output identities remain distinct; derived projections do not mutate the Owner.
- `eff`: read-only discovery, physical Runtime effect, retained evidence and destination publication are separate authorities.
- `prov`: exact source/profile/adapter/tool identity and content digests; distinguish OBSERVED, DECLARED, DERIVED, VERIFIED, FALSIFIED and UNKNOWN.
- `c,epsilon,unfold`: real resource/uncertainty cost and decomposition obligations; use typed UNKNOWN where not measured.

Use existing `.agents/skills/design-structure-matrix` for observed coupling and `.agents/skills/compositional-contracts` for actual substitution seams. Prefer deleting unconsumed code over renaming public wire identifiers. A module split is useful only if it gives a replaceable contract without breaking actual consumers.

## Selected processing example

```bash
cd capabilities/media
python3 scripts/studio-agent-surface.py studio_processing_profiles --arguments '{}'
```

Choose the returned `id` plus **both** exact `profileDigest` and `adapterDigest`. Call `studio_processing_probe_plan` with those digests, a real `inputPath` and `evidenceDirectory`; execute the returned plan using Runtime, then read the emitted native evidence. The profile `id` may differ from its filename. FFprobe/FFmpeg, OTIO and ttconv are replaceable native providers; never copy their parsers, or treat QC PASS as rights/aesthetic/publication acceptance. See `../../.agents/skills/media-native-processing/SKILL.md` from the repository root.

## Test, publishing and retirement

For source or contract changes use affected Owner tests (`scripts/owner-environment test`, specific `processing/tests/*-smoke.sh` for changed providers). Use standard Git branch/PR/CI/merge queue; don't replace the repository's release system. Verify current consumers before deleting data; native Git GC/worktree removal and existing cache mechanisms supersede custom cleanup frameworks. Retain selected masters, unique source, rights and actual read-back evidence, not speculative historical copies. A local test PASS is not end-to-end Production publication.

Human-facing orientation is `docs/human-guide.md`; technical source authority remains `MEDIA.md`, `STUDIO.md`, `docs/media-model.md` and live tool schemas.

## Optional DaVinci Resolve equipment

Use [the native API and consumer acceptance contract](docs/resolve-native.md).
Do not rebuild the retired embedded Ordivon menu Runner or staged-operation
protocol. Prefer the installed official API and existing OTIO/FFmpeg LEGO.
Live Windows session, source binding, native readback and Production acceptance
are distinct from fake-Resolve unit tests and historical Free 21 receipts.
## Native Resolve production action

For a real Windows editing consumer, source files and the intended Output
directory are exact task inputs. The source-owned
`scripts/resolve-native-produce.py` is a one-shot official Resolve API
operation for visual cuts, a separate audio track, optional CDL grading,
editable `.drp` and MP4 export. Use Windows Runtime `windowsAuthority=active_user`
and a supported Python API interpreter. Do not write to the selected
user project or bring back the retired menu Runner. Read the resulting
`.receipt.json` and render in a separate native Processing profile.
The installed scripting README is the API authority; the semantic
`studio_equipment_propose` action alone does not perform the physical edit.

## Agent: typed composition of existing Media LEGO

1. Resolve an explicit `productionId`, Claim source revision and
   Asset/Blob identities via existing Studio actions. Never guess from
   most-recent files or rebuild an action registry.
2. Pick the native editorial path: consecutive visual inputs or `--otio`
   with optional native media relinking. On Windows use the existing
   interactive-session Runtime authority and Blackmagic's installed API,
   not an embedded menu Runner. Supply `--min-timeline-frames` from a real
   consumer acceptance requirement, not an arbitrary universal threshold.
3. Read back the Resolve project/timeline and the .drp/.mp4 digest receipt.
   For OTIO, the receipt's `otioMediaReferencesIndependentlyVerified=false`
   requires independent Asset/Blob reconciliation before fidelity claims.
4. Compose existing providers by contract: Remotion renders a selected
   animation, FFprobe/FFmpeg verifies video and Fairlight audio exports,
   `otiotool` inspects editorial structure, `ttconv` handles TTML/SRT/VTT.
   An ASR/translation provider is selected only when a named language/audio
   consumer and real installed provider exist; it is never simulated by QC.
5. Match the delivered bytes to the selected Output and actual consumer
   review. Send publication through the named destination provider only,
   then verify its returned identity/readback. `UNKNOWN` is not `PASS`.
6. Garbage-collect only unreachable disposable workspace/cache bytes after
   checking current source, Production and Output consumers; use native Git
   and provider GC. Preserve selected editable masters and unique evidence.

Each operation is a R2.1 LEGO with an externally owned effect, specific
pre/post/invariants, content digests and observable result. A successful
Runtime process does not establish semantic acceptance or release.

## Native grade and actual media proof obligations

For color edits supply only the non-neutral parameters justified by
the caller, using `--grade-slope R,G,B`,
`--grade-offset R,G,B`, `--grade-power R,G,B`, and/or
`--grade-saturation N`. The producer delegates to Resolve's
`SetCDL` with neutral defaults, and emits `gradeCDL` in its
versioned receipt. Never infer target look or display correctness
from successful API dispatch.

Consume `nativeTimelineMediaReadback` as evidence of what Resolve
actually loaded. `nativeTimelineMediaReadbackComplete=true` proves
only that observed native timeline items resolved to readable,
digest-verified files at execution time. Compare each `sourceDigest`
with the selected Production's authorized Blob sources; preserve
`UNKNOWN` when inaccessible. This observation does not elevate the
OTIO file's own reference semantics to independent proof and does
not approve the film or publish it.

## Agent: parameterized Remotion without duplicate templates

For a selected `runtime-flow` animation, supply `eyebrow` and
`headline` in exact JSON `--props=/path/to/props.json` via the
existing Remotion CLI. The defaults and typed component stay in
`apps/motion-remotion/src/runtime-flow-composition.tsx`; Root advertises
the same `defaultProps`. This is the native Remotion `inputProps` contract,
not a new Ordivon animation schema. Bind the props-file digest and source
revision to the actual rendered MP4, then verify native media bytes
with FFprobe and the selected Production's Claim/Output evidence.
Keep editing only the consuming medium; do not treat render success
as creative acceptance or external publication.
