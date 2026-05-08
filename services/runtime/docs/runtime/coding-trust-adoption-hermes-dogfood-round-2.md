# Coding Trust Adoption — Hermes Dogfood Round 2

Status: **CLOSED** | Date: 2026-05-08
Phase: Coding-Trust-Adoption-R2
Task type: read-only external dogfood + report UX repair
Risk level: AP-R0 / R0
Authority impact: supporting evidence only; no authorization semantics

## Summary

Hermes Agent was used as a read-only agent-native dogfood sample for Coding
Trust Adoption after CTTS closure.

The exercise validated:

- `--summary` is useful for first-contact onboarding.
- `--markdown --full` exposes the correct merge-stage blockers.
- `--suggest-config --template deep --emit-template-dir` can emit a deep
  project-independent adoption pack without modifying the target repo.
- Hermes-specific observations remain dogfood evidence only and must not become
  generic OV template rules.

## Commands Run

```bash
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent \
  --suggest-config --template standard --summary

uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent \
  --profile coding --risk-stage merge --markdown --full

rm -rf /tmp/ov-hermes-deep-pack
uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent \
  --suggest-config --risk-stage release --template deep \
  --emit-template-dir /tmp/ov-hermes-deep-pack --summary

uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent \
  --suggest-config --risk-stage release --template deep --markdown
```

## Discovery Result

Observed by read-only discovery:

- candidate claim/receipt docs: 14
- candidate test commands: 2
- GitHub workflows: 10
- likely verification workflow candidates: 5
- write/deploy workflow surfaces: 5
- `SKILL.md` files: 145
- skill safety statuses: PASS 0 / WARN 55 / FAIL 90
- release claim lines sampled: 80
- release claim lines without evidence refs: 25
- agent claim bindings: 0
- memory/content records: 0
- harness/trace bundles: 0

## Merge-Stage Trust Result

The merge-stage trust report returned `BLOCKED`.

Primary blockers:

- missing agent claim binding file
- missing owner-confirmed gate manifest

Supporting missing evidence:

- no `receipt_paths` configured
- no debt ledger configured
- no document registry configured

This is the correct signal. Hermes may have strong local evidence, but OV cannot
trust a specific AI coding work claim until the project AI binds the claim to
artifacts, tests, receipt, review evidence, and owner-confirmed gates.

## Template Export Result

Deep template export wrote 16 files to:

```text
/tmp/ov-hermes-deep-pack
```

The target repo was not modified by OV. Existing Hermes working tree state was
observed as pre-existing:

```text
M ui-tui/package-lock.json
```

OV did not modify that file.

## UX Finding and Repair

Finding:

The first Hermes merge full Markdown report was semantically correct but noisy:
the same missing-evidence issues appeared under Top Findings, Hard Failures,
Missing Evidence, and Warnings.

Repair:

Markdown rendering now suppresses:

- Warnings entries already represented by hard failures or missing evidence.
- Missing Evidence rows already represented as Hard Failures.

Expected UX:

- Top Findings gives the reviewer the short diagnosis.
- Hard Failures names blockers.
- Missing Evidence lists remaining non-hard evidence gaps.
- Warnings only shows distinct warnings, not duplicate missing-evidence rows.

Verification:

```bash
uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_cli.py -q
# 84 passed

uv run --with pytest python -m pytest tests/unit/product/test_ordivon_verify_*.py tests/unit/product/test_coding_trust_template_localization_ctts2.py -q
# 321 passed

uv run python scripts/ordivon_verify.py check /root/projects/hermes-agent \
  --profile coding --risk-stage merge --markdown --full
# BLOCKED; Warnings section suppressed; Missing Evidence excludes hard-failure duplicates

python checkers/current-truth/run.py
# PASS

uv run python scripts/check_document_registry.py
# 241 registered docs, 0 completeness violations

python scripts/check_artifact_registry.py
# 705 registered artifacts, 0 ungoverned, 0 class errors

uv run python scripts/run_baseline.py --read-only
# READY, 26/26 hard gates PASS

uv run python scripts/run_baseline.py --pr-fast
# READY, 12/12 hard gates PASS

uv run python scripts/audit_ordivon_verify_public_wedge.py
# 0 blocking findings
```

## NO-GO Boundary Confirmation

This dogfood did not:

- modify Hermes
- promote Hermes workflows into generic OV gates
- authorize Hermes merge/release/deploy
- execute Hermes tests, skills, tools, agents, or workflows
- read credentials or refresh tokens
- add SaaS, GitHub bot, MCP server, agent runner, or auto-fixer behavior

`READY_WITHOUT_AUTHORIZATION` remains evidence sufficiency only.

## Closure Verdict

Coding Trust Adoption Hermes Dogfood Round 2 is CLOSED.

Next:

```text
Run the same adoption flow against a tiny fixture and a medium AI-heavy sample,
then compare report length and newcomer comprehension.
```
