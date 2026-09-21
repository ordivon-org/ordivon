# Skills M6 owner extraction acceptance — 2026-09-21

Standing: **ACCEPTED_SOURCE_ONLY**

## Scope

M6 extracts the temporary Agent Skills compatibility bridge from Harness into the independent monorepo owner platform/skills.

This acceptance covers source ownership, package/dependency separation, tests, artifact namespace boundaries, and repository orchestration. It does **not** authorize or claim production Skills MCP cutover.

## Frozen pre-cutover live authority

At acceptance time:

- service: ordivon-skills-mcp.service
- service state: active
- current release: /opt/ordivon/skills-mcp/releases/3d1943e349c21141468f95551e4ee37adc40f7f4
- live working directory: /opt/ordivon/skills-mcp/current
- live config schema: 2
- live project binding: ordivon-next -> /root/projects/ordivon-next
- bind/port: 127.0.0.1:8895
- OAuth environment remains service-owned under /etc/ordivon; no credential bytes were read or moved by M6.

The live service therefore remains on the pre-M6 release and is the rollback/cutover authority for M7.

## Source extraction lineage

1. bb118f9d8a2e4a8f8dcb89608c8992aab5e4698b
   - move-only extraction
   - 33 files
   - 0 insertions / 0 deletions
   - all moves detected as R100 renames
2. 76bb55929f9faba1000401d70ffd485c95cc987e
   - independent package owner established
   - Python namespace moved from ordivon_harness.skills to ordivon_skills
   - independent pyproject.toml, uv.lock, .python-version, and mise.toml
   - example project workspace binding moved to monorepo-owned /root/projects/ordivon/meta/next
   - bridge-only PyYAML/PyJWT test dependencies removed from Harness
3. e053c4f7eadb86eae8eaff53311ef97a315929be
   - owner/artifact boundaries hardened
   - Harness wheel forbids the extracted ordivon_harness/skills/ namespace
   - isolated Harness installation must not resolve ordivon_harness.skills
   - build/release paths clear owner-local setuptools build/ cache before wheel construction
   - root skills:verify added
4. 312658e546e202168b93640f9533b79c5ad22e5c
   - Harness current-evidence profile superseded after extraction
   - prior Python 3.14.7 receipt retained immutable and reclassified historical
   - post-extraction receipt bound to e053c4f7...
5. 1bb308398e9dcfc331ebf3ffea64ffc978bd3877
   - concurrent physical main reconciled
   - services/harness, platform/skills, and root mise.toml tree/blob identities unchanged across reconciliation

## Extracted owner acceptance

mise run skills:verify passed with:

- Python 3.14.7 locked owner environment
- Ruff: PASS
- compileall: PASS
- pytest: **85 passed + 34 subtests**
- independent wheel build: PASS
- wheel contains ordivon_skills
- wheel contains no ordivon_harness/*
- owner source/scripts contain no reverse import of ordivon_harness
- runtime requirements equal package runtime metadata
- example project binding is monorepo-owned /root/projects/ordivon/meta/next

The bridge runtime explicitly owns its actual RSA JWT dependency through pyjwt[crypto]; it no longer relies on cryptography being incidentally present in the Harness environment.

## Harness post-extraction acceptance

mise run harness:verify passed with:

- runtime-search physical profile: PASS
- locked environment / lock check: PASS
- Ruff: PASS
- pytest: **838 passed + 122 subtests**
- dependency contract: PASS
- documentation contract: PASS
- evidence contract: **90 historical / 1 verified**
- deterministic demo: PASS
- wheel build/install smoke: PASS
- hostFreeHarnessVerified=true

Harness source now requires src/ordivon_harness/skills to remain absent.

## Artifact contamination falsifier

During acceptance, a green Harness test run exposed stale setuptools build/ cache that could reinsert the removed Skills namespace into a wheel even though source files had moved.

The migration was not accepted on the first green test result.

The boundary was hardened and then verified in both directions:

- clean Harness wheel: no ordivon_harness/skills/* entries — PASS
- deliberately contaminated wheel containing ordivon_harness/skills/probe.py — checker rejects it — PASS

This turns a one-off cleanup into a permanent fail-closed artifact contract.

## Authority boundary

After M6:

- Agent Skills standards own portable SKILL.md semantics.
- Agent Plugins owns portable plugin packaging.
- MCP / the Skills extension own the wire protocol surface.
- platform/skills owns only the temporary local compatibility bridge: discovery/trust fences, exact-currentness checks, hostile-package filtering, protocol adaptation, and deployment/consumer mechanics.
- Harness owns Agent Run execution and no longer owns Skills internals.
- Host owns semantic continuity and does not own Skill discovery/scheduling.
- Agent Plugin may reference or bundle Skills but does not become the canonical owner of Skill content.

## Not yet accepted

M6 does not prove or perform:

- production Skills MCP source cutover to platform/skills
- live config workspace change from /root/projects/ordivon-next to the monorepo owner
- consumer acceptance against the new immutable release
- rollback rehearsal
- standalone Harness/Next repository retirement
- universal direct-client Agent Skills loading
- permanence of the compatibility bridge

Those remain M7 cutover work.
