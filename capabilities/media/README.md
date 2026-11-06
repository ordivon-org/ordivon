# Ordivon Media

Ordivon Media is an **optional media-domain capability** for intentional, reusable mediation and authored expression. It does not own every observer-facing representation across Ordivon, and it does not become a second truth authority.

The project Constitution is [`MEDIA.md`](MEDIA.md); canonical Media research starts at [`research/media/`](research/media/README.md). **Ordivon Studio is retained inside this project as the authoring and production capability plane.** Existing `ordivon-studio` CLI/package/tool identities remain Studio capability names rather than repository-owner names.

## Activation boundary

The default representation remains with its natural source/client owner. A tool result, status card, metric, ordinary UI projection, browser view, repository view, or provider-native response does **not** enter Media merely because a human or Agent can observe it.

Activate Media when the task actually requires a media-specific responsibility such as:

- a durable/reusable observer-facing projection contract;
- authored narrative or visual/audio/motion expression;
- editable production state;
- cross-medium composition/transformation;
- media-specific technical QC or review preparation;
- selected-asset provenance/rights needed by a production.

Use [`OMPC-v0`](research/media/engineering-consumption/OMPC-v0.md) as an optional reference when those projection semantics materially matter. It is not a mandatory contract for every Ordivon projection.

**Studio is an optional production capability.** A Studio Claim / Production is needed only when authoring, editing, rendering, packaging, or other Studio-owned production work is actually required. Consequential action remains with its external admission/execution owner.

### R6 Trial Ledger — PostgreSQL transition

The R6 search-history ledger now uses PostgreSQL instead of creating new
SQLite files. Set ORDIVON_MEDIA_TRIAL_PG_DSN for search. When the frozen
winner contains a PostgreSQL trial-ledger witness, the sealed holdout **must**
reuse the same search ledger: the native per-search transaction verifies the
exact frozen source/selected candidate before appending one reveal event.
Pure in-memory reasoning without a ledger remains available for independently
constructed research fixtures, but it cannot silently upgrade to a recorded
search or drop a recorded search's history.
The one-time SQLite importer now **defaults to no historical import**.
Only import a stopped legacy experiment when a current registered-search replay
or sealed-holdout audit actually consumes its history. Bind the exact consumer
search ID, selected purpose, and an independently established writer-stop
condition:

    uv run --project capabilities/media python capabilities/media/scripts/migrate-r6-trials.py \
      --sqlite /path/to/old-trials.sqlite \
      --expected-search-id experiment:required-current-search \
      --retention-consumer registered_search_replay --source-writers-stopped

The stop flag is an **operator assertion**, not automatic proof of all writers'
quiescence. The importer reads but never deletes the old source, and checks
identity, full event hashes, count, and PostgreSQL readback. The old file is
eligible for a *separate* consumer-based retirement decision after verified
cutover; neither an old file's existence nor hypothetical future usefulness
is a reason to migrate or retain it indefinitely. If no real consumer needs
the experiment, do not copy the event chain into PostgreSQL.
Run the PG acceptance via mise run pg:verify using a disposable
ORDIVON_MEDIA_TRIAL_TEST_DSN. Skipped tests do not prove the PG boundary.

## Source responsibility layout

The published `ordivon_studio` package keeps production, equipment, asset,
review and presentation capabilities at its root. Experimental validity,
creative-alpha, grounded-meaning and article/foundational studies live in
`ordivon_studio.research`. Research scripts import that subpackage directly;
there are no redundant compatibility shims or separate research truth store.

The R6 Creative Alpha method separates `research/creative_protocol.py`
(sealed protocol and mechanism construction), `research/creative_observer.py`
(browser-receipt-to-task projection), and `research/creative_analysis.py`
(independent visible, holdout, uncertainty and portfolio scoring).
The R6 experiment CLI consumes these owners directly. The former
`research/creative_alpha.py` monolith is retired without an adapter facade.

Equipment follows a three-stage, source-readable contract:
`equipment_discovery.py` observes physical Workstation/tool candidates;
`equipment_capabilities.py` projects selectable actions and verification;
`equipment_plan.py` compiles exact native-tool arguments without execution.
`equipment.py` remains the stable Studio/Agent entry point. Selection, planning,
process execution (Runtime), and output acceptance (the source/Artifact owner)
are **distinct**; no new equipment engine or parallel asset authority is admitted.

Creative navigation follows the same source-of-truth rule:
`creative_index.py` orchestrates a rebuildable projection over Media's native
equipment, productions and collections. `creative_index_artifact.py` reads
Artifact delivery evidence, and `creative_index_library.py` reads source-owned
Creative Library catalogs and generated evidence. `creative_index_source_utils.py`
retains only shared JSON reads and nonrecursive metadata traversal. All nodes
and relations remain derived navigation; queries do not mutate owner records.

