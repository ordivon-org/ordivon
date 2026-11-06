# External LEGO Evolution R1 — evidence-first, owner-local pipeline

**SourceCut:** 65d9bba3e2000f973fc3bcc05410fa2a8f97b5b7 (2026-11-06).

This is a composition of *existing* Catalog, Skills, Research and Composition obligations, not a new registry, permission service, scheduler, global source of truth or form of LEGO. No new always-on process is required.

## Evidence flow

1. **Discovery** — GitHub official daily/weekly/monthly Trending, upstream repo and release metadata, papers, standards, provider-native APIs. Stars are candidate-discovery signals only. Run the idempotent observation exporter as a report-producing task, never as installer.
2. **Decomposition** — isolate goal, natural semantic owner, real consumer, executable ability and transferable method. A repository or Skill package is not automatically one LEGO. Incomplete observations stay INCOMPLETE_CANDIDATE.
3. **Source and security** — bind exact source revision, GitHub repo, release digest, LICENSE, package inspection and Skill supply-chain review. Keep source approval, scanner outcome, effect authority and scientific qualification separate.
4. **Research qualification** — use the existing Research Tool Qualification R1 packet, positive/negative controls and owner-currentness requirement. No extra universal Tool Registry.
5. **Comparison** — match the incumbent and candidate against one real consumer contract; use property, negative, fault, performance and roll-back tests where relevant. Independent verifier-owned truth remains outside Catalog.
6. **Adoption or abstention** — owner decides direct reuse, scoped activation, minimal adapter, KEEP_NATIVE, HOLD or REJECT. Composition Successor Contract binds old/new candidates but does not promote them. Materialize only when owner has verified exact current state and effect approval.
7. **Evolution** — reobserve upstream/current license and actual owner state on version or contract change. Remove custom wrappers only after independently validating consumer reachability, negative evidence, restore path and post-cutover readback.

## First source-cut evidence chain

- Source discovery and upstream exact version: catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json
- Provider routing note: catalogs/capabilities/providers/worktrunk.md
- Method lesson: catalogs/knowledge/lessons/worktrunk-workspace-native-git-r1.md
- Existing Skill security procedure: .agents/skills/skill-supply-chain-audit/SKILL.md
- Existing Research qualification schema and scoped HOLD: profiles/research/tool-qualification/examples/worktrunk-workspace-r1.json
- Existing Composition Successor Contract: packages/composition/docs/SUCCESSOR_CONTRACT_R1.md
- Actual incumbent owner source: services/runtime/crates/ordivon-runtime-core/src/universal/workspace/
- Native Git / Worktrunk experiment and readback: catalogs/capabilities/evidence/worktrunk-git-comparison-20261106.json

Run: python3 catalogs/capabilities/scripts/check_external_lego_evidence.py catalogs/capabilities/evidence/external-lego-worktrunk-20261106.json

## Daily GitHub radar — no autonomous adoption

Run in a real local Runtime Workspace with GitHub official network access and authenticated GitHub CLI:

python3 catalogs/capabilities/scripts/github_radar_incremental.py --live --limit-per-window 5 --history-dir catalogs/capabilities/evidence/github-radar --output catalogs/capabilities/evidence/github-radar/YYYY-MM-DD.json

In a manual / replay situation use --input a frozen GitHub Trending observation instead of --live. The output contains repo, URL, per-window official Trending new-star display, UTC retrieval time, separately fetched current total Stars, metadata license and seven-day repeat status. Do not treat license metadata alone as LICENSE verification. For actual recommendations, inspect commit/release/licensing and compare the last seven days of both structured output and human-readable briefs.

This operation only creates a candidate observation. A resulting report does not imply that an external project was pulled, executed, installed, registered as a formal R2.1 LEGO, or adopted by a domain. There is deliberately no automatic auto-promote path.

## P2 initial Worktrunk experiment

Pinned v0.81.0 Linux release archive SHA-256 was checked against official release checksum. The binary executed only inside a disposable Git fixture. Reproduce after independently obtaining and checking the binary:

python3 catalogs/capabilities/scripts/compare_worktrunk_git.py --binary /path/to/reviewed/wt --output /path/to/new-report.json

The results show a positive read-only inventory comparison, dirty-state detection, native Git refusal to remove a dirty worktree, and successful fixture teardown. The experiment **does not** establish Worktrunk equivalence with Runtime's Workspace lifecycle, source cut, recovery, Host relation, privileged execution or side effects. Therefore keep Runtime native Git; no production switch or deletion is authorized. A separate owner-native integration and false-case replay are mandatory before changing that decision.

## P3 cross-owner learning without claims inflation

Evidence: catalogs/capabilities/evidence/cross-owner-evolution-prospective-r1.json

- Runtime: current scoped Worktrunk inventory comparison.
- Workstation: prospective semantic desktop accessibility from vercel-labs/agent-desktop; no consumer proof.
- Research acquisition: prospective D4Vinci/Scrapling; no data-quality or crawl-policy proof.

The starting scorecard is zero *verified* production substitutions and zero *verified* retired custom lines from this pipeline. Actual benefits require current owner evidence: baseline sources, exact consumer reads, candidate version, native tests, positive/negative/fault cases, measured cost/latency, rollback, and new source readback. UNKNOWN is not counted as zero improvement or as a passing result.

## Anti-growth constraints

- No global capability registry, central workflow/promotion service, parallel owner authority or registry database.
- No duplicate R2.1 calculus or per-file LEGO identities.
- No separate installation-currentness database; consult actual provider and owner.
- No upstream project hooks/bootstrap executables without independent review.
- No automatic deletion based only on zero grep hits or a positive fixture test.
