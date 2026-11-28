# Media R16 shared production source and output observation
Host #32982, #32974; extends R11-R15. No new owner or registry.
Baseline aab8814d3ce4b111e176fd1a64f90e6b8874c992.

## Thought / Logic / Capability
| Logic | Capability | Separation |
|---|---|---|
| Claim source selection | production_source_io.claims_source_path | descriptor is authority, no filename shadow |
| Portable local file naming | canonical_relative_file_path, pathlib | local carrier vs repository-relative motion path |
| Exact byte observation | existing assets.hash_file, native SHA-256 and fstat | unstable remains UNKNOWN |
| Output identity | production_output_identity.observe_output_blob | one implementation, no publication effect |
| Model validation | production_validation | source assertion requires match, historical output absence not failure |
| Context | production_context | mechanical projection, explicit consumer-selected bytes |
| Verification | unittest finite Cartesian oracle, existing Hypothesis, native tools | independent counterexamples, strict gates |

R2.1: I manifest/selected source and carrier; O exact parsed claim set and
bounded observation with role-dependent validation; S read-only local input;
pre canonical portable selected path, declared sourceCarrier, exact digest;
post both consumers select same source and observe same relation;
inv no shadow, no UNKNOWN-to-match, no semantic approval from byte equality;
eff reads only; c one stable hash per output observation, no persistent cache;
epsilon no atomic filesystem snapshot, remote artifact availability or
historical execution proof; prov source-bound RED/GREEN and actual fixture
matrix; unfold select -> resolve -> observe -> consumer policy.

P0 DELETE-CUSTOM duplicate direct hashlib.file_digest path and inline carrier
selection; REUSE existing stable hash_file and read_bound_object.
P0 claims selection and carrier role parity. Repo-relative motion sources
remain supported; no blanket Production-root restriction on motion inputs.
P1 generated property/stateful validation (reuse #2835 lock after merge),
targeted mutation and real consumers; no new runtime dependency.
P1 actual native strict CI handoff #32850, no root writer.
P2 audit remaining production references and QC/equipment seams by actual
counterexamples; keep historical byte and source claims distinct.

Acceptance: real model/context selected claim mismatches, missing and shadow
cases; finite 2x4 role/state matrix; 2x6 invalid path alias matrix, invalid
path must never hash; symlink and unstable evidence. Existing model,
context, lineage and full strict native qualification retain their standing.
