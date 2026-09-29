# Experimental Fabric Pilot R1 — Model × Harness

This study is the first live inferential-pressure consumer of Experimental Fabric R1.

Design: a balanced `2 Model × 2 Harness codec × 3 task block` pilot using the current Adaptive Edit live runner. The two model levels are `deepseek-flash` and `deepseek-v4-flash`; the two Harness levels are `exact-replacement-v1` and `anchored-line-v1`; the three deterministic task families are the current repository-repair, repeated-addressing, and multi-region edit evals.

The run is deliberately small. Its purpose is to validate factor attribution, owner/evidence binding, provider-owned randomness representation, contamination detection, and analysis plumbing before spending on a larger replicated campaign. Cell estimates are descriptive; the three task blocks do not justify a broad capability ranking or significance claim.

The runner writes the preregistration and assignment schedule before any live trial. It journals `trial_started` before Provider dispatch and fails closed on restart if a started trial has no completion record, so uncertain Provider work is never blindly replayed.

Run from `services/harness` so the existing Harness development environment and live runner are the execution substrate:

```bash
mise exec -- uv run python ../../studies/experimental-episode/pilot-r1/run_factorial_pilot_r1.py \
  --output-dir ../../studies/experimental-episode/pilot-r1/evidence/20260928-r1
```

The pilot uses the existing root-private DeepSeek secret file and never copies credential material into the study artifacts.

## Post-live finalization recovery

The preregistered R1 runner is intentionally immutable after live execution. The first live campaign completed all 12 planned Provider trials and durably journaled every `trial_started` with a matching `trial_completed`, then failed during deterministic analysis serialization because the repository canonical JSON contract rejects floating-point values.

`recover_finalize_r1.py` is a post-registered deterministic recovery adapter. It does **not** call the Provider and refuses recovery unless the frozen runner still matches the preregistration, all 12 journal starts are completed, and the result, Episode, and EvaluationRecord digests validate. It encodes analysis rates and means as exact `{numerator, denominator}` rationals, then produces `analysis.json`, `forks.json`, `acceptance.json`, and `recovery.json` from the already frozen live evidence.

Run from `services/harness`:

```bash
mise exec -- uv run python ../../studies/experimental-episode/pilot-r1/recover_finalize_r1.py \
  --output-dir ../../studies/experimental-episode/pilot-r1/evidence/20260928-r1
```

Recovery is finalization only. It must never be used to replay an uncertain Provider trial; an unmatched `trial_started` is a fail-closed condition.

## Model-factor qualification

A later owner-evidence audit found that the preregistered requested identifiers
`deepseek-flash` and legacy `deepseek-v4-flash` did not produce two distinct effective
Provider model identities in this live campaign. Across the frozen 12 trials, 29
Provider calls requested `deepseek-flash` and 28 requested `deepseek-v4-flash`; all
57 calls report effective/provider model `deepseek-flash` with the same observed
system fingerprint. The append-only evidence artifact
`evidence/20260928-r1/model-factor-qualification.json` therefore marks the Model main
effect and Model×Harness interaction as `NOT_ESTIMABLE`. It does not rewrite the
preregistration, trials, Episodes, EvaluationRecords, analysis, or the mechanical
`PASS_PILOT_MECHANICS` acceptance. Harness/process/recovery/fork mechanics remain
useful within the single observed effective-model regime.

Run the deterministic qualification check from `services/harness`:

```bash
mise exec -- uv run python ../../studies/experimental-episode/pilot-r1/qualify_model_factor_r1.py \
  --evidence-dir ../../studies/experimental-episode/pilot-r1/evidence/20260928-r1
```
