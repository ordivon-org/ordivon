# OpenSSF Scorecard admission R1

Date: 2026-09-12
Standing: `PROVIDER_AVAILABLE / TARGET_IDENTITY_BLOCKED`.

## Provider proof

OpenSSF Scorecard release `v5.5.0` was acquired from the official GitHub release rather than Docker Hub.

- release binary reports Git commit `c395761df6afe1a69e476bc60a013a94bcbc153f`;
- Linux amd64 release archive SHA-256: `83b90a05c1540ef1390db1cd5711e5fd04be9c1d8537fb84d39d02092d6a8dff`;
- the archive digest exactly matches the official `scorecard_checksums.txt` in the same release;
- extracted binary SHA-256 observed locally: `e63945e2c94060b4768d86b3ae3878c3b985fbfae3b082603a6fa9c06f28fe86`.

## Why Security v2 itself is not yet scanned

At the R1 observation boundary, the standalone Security-v2 carrier at /root/projects/ordivon-security-v2 had no Git remote. A read-only query of the authenticated GitHub account returned no repository matching ordivon-security*. Scorecard evaluates forge/repository posture, so inventing another repository identity or scanning an unrelated project would have been false-green evidence. The current Security source owner is /root/projects/ordivon/platform/security; this historical R1 blocker is not a claim about the current monorepo repository identity.

An unauthenticated public-repository CLI smoke was also attempted and exceeded the bounded 180-second acceptance window. This does not alter the target-identity blocker.

## Admission rule

Scorecard becomes a current Security v2 evidence provider only after an exact forge repository identity exists and is bound to the exact source revision under review. Security will consume named checks plus applicability metadata; the aggregate score is never admission authority by itself.

No remote repository was created and no Git configuration was mutated during R1.