The Agent entry point follows the existing ports-and-adapters boundary:
`agent_surface.py` advertises and validates stable JSON Schema tools;
`agent_dependencies.py` observes exact Python/pnpm materialization and emits
explicit acquisition **plans** without installing anything;
`agent_productions.py` reads owner-native Production identity and does not
guess the Agent's currently intended Production. The runtime/tool-execution
authority and production/source truth remain outside the Agent adapter.

Resolve-private editorial interchange and selected-asset binding live in
`ordivon_studio.resolve_editorial`. `resolve_discovery` owns Windows/WSL
and FFprobe observations; the already-existing `resolve_contracts` owns
the pure native result contract and operation identity. `resolve_operations`
constructs the operation payloads without side effects; `resolve_adapter`
owns the existing Windows operation stage, Runner installation and result
readback, rejecting success receipts bound to a different staged operation.
The embedded Resolve Runner remains the same self-contained deployable file.
OpenTimelineIO and existing Media Blob hashing are reused, not reimplemented.

Video perception follows the same native-tool composition:
`perception_video_io.py` invokes FFmpeg's built-in `select`, `tblend`,
`signalstats` and `xstack` filters to observe frames and assemble a real
contact sheet; `perception_selection.py` purely selects a bounded set of
diagnostic frames using coverage, user requests and observed change peaks.
`perception.py` composes the review bundle, and `rich_perception.py` consumes
the native observer directly. Neither module claims to infer visual meaning,
scene importance or creative approval. The source video and exact frame bytes
remain with their natural asset/production owner.

## Studio capability plane

A Runtime fact is true at revision `R`. Studio turns it into a film. Runtime later changes.

The film still expresses what was bound at `R`; it does **not** become the current Runtime authority because it is polished, approved, or published.

**Ordivon Studio turns source-owned reality into editable medium-specific expression without creating a second truth store.**

```text
exact owner revision + bounded Claim
→ editable writing / visual / audio / motion / interaction source
→ selected Assets and exact bytes
→ render or composition
→ factual/mechanical review
→ medium craft judgment
→ human-response calibration only when the claim requires it
→ Output / publication package
```

## Purpose

Facts and code do not decide how a reader should encounter them. Studio owns the remaining creative responsibility: medium choice, narrative structure, editable production state, selected expression, rendering, review preparation, and replaceable delivery variants.

The source owner keeps current product/research truth. Studio keeps the expression bound to the exact source revision.

## One expression journey

For a video explaining Runtime recovery:

1. Runtime owns the fact and evidence.
2. Studio binds an exact Runtime revision through a Claim that limits what may be said.
3. Studio chooses narration, diagrams, pacing, typography, motion, sound, and edit structure.
4. Render evidence proves what artifact was observed; decision context proves which Claim/Production boundary governed review.
5. An Agent may revise or no-op; intermediate critique is transient unless its consequence matters later.
6. A later Runtime change does not silently float the old Claim. Studio keeps a historical expression or explicitly rebases it.

## Responsibility boundary

| Responsibility | Owner |
| --- | --- |
| current product/research fact | source repository/native owner |
| revision-bound allowed expression | Studio Claim |
| creative intent and editable production state | Studio |
| exact selected bytes | the named durable byte authority for that medium |
| render/QC evidence | Studio tooling and retained receipts |
| public site orientation/publication | Web or destination platform |
| external publication/effect | destination/provider + caller IAM/policy; optional Distribution profile only for a demonstrated cross-provider gap |
| human comprehension, preference, trust, recall, or other audience response | scoped human-response evidence |

Persisting or presenting another owner's fact does not transfer that fact to Studio.

## Human-response boundary

Studio separates three claims:

```text
mechanical / factual → verify against source, bytes and render evidence
medium craft         → conventions + explicit intent + bounded critique
human experience     → human/expert evidence when uncertainty matters
```

A vision-capable Agent can falsify obvious semantic or visual problems. It cannot establish that people understood, preferred, trusted, remembered, or enjoyed the work. One person's preference is not universal taste authority either.

This is why a Production may remain in `review` after technical, factual, storage, and Agent-perception checks pass when the unresolved decision is genuinely human-response dependent.

## Current boundary

Studio currently retains:

- the cross-medium identity source and Art & Expression Laboratory;
- Production, Claim, Asset/Blob, TimedText, Receipt, and Output contracts;
- editable production sources and reusable expression primitives;
- provenance/rights records for selected Assets;
- deterministic media inspection, rendering, QC, review preparation, and selected-byte recovery;
- optional Resolve/OTIO equipment behind explicit compatibility checks;
- real motion and Writing-only Productions that pressure-test the model.

Large media bytes, caches, proxies, and exports stay outside Git. Git stores identities, manifests, editable text/code, provenance, interchange snapshots, and checksums. Exact selected bytes use the durable authority appropriate to their medium and failure boundary; Git itself may already be sufficient for canonical tracked text/code.

Current production status and storage evidence remain in the production and technical documents rather than this entry page.

`studio_production_standing` deliberately does **not** infer a unique current Production from status, directory order, or recent Git activity. When several valid Productions exist, caller/owner intent must identify the work before `studio_production_context` is consumed. This preserves action relevance without turning a convenient index into a priority authority.

