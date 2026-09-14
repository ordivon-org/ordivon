# HARNESS-EDIT-ADDRESSING-002

Status: Adaptive Edit R2 addressing-pressure workload

## Purpose

This Task isolates repeated textual targets. `feature_flags.py` contains two identical
`return False` lines, but only the second logical entity (`beta_enabled`) may change.
The visible suite checks the requested beta behavior; the hidden verifier additionally
requires alpha to remain false and preserves the public function surface.

The task does not make exact replacement impossible: an exact-replacement Agent may
expand `oldText` to include unique surrounding context. Anchored addressing can instead
select the second repeated line directly. The workload therefore measures ACI behavior
rather than hard-coding one codec as the only expressible solution.

Run:

```bash
python3 evals/harness-edit-addressing-002/qa.py
python3 -m unittest -v tests/test_eval_harness_edit_addressing_002.py
```
