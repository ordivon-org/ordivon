# Media Owner directory and consumer audit 鈥?2026-11-07

Scope: `capabilities/media/` in the active `ordivon-org/ordivon` monorepo.
This is a **source/consumer inventory**, not a second LEGO registry, a filesystem
garbage collector, or a claim that every output has been externally revalidated.
The source baseline was observed on 2026-11-07; the change branch is cut from
`origin/main`. Re-observe the working tree and consumers before effectful
deletion. The archived standalone Media repository is not a release target.

## Decision rule

Keep a file because a current consumer needs its exact bytes or semantics, not
because it happened to exist. Conversely, do not delete source, deliverable,
rights/provenance evidence, or a replay contract merely because its filename
contains `history`, `render`, `evidence`, `r6`, or `old`. Prefer a native
provider or existing Owner's capability over a parallel Media framework.

Only call a target **deletable** after checking Git-tracked references, runtime
consumers, Production source/output identities, and remote/provider needs;
being absent from Python imports is not sufficient for media source bytes.
Unknown consumer reachability stays **UNKNOWN**, not FALSE. Build caches are
managed using the native package managers and Git, not through a bespoke
destructive Media cleanup command.

## Actual directory decisions

| Actual directory | Responsibility and observed consumer | Decision / next change |
| --- | --- | --- |
| `apps/motion-remotion/` | Programmatic video compositions, source edits and rendered Output consumed by Productions | KEEP. Renderer-specific adapter; parameters remain source/Production decisions. Do not move shared identity tokens into Remotion. |
| `apps/preview/` | Web preview app used by the creative review loop | KEEP. Its compiled `dist/` and installed `node_modules/` are rebuildable, ignored caches, not immutable source. |
| `packages/identity/` | DTCG design-token source and replaceable compiler | KEEP. Align token semantics with DTCG 2025.10, not a proprietary identity registry. |
| `packages/visuals/` | React/SVG reusable primitives consumed by applications | KEEP. Do not make Remotion the owner of visuals. |
| `src/ordivon_studio/` | Python Studio CLI/Agent surface; Production, review, perception, QC, creative index, equipment, research and R2 adapters | CONVERGE by actual import/consumer seams. Reuse one Production source path boundary in both Production context and learning; preserve public `ordivon-studio` and `studio_*` names. Do not split into new pip packages without independent release consumers. |
| `scripts/` | Actual entrypoints for dependency materialization, native providers, equipment, research experiments and old production reproduction | KEEP CURRENT CONSUMERS. Evaluate `run-r4/r5/r6`, `migrate-r6-trials` and SAPI scripts against reproducible experiment/Production requirements before retirement; lack of direct import alone is not a deletion proof. |
| `processing/` | Digest-selected FFprobe/FFmpeg, OTIO and TTML adapter scripts; profile JSON and native consumer smoke checks | KEEP. Exact Profile/Adapter digests and real provider readback are already the LEGO seam. No second media decoder or executor. |
| `schemas/` | Existing Production, Asset, Claims, timed text and receipt formats | KEEP. These are wire/data contracts; do not rename live IDs for cosmetic consistency. |
| `formal/` | Lean/SMT abstraction of selected processing admission and numerical soundness | KEEP AS MODEL, NOT END-TO-END PROOF. An implementation-refinement/physical-provider gap remains UNKNOWN. |
| `planning/` | Existing `lego-plan-r1.json` evidence/contract map used by Agents | KEEP as current planning carrier. Do not duplicate into new catalog/registry. Audit statuses against actual source, installed provider and consumers before claiming operation. |
| `productions/` | 13 named Productions; exact editorial/project source, Claims, Outputs and work-specific evidence | KEEP by selected Production consumer, not a blanket archive. `live-relay-001` contains a ~40 MB MKV master and ~16 MB MP4 source: independently named work roles, not automatic cache. |
| `creative-library/` | Source boundary and browseable creative work navigation | KEEP. Search/index projections do not own the referenced source facts. |
| `artifacts/` | Current creative-index catalog, preserved archive snapshot, derived previews and provenance receipts | AUDIT AS DERIVED DATA, NOT AUTO-DELETE. Current catalog/derived receipts refer to these exact paths; regenerate/repoint and prove consumer reachability before removing any tracked payload. |
| `research/media/` | Media Foundations MF0鈥揗F9 and cross-Owner research navigation | KEEP semantic and provenance boundaries; MF10 remains UNKNOWN / NOT ADMITTED. Historical research names are not public API rename targets. |
| `research/expression/` | Art/Expression priors, R4鈥揜6 experiments and scoped learning evidence | KEEP when an experiment or `studio_learning_context` consumes it. Reject promotion of one viewer's reaction into universal aesthetic truth. |
| `research/equipment/` | Equipment world, capability experiments and E6/E7 evidence | KEEP while `studio_equipment_propose` and tool-choice research consume its source. Tool presence is not a proof of operation. |
| `play/` | Dated Media Ecology pilot with its own references and regression tests | ISOLATE AS PILOT, not core runtime; retire only once the pilot's explicit consumer/retention decision is recorded. |
| `tests/` | Source and real-consumer regressions (Studio semantics, native adapters, formal gaps) | KEEP targeted tests that witness implementation/refinement and independent provider behavior. Prefer mature test runners; do not add synthetic gates merely to make directory symmetry. |
| `docs/` | Human guide, capability reference, authority, Resolve/native and semantic baseline | KEEP as navigation and explanation only; executable tool schemas and source remain authoritative. |