## Start here

For ordinary Agent work, start from the dependency-independent Studio semantic surface rather than reconstructing Production state from repository chronology or materializing the full authoring environment first. Running it with no action lists the bounded owner-native actions and their schemas:

```bash
python3 scripts/studio-agent-surface.py
```

| Need | Read / invoke |
| --- | --- |
| design or inspect a generic observer-facing Media projection without assuming Studio production | [`research/media/engineering-consumption/OMPC-v0.md`](research/media/engineering-consumption/OMPC-v0.md) |
| discover the bounded Studio Agent surface without `.venv` or `node_modules` | `python3 scripts/studio-agent-surface.py` |
| discover existing FFprobe/FFmpeg/OTIO/timed-text processing LEGO with exact profile hashes | `./.venv/bin/python scripts/studio-agent-surface.py studio_processing_profiles --arguments '{}'` (after the pinned Python dependencies are materialized) |
| compile one selected processing profile into a digest-pinned, nonexecuting Runtime command | Use the existing Studio action: studio_processing_probe_plan, with digests from studio_processing_profiles |
| inspect Production standing before selecting current work | `python3 scripts/studio-agent-surface.py studio_production_standing --arguments '{}'` |
| after caller/owner intent identifies one Production, inspect its bounded context | `python3 scripts/studio-agent-surface.py studio_production_context --arguments '{"productionId":"<id>"}'` |
| inspect one Production, its Claims/Outputs, and optional source-binding Git relation through the lower-level CLI | `uv run ordivon-studio production-context <production-root> [--source-repo BINDING_ID=PATH]` |
| hydrate scoped retained learning for the selected Production | `python3 scripts/studio-agent-surface.py studio_learning_context --arguments '{"currentProductionId":"<id>"}'` |
| compile a truthful equipment proposal only when one exact capability is needed | `python3 scripts/studio-agent-surface.py studio_equipment_propose --arguments '{"capability":"<capability>","parameters":{}}'` |
| use lower-level media inspection/render/QC/recovery operations after dependencies are materialized | `uv run ordivon-studio --help` |
| understand the Media owner contract | [`MEDIA.md`](MEDIA.md) |
| inspect Phase-1 closure / freeze / reopen posture | [`docs/media-phase1-construction-audit.md`](docs/media-phase1-construction-audit.md) |
| understand why Studio exists | this README |
| determine document/fact/evidence authority | [`docs/authority.md`](docs/authority.md) |
| first-principles architecture and technical choices | [`STUDIO.md`](STUDIO.md) |
| Production/Claim/Asset/Blob/Output model | [`docs/media-model.md`](docs/media-model.md) |
| Agent review consumption and transient critique | [`docs/review-consumption.md`](docs/review-consumption.md) |
| perception/model-view preparation | [`docs/artifact-perception.md`](docs/artifact-perception.md) |
| Art & Expression research | [`research/expression/README.md`](research/expression/README.md) |
| local render/review loop | [`docs/fast-inner-loop.md`](docs/fast-inner-loop.md) |
| storage/recovery boundaries | [`docs/storage-layout.md`](docs/storage-layout.md) |

## Fresh Workspace bootstrap

```bash
scripts/owner-environment bootstrap
scripts/owner-environment doctor
scripts/owner-environment test
```

The owner entrypoint consumes the existing pinned `mise.toml`, `pnpm-lock.yaml`, `uv.lock`, and Python materialization receipt. `cold-start` proves the same default check surface from a copied source fence with neither `node_modules` nor `.venv`.

Resolve is optional equipment:

```bash
scripts/owner-environment test-resolve
```

## License

Apache-2.0. Production assets may carry their own rights and usage records in Asset metadata.

Studio CLI command processing is organized by domain under
`src/ordivon_studio/cli_handlers/` (media, ecology, equipment, Resolve).
The public `ordivon-studio` console entry, `argparse` grammar and result
exit codes remain owned by `cli.py`; this source-only split adds neither
another command registry nor another operational authority.

The R6 experiment core has three source/consumer boundaries under
`src/ordivon_studio/research/`: `trial_registration.py` (typed registration,
seed seal), `trial_ledger.py` (PostgreSQL-native append-only history), and
`search_calibration.py` (search/replay/holdout and null calibration).
No legacy `research_validity.py` facade or second database authority is
retained. The research CLIs and test consumers import the natural boundary.

The R5 Grounded Meaning research method is implemented by
`research/grounded_evidence.py` (evidence and result contracts),
`research/grounded_text_tasks.py` (controlled writing and comprehension tasks),
`research/grounded_av_tasks.py` (source-semantic video, timed transcript,
speech and crossmodal tasks), and `research/grounded_provider.py` (the
existing bundled experiment entry point). `grounded_scoring.py` independently
scores provider receipts. The former `grounded_meaning.py` is retired rather
than retained as a forwarding module.
