# ClusterFuzzLite admission R1

Date: 2026-09-12
Standing: `FUZZ_TARGET_VERIFIED / PROVIDER_RUNTIME_BLOCKED`.

## Integration shape

Security v2 now carries the standard external ClusterFuzzLite project surface:

- `.clusterfuzzlite/project.yaml` with `language: python`;
- `.clusterfuzzlite/Dockerfile` based on the OSS-Fuzz Python builder image;
- `.clusterfuzzlite/build.sh` producing a standalone Atheris fuzzer wrapper;
- `fuzz/replay_binding_fuzzer.py` as a real semantic-waist fuzz target.

The target fuzzes `ReplayBinding`, not a dummy parser. It continuously checks three Security invariants:

1. empty request identity fails closed;
2. exact replay returns the original admission rather than a later caller-supplied result;
3. reusing the same request identity with changed content fails closed.

These are the same residual semantics preserved by the old->v2 effect-admission differential.

## Local target proof

The exact Atheris target was executed directly under Python 3.12 with Atheris 3.1.0 for 20,000 bounded runs. The run completed without an invariant crash. This proves the target and invariants are executable; it does not claim ClusterFuzzLite orchestration ran. An earlier attempt with obsolete Atheris 2.3.0 failed during package compilation on Python 3.12 and was not promoted to fuzz evidence.

## Provider-runtime blocker

ClusterFuzzLite's documented local toolchain requires Docker and the OSS-Fuzz builder images. On the current host during R1:

- the Docker CLI is present but `/var/run/docker.sock` is absent, so no Docker daemon is available;
- direct registry access to `gcr.io/oss-fuzz-base` timed out;
- no Network or Operations configuration was changed to force this provider green.

Therefore the ClusterFuzzLite build/container path remains `PROVIDER_RUNTIME_BLOCKED`. The configuration is admitted as the target integration, while provider execution must be re-run after the shared container/network substrate is available.

Security does not replace the blocked ClusterFuzzLite orchestration with a custom fuzz engine. Direct Atheris is only a target-level acceptance.
