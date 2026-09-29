# Experimental Fabric Pilot R2

Status: **offline design/compiler implementation; no R2 Provider campaign admitted yet**.

R2 follows R1 but treats its two strongest lessons as hard constraints:

1. requested model identifiers are not treatment evidence unless Provider effective identities remain distinct; and
2. repeated Provider samples on one task are not independent task replication.

The planned design is a blocked 2×2 Model×Harness factorial. The current model factors are
`deepseek-flash` and `deepseek-v4-pro`; the Harness factors remain
`exact-replacement-v1` and `anchored-line-v1`. Every independent task instance receives all four cells.

The task-bank target is 24 independent task instances: 8 qualified variants from each of the three current Harness eval families (`repository_repair`, `edit_addressing`, `edit_multiregion`). One predeclared sentinel per family receives a second Provider replicate in all four cells. This yields 96 core trials + 12 nested stochasticity trials = 108 total live runs while task-level independent n remains 24.

`design_r2.py` is deliberately Provider-free. It validates a task-bank manifest and a separate Provider model-identity preflight, rejects alias collapse, compiles a seeded randomized schedule, and computes exact-rational task-block contrasts without counting nested Provider repeats as independent observations.

No live execution is permitted until:

- the 24 task variants exist and each has independent task/QA digests;
- a disjoint calibration bank has shown the endpoint is not at an obvious floor/ceiling;
- real Provider identity preflight proves `deepseek-flash` and `deepseek-v4-pro` resolve to distinct effective identities at execution time;
- the uncertainty method and missing-cell rules are preregistered;
- complete fixture/finalize/fork/acceptance tests pass; and
- the R2 preregistration is committed.

The R1 runner and evidence remain immutable. R2 is a new experiment revision rather than a patch to R1.
