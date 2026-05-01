# Ordivon Verify — Release Readiness Checklist

Status: **PROPOSAL** | Date: 2026-05-01 | Phase: PV-12
Authority: `proposal`

## 1. Code Readiness

- [ ] CLI extracted to package structure (`src/ordivon_verify/`)
- [ ] All checks modularized (receipts, debt, gates, docs)
- [ ] No private Ordivon Core dependencies in package code
- [ ] No broker/API code in package
- [ ] No finance pack references
- [ ] No Phase 7P paper dogfood references
- [ ] No internal paths (`/root/projects/Ordivon/`)
- [ ] Exit codes 0-4 implemented and tested
- [ ] `--json` output schema stable
- [ ] All tests pass in clean checkout

## 2. Packaging Readiness

- [ ] `pyproject.toml` created with package metadata
- [ ] `README.md` finalized for public repo
- [ ] `CHANGELOG.md` created (empty initially, or v0.1.0 entry)
- [ ] Console script entrypoint registered
- [ ] `pip install -e .` or `uv pip install` tested locally
- [ ] Package imports work: `from ordivon_verify import cli`
- [ ] No private repo paths in package code

## 3. Documentation Readiness

- [ ] Public README finalized (from PV-10 draft)
- [ ] Quickstart tested end-to-end by a fresh user
- [ ] Adoption guide complete
- [ ] CLI contract documented
- [ ] CI example clear and marked as example
- [ ] PR comment templates ready
- [ ] Agent skill (SKILL.md) included
- [ ] No internal-only references in any public doc
- [ ] No "Phase 7P", "DG-Z", "Post-DG" mentions in public docs
- [ ] No `/root/projects/` paths in docs

## 4. Security / Privacy Readiness

- [ ] Secret scan run (git-secrets, trufflehog, or gitleaks)
- [ ] Zero secrets found
- [ ] No API keys, tokens, or credentials
- [ ] No `.env` files
- [ ] No broker URLs
- [ ] No internal hostnames or IPs
- [ ] Dependency audit run
- [ ] No vulnerable dependencies

## 5. Governance Readiness

- [ ] READY does not claim authorization
- [ ] READY does not claim merge approval
- [ ] READY does not claim production readiness
- [ ] BLOCKED is documented as governance success
- [ ] DEGRADED is documented as review-required
- [ ] No claims of real customers
- [ ] No claims of production maturity
- [ ] Maturity label clear (public alpha, not stable)

## 6. Community Readiness

- [ ] Public issue templates created
- [ ] Contribution policy decided (if open-source)
- [ ] Code of conduct considered (if open-source)
- [ ] Discussion venue identified (GitHub Discussions, etc.)

## 7. Legal / License Readiness

- [ ] License selected and committed (Apache-2.0 recommended)
- [ ] LICENSE file present in repo root
- [ ] License references in pyproject.toml
- [ ] No conflicting licenses in dependencies
- [ ] Trademark considerations noted

## 8. Release Decision Gate

All checkboxes above must be checked before public alpha.

Additionally:
- [ ] Private Ordivon team review complete
- [ ] Extraction audit receipt created
- [ ] Secret / private reference audit clean
- [ ] Decision recorded with rationale

## 9. Non-Activation Clause

No release has occurred. This checklist defines gates for a future release decision. All items are unchecked because no release is in progress.
