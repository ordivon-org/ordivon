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
