# Developer egress: GitHub Release acquisition

The developer-egress profile preserves the single native Gluetun Surfshark
outbound. Browser downloads of GitHub Release assets returned HTTP 504
although the official GitHub release-asset REST API, accessed through the
same VPN using native GitHub CLI, returned complete, digest-verified bytes.

The Network consumer code github_release_mise.py checks one exact upstream
GitHub asset ID, declared state, name, size, archive SHA256 and extracted
binary SHA256. It then atomically installs it in the path owned by upstream
jdx/mise-action. The upstream pinned action is retained for toolchain and
PATH management, and independently checks its sha256 input.

Run at monorepo root with gh authentication:
python3 platform/network/consumers/developer-egress/github_release_mise.py

On GitHub Actions the read-only github.token is supplied as GH_TOKEN.
Failures fail closed; no direct/public-proxy fallback, third-party mirror,
second VPN session, new credential owner or alternative package manager.
This is a developer tool transport, not an OCI Supply-Chain policy change.

CI hosted runner egress is separate from Ordivon VPN; actual merge_group
verification is required to prove that consumer.

Official upstream: https://docs.github.com/en/rest/releases/assets
Action: https://github.com/jdx/mise-action


The same GitHub Runner counterexample then affected the pinned Python
3.15.1 standalone distribution. The --python mode fetches upstream
astral-sh/python-build-standalone asset ID 663549456 (38,075,450 bytes),
checks its official SHA-256 and the extracted Python 3.15.1 executable
digest, and stages the official install_only_stripped archive into
mise's native installs/python/3.15.1 layout. Native mise install python@3.15.1
then reports already installed and mise which python resolves that exact
interpreter. This is reuse of an upstream relocatable Python distribution
and of mise's own installation layout, not a Python build system or a new
toolchain manager. A mismatched existing executable fails closed.

Locally qualified with a fresh disposable MISE_DATA_DIR, an actual GitHub
API 38 MB download and a native mise install/which consumer readback.


The GitHub-hosted runner also observed transient 502/503/504 on mise's
native aqua releases for uv and gitleaks after the official Python
distribution was recovered. The root verification jobs therefore use
mise install itself, limiting native install parallelism to two with a
three-attempt outer bound. Already installed tools are reused by mise;
checksums, Owner tests and required GitHub jobs are not skipped.
If every attempt fails, the job exits nonzero with an explicit upstream
network blocker, rather than reporting test PASS.
