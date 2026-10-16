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
| G-001 | practice | Exact fixed Windows-native external tools could not use managed_equipment because resolve_managed assumed a Linux Path | platform/workstation/workstation/tool_binding.py + current main c3cf38199aacbd8867029bf90a230ad61122ecc0 | Existing managed binding now resolves windows_native through the existing Windows path projector and verifies exact SHA-256 | P1 | S | done |
| G-002 | missing feature | go-ios v1.3.2 previously had no current-main exact Workstation binding | platform/workstation/workstation/software.toml + current main c3cf38199aacbd8867029bf90a230ad61122ecc0 | Exact managed_equipment binding now names the admitted versioned carrier | P1 | S | done |
| G-003 | missing feature | Original go-ios carrier lived outside Runtime executable roots | original C:/ProgramData/Ordivon/Mobile direct admission failed; fresh 2026-10-17 direct limited Runtime execution from RuntimeCandidateR6/native-tools passed | Keep carriers under the already admitted Runtime native-tools tree; do not broaden C:/ProgramData/Ordivon | P1 | S | done |
| G-004 | technology | go-ios v1.3.2 upstream archive identity needed byte-level closure | GitHub Release API digest equals retained go-ios-win.zip SHA-256; tar replayed ios.exe equals original and Runtime carrier SHA-256 | Keep the exact release archive/executable digests in the carrier contract | P2 | S | closed |
| G-005 | missing feature | No physical Apple USB device is currently visible | fresh 2026-10-17 Windows limited probe: VID_05AC count=0, Apple Mobile Device Service Running/Automatic; go-ios and mobilecli device lists empty | Physical-device gate: USB + Trust + Developer Mode, then identity parity | P1 | M | open |
| G-006 | missing feature | No signed DeviceKit/WDA runner has been installed and accepted on a physical device | no P12/mobileprovision or installed runner evidence | Qualify DeviceKit 0.0.34 first; keep WDA only as independent fallback | P1 | M | open |
| G-007 | architecture | A second Windows-native iOS carrier was not yet bound through the same generic seam | current main binds mobilecli 1.0.20 and go-ios 1.3.2 through the same managed_equipment seam | Keep the generic seam; do not add a mobile-specific binding abstraction | P1 | S | done |
| G-008 | technology | go-ios 1.3.2 default DeviceKit download is 0.0.18, which is not the runner current mobilecli expects | mobilecli 1.0.20 exact VCS revision b8bd2f90 pins agentVersionIOS=0.0.34 and runner SHA-256 a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf; fresh official 0.0.34 runner download reproduced that digest and size 12,451,974 bytes | Pin the mobilecli-compatible 0.0.34 runner and pass it to go-ios with --path; never use go-ios default 0.0.18 for this route | P1 | S | contract-closed/device-open |
| G-009 | security | Apple signing inputs do not have a proven Windows Runtime credential authority | go-ios needs p12+mobileprovision or App Store Connect p8 inputs; Windows Runtime credentialAuthorities remains empty; Runtime credential-bound execution is Linux-only | Keep signing as an explicit bootstrap authority outside the normal Agent execution path; do not create a generic Windows secret broker unless repeated real-device bootstrap proves it is necessary | P1 | M | bounded-by-operator-input |
| G-010 | missing feature | Exact Windows-native carriers previously depended on manual live copies rather than a source-owned reconstructible transaction | current main contains one generic manifest/materializer for official go-ios ZIP and npm mobilecli TGZ with exact archive/member/executable digests, staging, fail-closed drift, source self-binding and receipts | Keep the generic native-tool-carrier seam | P1 | M | done |
| G-011 | provenance | mobilecli 1.0.20 registry binary is exact but its Go build metadata reports vcs.modified=true | npm registry integrity + local lock + tarball replay bind the binary; VCS revision b8bd2f90d2af74b2242f5da79e87055e4056d48d is observed but clean-tree reproducibility is not | Treat the registry binary as the current exact carrier while keeping clean-source reproducibility UNKNOWN | P2 | S | bounded-accepted |
| G-012 | missing feature | Source-owned carrier materialization is now in main, but no automatic operational convergence action invokes it | current main c3cf38199aacbd8867029bf90a230ad61122ecc0 contains the generic materializer; live carriers already exist under RuntimeCandidateR6/native-tools | Add only a narrow existing-operations invocation when recurring clean-node convergence is actually needed; do not create a mobile installer subsystem | P2 | M | open |
| G-013 | upstream defect | mobilecli 1.0.20 real-iOS agent installation is not a valid Windows bootstrap route | upstream issue mobile-next/mobilecli#380 is open; exact 1.0.20 utils/resign.go invokes macOS /usr/bin/security and codesign | Use go-ios 1.3.2 for Windows signing/install of the exact DeviceKit 0.0.34 IPA; use mobilecli after installation for agent status and high-level automation | P1 | S | workaround-selected |

What does not change:
- Runtime remains owner of Job/Attempt/execution truth.
- Workstation owns node-local desired state/materialization/binding only.
- Harness/domain code owns mobile task semantics and authorization.
- Device signing is bootstrap authority, not ordinary tap/screenshot authority.
- No new Mobile Runtime, workflow language, router ontology, generic mobile abstraction, or Windows-wide secret broker is introduced in this slice.