The top-level `.venv/`, app `node_modules/` and Python `__pycache__/`
are locally ignored, disposable dependency/cache state. The audit observed
a ~51 MB `.venv` and installed JS modules, **but did not remove them**:
current tests or native production may still consume the materialization.
OS/Windows/WSL directories and the unrelated Network Owner are out of scope.

### Exact-byte duplicates are not automatically redundant

The identical PNG bytes at
`productions/archive-archipelago-001/render/archive-archipelago-001.png`
and `productions/live-relay-001/source/archive-archipelago-001.png` have
different Production roles. The same applies to a Convergence Object PNG
reused by Live Relay. Do not unlink a self-contained source snapshot to save
space unless the consuming Production switches to a digest-addressed Blob
and recovery/replay is demonstrated. Several identical tiny Chromium console
JSON receipts also retain distinct encounter paths; cleaning them saves
negligible bytes and could lose context.

## LEGO selection 鈥?not a new registry

Use the existing `planning/lego-plan-r1.json`, the actual `studio_*`
tool definitions, `processing/profiles/*.json`, selected Production source
and native tool evidence.

| Selected need | Existing mature capability LEGO | What remains owned by Media | Required consumer evidence |
| --- | --- | --- | --- |
| Media file inspection | FFprobe/FFmpeg | Profile interpretation and expected output | Real input, exact adapter+profile, output readback |
| Editorial timeline | ASWF OpenTimelineIO + Resolve official API | Selected Production/timeline mapping and fidelity limits | Independent media refs, native timeline/project readback |
| Programmatic motion | Remotion + React/SVG | Selected editable composition and design grammar | Parameter-specific render/probe and Output consumer |
| Text timing/captions | TTML + ttconv, SRT/WebVTT | Source cue identities, editorial meaning and language | Exact cue/time parse and delivery inspection |
| Audio loudness | FFmpeg EBU R128/BS.1770-compatible measurement | Delivery profile and result interpretation | Actual measured audio, true peak and tolerance |
| Shared visual identity | DTCG 2025.10 + existing token compiler | Token meaning, renderer-independent visual source | Output in an actual consumer |
| Creative retrieval | Existing Creative Library + derived Creative Index | Navigation and source-bounded creative reuse | Resolved source identity/revision, not just search hit |
| Local/remote byte durability | Existing CAS and Cloudflare R2 adapter | Asset/Blob semantic link and recovery expectation | SHA-256 re-materialization; remote is a replica |
| Agent execution | Existing Runtime/Harness/Workstation | Semantic action and exact non-executing proposal | Runtime Job, physical effect, receipt and consumer |

