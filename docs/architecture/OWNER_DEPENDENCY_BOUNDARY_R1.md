# Ordivon owner dependency boundary R1

Source implementation: `tools/repo/check_owner_boundaries.py`, policy: `tools/repo/dependency_contracts.toml`.

Updated: 2026-11-10. Status: **IMPLEMENTED** — bounded source-literal and public Python AST dependency check.

## Contract

Repository co-location confers neither ownership nor permission to import an
Owner's private implementation. Cross-Owner consumption follows an explicitly
named public contract or narrow observed source seam. The existing guard scans
active tracked code/config and rejects undeclared literal references and stale
or overlapping policy exceptions.

## Observed seams (2026-11-10; main ef17d6879d12faa61fff3bb762b0d500d73c9113)

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
| Capability Catalog ELE | Artifact / Preservation / Capital / Network / Harness / Media | Source-qualified research projections only; no effect or truth transfer |
| Data | Capital | Test-only ODPS source contract |
| Composition | Capital | Test-only Finance public source contracts |

Observed check at this SourceCut: **2,320 active tracked files; 10 source packages; 31 declared seam entries; 38 bounded source references; zero undeclared literal/public-import edges in the checked scope**. These numbers come from the existing `python3 tools/repo/check_owner_boundaries.py`; they are not a manually maintained dependency registry. Declared seam edges are not proof of installed or dynamic consumer reachability.

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
