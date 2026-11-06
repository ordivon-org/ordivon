# External Capability Evaluation R1 (formerly LEP)

Status: **composition of existing Owners**, not a new service, permission owner, registry, scheduler, formal LEGO calculus or software installer.

## First principles and objective

For one actual consumer C and its incumbent implementation A, introduce upstream B only if the observed consumer benefit exceeds change, ongoing maintenance, integration and recovery costs **while preserving the full required contract**. A GitHub repository is not one LEGO; a project can yield several capability operators and several independently useful methods. Passing toy tests or growing Stars never establishes that B is formally equivalent to A.

Use Recursive LEGO R2.1 and the existing Composition Successor Contract for formal refinement: inputs, outputs, states, pre/postconditions, invariants, effects, cost, approximation, provenance and unfolding. UNKNOWN is not FALSE or PASS. An external candidate record is not a formal declaration. Default: remove redundant custom code **after real consumer proof** → reuse upstream natively → compose existing Owners → use the smallest justified adapter → implement only the genuinely missing capability.

## Modules and natural Owners

| Need | Owner and already-existing source |
|---|---|
| Official external discovery, timestamps and 7-day dedup | Catalog: catalogs/capabilities/scripts/github_radar_incremental.py |
| Upstream source-cut, release/package/license metadata and provider reference | Catalog read-only: catalogs/capabilities/providers/ and evidence/ |
| Skill or executable-influence safety assessment | Security / Skills: .agents/skills/skill-supply-chain-audit/SKILL.md |
| Research operation-local qualification and falsification | Research: profiles/research/tool-qualification/TOOL_QUALIFICATION_R1.md |
| Contract composition and successor migration | Composition: packages/composition/docs/SUCCESSOR_CONTRACT_R1.md |
| Consumer effects, deployment, readback and recovery | Actual domain Owner and Runtime, **never** Catalog |
| Useful external method, without executable adoption | Knowledge lessons and existing Agent Skills |

Pipeline: official discovery → evidence-only candidate → capability/method split → consumer-local contract → license/provenance/Security evidence → independent incumbent comparison, negative controls and recovery → native Owner decision → existing Composition successor → real consumer readback → retire proven redundant code → requalify when versions or assumptions change.

There is deliberately no edge from Trending directly to installation, formal registration or production switching.

## Distinct Human and Agent interfaces

**Human:** The existing [HUMAN_EXTERNAL_LEGO_REVIEW_R1.md](HUMAN_EXTERNAL_LEGO_REVIEW_R1.md) is the task walkthrough. This file is the cross-Owner architecture and evidence contract, not a duplicate how-to.

**Agent:** [AGENTS.md](../AGENTS.md) is the local Owner routing entry; .agents/skills/external-capability-evaluation/SKILL.md is the on-demand reusable method. No new permission or registration authority is created.

**Observed:** Worktrunk read-only inventory matched the scoped Repo consumer, while prunable and Runtime lifecycle equivalence remain unproved. The actual Repo observation of 145 worktrees/107 detached was dated and not live currentness. The Research packet remains HOLD.

## Existing provider commands

Official Github radar (does not install or admit any software):

    python3 catalogs/capabilities/scripts/github_radar_incremental.py --live --limit-per-window 5 --history-dir catalogs/capabilities/evidence/github-radar --output catalogs/capabilities/evidence/github-radar/YYYY-MM-DD.json

Pinned standard JSON Schema validator, already available in Ordivon:

    uv run --with check-jsonschema==0.38.0 check-jsonschema --schemafile catalogs/capabilities/evidence/external-capability-candidate-r1.schema.json catalogs/capabilities/evidence/worktrunk-candidate-20261106.json

Narrow existing Git/cross-file reference witness (not another JSON parser):

    python3 catalogs/capabilities/scripts/check_external_candidate_references.py catalogs/capabilities/evidence/worktrunk-candidate-20261106.json

Owner consumer comparison in a disposable fixture, with an independently sourced/reviewed binary matching the pinned Worktrunk v0.81.0 digest:

    python3 catalogs/capabilities/scripts/compare_worktrunk_owner_consumer.py --binary /path/to/wt --output /tmp/consumer-evaluation.json

Actual Repo governance consumer: tools/repo/exhaustive_coverage.py. The experiment demonstrated equivalent scoped read-only output but native Git supplies prunable facts with no demonstrated Worktrunk counterpart. **Decision: KEEP_NATIVE_GIT.**

## LEGO collection and mature source strategy

Capability candidates: GitHub source discovery and metadata (gh api); native Git worktree inspection; Worktrunk UX inventory; web-content extraction; semantic desktop control; security audit tooling. These are distinct candidates, not pre-registered formal LEGOs.

Method candidates: independently falsifiable source-bound research, contract refinement and recovery, branch-centric presentation over the true owner, provider-native reuse, Strangler Fig or expand-contract for scoped migration, and provenance-first supply chain decisions. Use existing Skills such as recursive-lego-calculus, compositional-contracts, design-structure-matrix, minimum-sufficient-representation, skill-supply-chain-audit. Avoid registering duplicate descriptions for the same method.

Cross-Owner discovery-only facts with exact commits and LICENSE blob IDs: catalogs/capabilities/evidence/cross-owner-source-observations-20261106.json, covering agent-desktop / Workstation, Scrapling / Research, cloudflare security-audit-skill / Security-Skills. Real integration and compatibility remain UNKNOWN; no installation or substitution occurred.

## Cleanup and publication

Classify each file as active-consumer source, uniquely recoverable evidence, recomputable short-lived report, or duplicate/expired/no-consumer. Keep the first two when consumers are real; aggressively remove the rest, while using Git history for published old revisions. Do not delete other agents' Workspaces or system files from filesystem searches. Use Runtime's native workspace.close after exact lifecycle checks, not a hand-written rm of Runtime state. Use standard GitHub PR, required checks, merge queue and post-merge readback instead of bypass mechanisms.

This pass retires the duplicate early Worktrunk fixture runner, two superseded machine reports, the speculative cross-Owner placeholder and duplicate Research/Worktrunk instructions. The single retained owner-consumer study preserves the distinguishing experimental facts. Real production substitutions and proven retired custom code remain **zero** for this pilot, not an inferred cost saving.

## External established standards

- SLSA v1.2 (https://slsa.dev/spec/v1.2/) for source/build provenance; only claim a provenance level when attested and verified.
- in-toto (https://in-toto.io/) for authenticated subjects, predicates and multi-step attestations; do not build an Ordivon fork.
- OpenSSF Scorecard (https://openssf.org/projects/scorecard/) as upstream risk signal, not proof of interface suitability.
- SPDX 3.0 (https://spdx.dev/use/specifications/) for package/license/relationship vocabulary when an actual SBOM or license inventory is warranted.

No new permanent verification suite is needed merely because an upstream exists; use the incumbent's normal Owner acceptance suite and a few discriminating counterexamples.
