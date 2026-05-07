# Ordivon Verify External Dogfood — Hermes Agent

Status: **CLOSED** | Date: 2026-05-07
Phase: External-Dogfood | Target: `/root/projects/hermes-agent`
Authority: `supporting_evidence` | AI Read Priority: 2

## Purpose

This receipt records a first read-only Ordivon Verify trial against the external
local repository `/root/projects/hermes-agent`.

The goal was to test the current product wedge as a newcomer would use it:

```text
AI coding project -> Ordivon Verify check -> trust report
```

This receipt is evidence only. It does not authorize merge, release, deploy,
publication, package extraction, checker promotion, token handling, agent
execution, or external action.

## Repository Condition

Observed before the trial:

- Hermes worktree had one pre-existing modification:
  `ui-tui/package-lock.json`.
- No Hermes files were modified by this trial.
- Ordivon used only read-only checks and a temporary config under `/tmp`.

## Trial 1 — No Ordivon Config

Command:

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent --markdown
```

Observed result:

- Status: `DEGRADED`
- Mode: `advisory`
- Missing evidence:
  - `receipt_paths`
  - `debt_ledger`
  - `gate_manifest`
  - `document_registry`

Interpretation:

Hermes is not Ordivon-configured. The report correctly refused to produce
READY from an unconfigured external repo and surfaced missing governance
evidence instead.

## Trial 2 — Ad Hoc Claim Scan

Temporary config:

```json
{
  "schema_version": "0.1",
  "project_name": "hermes-agent-adhoc-claims",
  "mode": "advisory",
  "receipt_paths": [
    "README.md",
    "AGENTS.md",
    "RELEASE_v0.11.0.md",
    "SECURITY.md"
  ]
}
```

Observed result:

- Status: `DEGRADED`
- Claim/receipt/test/diff/review surfaces: `PASS`
- Debt/docs/gates surfaces: `MISSING_EVIDENCE`

Interpretation:

The lightweight receipt scanner found no direct receipt contradiction in the
selected public-facing claim documents. The project still remained DEGRADED
because debt, gate, and document-governance evidence were not configured.

## Product Finding

This dogfood exposed a useful product gap:

```text
Ordivon Verify can honestly classify an unconfigured external repo,
but it does not yet auto-discover common existing evidence surfaces.
```

Hermes has many relevant evidence objects:

- test suites under `tests/`
- security boundary documentation in `SECURITY.md`
- skills under `skills/` and `optional-skills/`
- ACP/MCP/permission-related code and docs
- release notes with feature and deployment claims

Today, Ordivon only uses those surfaces if the user provides a config or if a
dedicated checker knows how to import them. That is acceptable for Alpha, but it
creates newcomer friction.

## Follow-Up Implementation — Suggest Config

After the initial trial, Ordivon Verify added a read-only evidence discovery
entry point:

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent --suggest-config
```

