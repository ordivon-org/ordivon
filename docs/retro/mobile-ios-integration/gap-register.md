# Mobile iOS Integration Brownfield Gap Register

Current phase: Phase 5 — forward execution

Perimeter:
- platform/workstation/workstation/software.toml
- platform/workstation/workstation/tool_binding.py
- platform/workstation/tests/test_workstation_tool_binding.py
- platform/workstation/workstation/windows/*
- services/runtime/packaging/windows/*
- services/gateway/src/ordivon_gateway/*
- services/harness mobile/browser execution seams
- Windows Runtime native tool carrier and physical iOS discovery

| ID | Axis | Gap | Evidence | Forward fix | Severity | Effort | Status |
|---|---|---|---|---|---|---|---|
| G-001 | practice | Exact fixed Windows-native external tools cannot use managed_equipment because resolve_managed assumes a Linux Path | platform/workstation/workstation/tool_binding.py:229-242 | Extend the existing managed binding seam to resolve windows_native through the existing Windows path projector and keep exact SHA-256 | P1 | S | candidate-verified |
| G-002 | missing feature | go-ios v1.3.2 has no current mainline exact Workstation binding | platform/workstation/workstation/software.toml | Add one managed_equipment declaration for the admitted versioned carrier | P1 | S | candidate-verified |
| G-003 | missing feature | Original go-ios carrier lived outside Runtime executable roots | live Runtime probe: C:\ProgramData\Ordivon\Mobile direct executable admission failed; RuntimeCandidateR6/native-tools direct limited execution later passed | Keep carrier under the already admitted Runtime native-tools tree; do not broaden C:\ProgramData\Ordivon | P1 | S | live-fixed/candidate-bound |
| G-004 | technology | go-ios v1.3.2 upstream archive identity needed byte-level closure | GitHub Release API digest equals retained go-ios-win.zip SHA-256; tar replayed ios.exe equals original and Runtime carrier SHA-256 | Keep the exact release archive/executable digests in the carrier contract | P2 | S | closed |
| G-005 | missing feature | No physical Apple USB device is currently visible | fresh Windows VID_05AC count=0; go-ios/mobilecli device lists empty | Physical-device gate: USB + trust + Developer Mode, then identity parity | P1 | M | open |
| G-006 | missing feature | No DeviceKit/WDA signing and runner acceptance | no P12/mobileprovision or installed runner evidence | Qualify signing authority and DeviceKit first, WDA as independent fallback | P1 | M | open |

| G-007 | architecture | A second Windows-native iOS provider was not yet bound through the same generic seam | live mobilecli 1.0.20 standalone exe and exact SHA-256 | Reuse managed_equipment; do not add a mobile-specific binding abstraction | P1 | S | candidate-verified |
| G-008 | technology | go-ios 1.3.2 default DeviceKit download is runner 0.0.18 while the Mobile Next line moved beyond it | live go-ios download plus current Mobile Next changelog evidence | Do not sign/install the downloaded 0.0.18 by default; qualify the runner used by current mobilecli first | P1 | S | open |
| G-009 | security | Apple signing inputs have no admitted Windows credential/file authority path yet | go-ios help shows ASC key id + issuer id + .p8 or p12 + mobileprovision inputs; Windows Runtime exposes no credentialAuthorities | Reuse provider-native signing semantics, but add a narrow secure authority/materialization path before any signing effect | P1 | M | open |
| G-010 | missing feature | Exact Windows-native carriers previously depended on manual live copies rather than a source-owned reconstructible transaction | one generic manifest/materializer now handles official go-ios ZIP and npm mobilecli TGZ with exact archive/member/executable digests, staging, fail-closed drift, source self-binding and receipts | Keep the generic native-tool-carrier seam; wire operational convergence only after candidate promotion | P1 | M | candidate-verified |
| G-011 | provenance | mobilecli 1.0.20 registry binary is exact but its Go build metadata reports vcs.modified=true | npm registry integrity + local lock + tarball replay bind the binary; VCS revision b8bd2f90d2af74b2242f5da79e87055e4056d48d is observed but clean-tree reproducibility is not | Treat the registry binary as the current exact carrier while keeping clean-source reproducibility UNKNOWN | P2 | S | bounded-accepted |

What does not change:
- Runtime remains owner of Job/Attempt/execution truth.
- Workstation owns node-local desired state/materialization/binding only.
- Harness/domain code owns mobile task semantics and authorization.
- No new Mobile Runtime, workflow language, router ontology, or generic mobile abstraction is introduced in this slice.
