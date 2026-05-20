## Summary
What this PR changes.

## Boundary Confirmation
- [ ] No policy activation or schema standard claims
- [ ] Phase boundaries respected (see `docs/architecture/ai-native-project-object-model.md`)
- [ ] Import direction preserved

## Verification
- [ ] `cargo test --workspace` passes
- [ ] `PYTHONPATH=.:src .venv/bin/python -m pytest -q tests/` passes
- [ ] `PYTHONPATH=.:src .venv/bin/python scripts/check_document_registry.py` passes
- [ ] `PYTHONPATH=.:src .venv/bin/python -m ordivon_verify all --check` passes
- [ ] New docs registered in `docs/governance/document-registry.jsonl`
- [ ] Receipt generated in `receipts/governance/`

## Debt Registration
If this PR introduces known unresolved issues, register in
`docs/governance/verification-debt-ledger.jsonl`.