It now also supports newcomer-readable Markdown:

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent --suggest-config --markdown
```

Observed Hermes inventory:

- Python test files: `822`
- JS test-like files: `515`
- GitHub workflows: `10`
- `SKILL.md` files: `145`
- Candidate claim/receipt docs: `AGENTS.md`, `CONTRIBUTING.md`, `README.md`,
  `SECURITY.md`, and release notes.
- Agent-native surfaces discovered:
  - `mcp`: `hermes_cli/mcp_config.py`, `mcp_serve.py`, MCP skills/docs.
  - `acp`: `acp_adapter/**`, `acp_registry/agent.json`, ACP tests/docs.
  - `approval`: `tools/approval.py`, ACP permissions, gateway approval tests.
  - `memory`: memory providers/plugins/docs.
  - `credential`: credential pool/source files and credential tests/docs.
- Gate candidates inferred:
  - `bash scripts/run_tests.sh`
  - `python -m pytest tests/ -q`
  - 10 GitHub workflow candidates, including tests, Nix, docs, Docker, skills,
    deployment, and supply-chain audit workflows.
- Release claim audit:
  - `80` release claim lines sampled.
  - `22` sampled claim lines lacked obvious local evidence references.
- Skill safety precheck:
  - broad tool/shell mentions: `120`
  - credential-language mentions: `91`
  - script mentions: `145`
  - high-attention overlaps: `79`
- Agent-native risk matrix:
  - `mcp`: high
  - `acp`: high
  - `approval`: high
  - `memory`: medium
  - `credential`: high
  - `skills`: high

Suggested config was advisory-only:

```json
{
  "schema_version": "0.1",
  "project_name": "hermes-agent",
  "mode": "advisory",
  "receipt_paths": [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "SECURITY.md",
    "RELEASE_v0.10.0.md",
    "RELEASE_v0.11.0.md",
    "RELEASE_v0.2.0.md",
    "RELEASE_v0.3.0.md"
  ]
}
```

This is still not full project-independent governance. It is a first discovery
layer: Ordivon can now see the external repo's evidence landscape before
asking the user to write governance files.

## Follow-Up Implementation — Deep External Audit Draft

The discovery layer was then expanded beyond counts into per-surface
evidence judgments:

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent --suggest-config --standard-pack --markdown
```

Observed Hermes deep-audit draft:

- `SKILL.md` files scanned: `145`
  - PASS: `0`
  - WARN: `55`
  - FAIL: `90`
  - Common findings: script/shell surfaces, credential language, missing
    boundary statements, protocol/server surfaces, and authorization language.
- GitHub workflow gate inference:
  - high-confidence verification candidates: docs site checks, Nix checks,
    supply-chain audit, tests.
  - not-canonical for verification without owner confirmation: contributor
    checks, deploy-site, docker-publish, nix-lockfile-fix, skills-index.
  - deployment/write/release workflows are intentionally separated from
    verification gates.
- Release claim evidence mapping:
  - claim lines sampled: `80`
  - supported: `2`
  - partial: `53`
  - missing evidence reference: `25`
  - blocked: `0`
  - This does not prove unsupported claims false; it shows which claims still
    need CI/test/workflow/review evidence mapping.
- Agent claim bindings:
  - binding file: not found.
  - Hermes cannot yet bind a specific agent completion claim to concrete
    artifacts, tests, receipt, and review evidence.
- Standard pack draft:
  - `ordivon.verify.json`
  - `governance/verification-gate-manifest.json`
  - `governance/verification-debt-ledger.jsonl`
  - `governance/document-registry.jsonl`
  - `governance/skill-safety-report.json`
  - `governance/release-claim-map.jsonl`
  - `governance/agent-claim-bindings.jsonl`
  - `governance/discovery-candidates.json`
  - `governance/project-ai-onboarding-playbook.md`
  - `receipts/external-audit-receipt.md`

The standard pack is a dry-run template pack only. It writes no files, does not
claim that inferred gates are canonical, and does not specialize Ordivon to
Hermes. Discovery candidates are separated from canonical templates so the
target project's own AI or owner can decide what becomes local governance.

## Follow-Up Implementation — Coding Trust Profile v1

Ordivon Verify then made the previously implicit coding trust profile explicit:

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent --profile coding --risk-stage vibe --summary
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent --profile coding --risk-stage merge --markdown --full
```

Observed behavior:

- `vibe` stage returns `DEGRADED`, not `BLOCKED`, and keeps the report compact:
  missing `receipt_paths`, `debt_ledger`, `gate_manifest`, and
  `document_registry`.
- `merge` stage returns `BLOCKED` because Hermes has no confirmed
  `agent_claims.jsonl` binding and no configured canonical `gate_manifest`.
- `--full` includes an evidence appendix summarizing agent claim bindings,
  release claim evidence map, skill safety counts, gate candidates, and
  agent-native risk surfaces.

This confirms the intended product split:

```text
vibe  = fast advisory discovery during rapid AI-assisted coding
merge = concrete claim-to-evidence closure before trusting work
release = stricter release/skill/tool/debt boundary audit
```

## Follow-Up Implementation — Newcomer Flow Repair

Hermes dogfood then exposed a concrete false-comfort bug in new-project
onboarding:

```text
discovery suggested Markdown files in receipt_paths,
but the receipt scanner only scanned directories.
```

Observed before repair:

- Suggested config included file paths such as `AGENTS.md`, `README.md`,
  `SECURITY.md`, and `RELEASE_v0.11.0.md`.
- The configured run reported `receipts: PASS`.
- The receipt summary was actually `0 receipt(s) scanned, 0 contradictions`.

This was incorrect product behavior: a configured evidence path that scans zero
files must not look like evidence sufficiency.

Implemented repair:

- `receipt_paths` now accepts both Markdown files and directories containing
  Markdown receipts.
- Configured `receipt_paths` that match zero Markdown files now return
  `WARN`/`MISSING_EVIDENCE` instead of `PASS`.
- `--suggest-config --summary` now renders a compact onboarding summary instead
  of large JSON.

Hermes retest with a temporary config:

```json
{
  "schema_version": "0.1",
  "project_name": "hermes-agent",
  "pack": "coding",
  "profile": "ai_coding_trust_audit",
  "risk_stage": "vibe",
  "mode": "advisory",
  "receipt_paths": [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "SECURITY.md",
    "RELEASE_v0.11.0.md"
  ]
}
```

Observed after repair:

- Status: `DEGRADED`
- Receipts: `PASS`
- Receipt summary: `5 receipt(s) scanned, 0 contradictions`
- Remaining missing evidence:
  - `debt_ledger`
  - `gate_manifest`
  - `document_registry`

New onboarding summary command:

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent \
  --profile coding --risk-stage vibe \
  --suggest-config --standard-pack --summary
```

Observed compact summary:

- Candidate claim/receipt docs: `14`
- Candidate test commands: `2`
- GitHub workflows: `10` (`5` likely verification candidates, `5`
  write/deploy surfaces)
- `SKILL.md` files: `145` (`WARN 55`, `FAIL 90`)
- Release claims sampled: `80` (`25` missing evidence refs)
- Agent claim bindings: `0` (`not found`)

## Remaining Gap

The current implementation has moved from pre-verification into structured
external audit draft, but it is still not full proof:

```text
discover evidence surfaces != prove a specific claim
infer gates != confirm canonical gates
map release claims != prove claims true or false
skill safety heuristic != full human security review
risk matrix != authorization boundary enforcement
standard pack draft != committed project governance
```

The next maturity step is to turn these discovered surfaces into optional
read-only external checkers:

- per-skill safety reviewer with explicit owner disposition.
- workflow/gate manifest generator with reviewer and approver confirmation.
- release-claim-to-evidence mapper tied to CI runs, PRs, and review notes.
- MCP/ACP/approval/memory/credential boundary checker.
- agent claim binding files that connect one claim to diff, test, receipt, and
  review evidence.

## Recommended Next Product Work

1. Add an external dry-run helper that reports discovered candidate evidence
   paths without treating them as verified. **Round-1 implemented as
   `--suggest-config`.**
2. Add optional read-only skill scan support for external repositories with
   `skills/**/SKILL.md` and `optional-skills/**/SKILL.md`. **Round-2
   implemented as per-file PASS/WARN/FAIL.**
3. Add a `--suggest-config` mode that prints a proposed `ordivon.verify.json`
   from discovered files, but does not write it. **Round-1 implemented.**
4. Keep default unconfigured external repos as `DEGRADED`, not READY.
5. Add a dry-run standard pack so a newcomer can see the exact files needed
   for adoption without Ordivon mutating the target repository. **Round-2
   implemented as `--standard-pack`.**

## Boundary

The Hermes result is not a quality score for Hermes. It means only that Ordivon
did not receive enough configured governance evidence to verify AI work claims
as READY.

READY, PASS, DEGRADED, and BLOCKED remain evidence signals only. They are not
authorization to merge, release, deploy, execute, publish, trade, refresh
tokens, start servers, or perform external action.
