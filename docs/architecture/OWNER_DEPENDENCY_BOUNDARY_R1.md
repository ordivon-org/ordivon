# Ordivon owner dependency boundary R1

Source implementation: `tools/repo/check_owner_boundaries.py`, policy: `tools/repo/dependency_contracts.toml`.

Updated: 2026-11-06. Status: **IMPLEMENTED** — bounded source-literal dependency check.

## Contract

Repository co-location confers neither ownership nor permission to import an
Owner's private implementation. Cross-Owner consumption follows an explicitly
named public contract or narrow observed source seam. The existing guard scans
active tracked code/config and rejects undeclared literal references and stale
or overlapping policy exceptions.

## Observed seams (2026-11-06; main 21ae23a)

| Consumer | Producer | Boundary |
| --- | --- | --- |
| Harness | Security | Named public Security subtree locators |
| Web | Security | Public verifier/admission contracts and explicit E2E/test bindings |
| Media | Artifact | Read-only delivery/acceptance projection |
| Workstation | Distribution | Native smoke acceptance evidence |
| Workstation | Game / Media | Test-only environment bindings |
| Harness / Composition | Runtime | Pinned public formal toolchain, not Job/Attempt authority |
| Composition | Runtime | Source-bound formal trace test contract |
| Artifact | Authority Catalog | Test-only publication venue locator |

Observed check: **2,136 active tracked files; 19 seam declarations;
21 literal references; zero undeclared literal edges**.
These are source-text observations, not proof that a referenced consumer
is exercised in the deployed system.

## Retired ownership

`meta/` and standalone Next source are retired in this SourceCut. They are not
Owners, not approved dependency destinations, and not resurrected by historical
references, compatibility aliases, receipts or old plans. Their live responsibilities were delegated to natural Owners such as
Composition, Skills, Authority Catalog, Studies and domain-specific modules.

## Limits

The check covers literal source paths, not all package-resolver imports,
constructed paths, runtime calls, generated code or semantic consumer behavior.
Language-native and runtime consumer checks remain with the affected Owner.
This bounded policy is preferable to inventing a global dependency registry.
