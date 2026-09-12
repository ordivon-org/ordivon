# Local Python wheel build type v1

Type URI: `https://ordivon.local/security-v2/build-types/uv-python-wheel/v1`

This is a narrow build-type description for Security v2's local SLSA Build L1 acceptance. It is not a general Ordivon build framework.

Given a clean Git repository and exact `HEAD` revision, the builder:

1. materializes exactly `git archive HEAD` into a temporary source directory;
2. runs `uv build --wheel` against that materialized source;
3. requires exactly one wheel output;
4. computes the wheel SHA-256;
5. emits an in-toto Statement v1 with SLSA provenance predicate `https://slsa.dev/provenance/v1` from the same builder process.

External parameters are the artifact kind (`python-wheel`) and Python requirement (`>=3.12,<3.13`). The exact Git commit is recorded under `resolvedDependencies`. Builder versions identify the builder-script Git commit, uv, and Python version.

This build type makes no SLSA Build L2 or L3 claim. The local machine and builder identity are not independently authenticated by this document.