**Capability LEGO** may bind an existing native provider. **Idea LEGO**
(such as source-truth conservation, observer-vs-source, editable-master
separation, or human-evidence uncertainty) constrains composition and
falsification; it is not automatically a separate executable service.
For formalized LEGO retain `ell=(I,O,S,pre,post,inv,eff,c,epsilon,prov,unfold)`
and preserve UNKNOWN where implementation refinement or real use is absent.

## Human path

1. Select a named Production, audience, permitted factual Claim and actual deliverable.
2. Inspect its editable source, rights constraints and Output identity.
3. Reuse existing Creative Library, visual tokens, Remotion/Resolve source and
   native Processing profiles instead of selecting equipment by popularity.
4. View or listen to the **real result**; mechanical QC does not establish
   beauty, narrative meaning, language correctness, copyright or acceptance.
5. Approve the appropriate Output deliberately. External publication remains
   the destination owner's operation; retain its provider receipt if published.

Use `docs/human-guide.md` for commands and examples.

## Agent path

1. Call the source-only `scripts/studio-agent-surface.py` discovery, then
   `studio_production_standing`. Select the user's actual `productionId`.
2. Use `studio_production_context` to bind the Claim/source revision and
   Output; pick the existing LEGO by `pre/post/eff/prov` and real consumer.
3. For a selected native QC profile, call
   `studio_processing_profiles` then `studio_processing_probe_plan`
   with **both** advertised digests. For hardware, use
   `studio_equipment_propose`; readiness/proposal is not execution.
4. Submit the explicit effect through existing Runtime, inspect Job
   disposition and actual media evidence, and verify source/Output linkage.
5. Report separately mechanical evidence, subjective/human consequence,
   source-owner truth and publication status. UNKNOWN does not mean PASS.
6. Retire only unconsumed scratch/cache/worktrees using native providers
   after checking the consumer and digest recovery boundary.

Use `AGENTS.md` and existing `media-studio-navigation` and
`media-native-processing` Skills. This file creates **no additional agent
surface, registry, CLI, or approval protocol**.

## Mature external baseline

- [PyPA src-layout guidance](https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/):
  keep `src/ordivon_studio` as an importable distribution; avoid speculative
  cross-distribution extraction.
- [ASWF OpenTimelineIO](https://opentimelineio.readthedocs.io/en/latest/):
  editorial cut/interchange information references external media, not the
  media bytes or every NLE-specific effect.
- [Design Tokens Community Group 2025.10](https://www.w3.org/community/reports/design-tokens/CG-FINAL-format-20251028/):
  standardized tokens before tool-specific transform code.
- [Di谩taxis](https://diataxis.fr/): make Human how-tos, Agent interface
  reference, and architectural explanation serve different reader jobs.

## Prioritized consumer-driven follow-ups

- **P0, implemented in this change:** remove identical Production source
  JSON/path boundary implementations from `learning_context.py`; reuse the
  existing Production Context functions and add a regression for path escape.
  Keep wire IDs, manifests and actual results stable.
- **P1, conditional:** `agent_surface.py` coordinates seven or more domains;
  measure actual cold discovery cost/import pressure or independent consumer
  requirements before a dispatcher split. Do not split only for file count.
- **P1, conditional:** evaluate the ~62 MB Live Relay sources and outputs
  against selected delivery/re-edit/recovery consumers; do not treat
  binary size or same digest alone as a deletion proof.
- **P2, conditional:** inspect historical `run-r4/r5/r6`, SAPI and `play/`
  consumers before moving or retiring them. Historical evidence should
  remain available by Git revision even if executable code is retired.

No system files, OS services, independent Owner data, current Production
masters or ignored tool environments are deleted by this change.
