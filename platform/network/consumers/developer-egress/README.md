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
