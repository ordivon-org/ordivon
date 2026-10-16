# Mobile iOS Integration Slice Verification

Original qualification base: 4a191669dc3bc24c0d876c633da585b75ce16e85.
Current integrated main: c3cf38199aacbd8867029bf90a230ad61122ecc0.

## TDD evidence

RED:
- managed Windows binding test failed because resolve_managed had no Windows mount projection.
- go-ios catalog test failed because no exact managed binding existed.

GREEN:
- focused new tests passed after the minimal implementation.
- related binding suite: 11/11 PASS after adversarial negatives.
- Ruff on changed Python: PASS.
- git diff --check: PASS.

Adversarial controls:
- wrong Windows managed-equipment digest fails closed.
- unknown managed execution target fails closed.
- existing Linux managed-equipment compatibility remains green.

## Owner-native verification

Fresh mise run workstation:ci: PASS.
Fresh final mise run workstation:verify: PASS after all test changes.

## Live Runtime evidence

Exact carrier:
C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\go-ios\v1.3.2\ios.exe

SHA-256:
c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5

Runtime service access is ReadAndExecute; SYSTEM and Administrators retain FullControl.

Direct Windows Runtime execution without a PowerShell child wrapper:
- ios.exe --version under limited authority: exit 0, version 1.3.2.
- ios.exe list under limited authority: exit 0, deviceList empty.

The empty list matches fresh PnP observation: no Apple USB VID_05AC device. No device effect was attempted.

## Explicit non-closure

- go-ios v1.3.2 release-byte provenance is now closed: GitHub Release API advertises `go-ios-win.zip` SHA-256 `939c6bcaafed183a92afb9f79cc11b1f935fa6389bfc94d3902e3f52c4dff3fe`; the retained local archive has that exact digest and replays `ios.exe` SHA-256 `c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5`, matching the original and admitted Runtime carrier.
- No physical Apple USB device, tunnel, signing authority, DeviceKit, or WDA E2E is qualified.
- RuntimeCandidateR6 is a current node-local realization name, not a permanent architecture contract.


## Second real provider — mobilecli

Observed installed standalone binary:
`C:\ProgramData\Ordivon\Mobile\mobile-mcp\1.0.11\node_modules\@mobilenext\mobilecli-windows-amd64\mobilecli-windows-amd64.exe`

Package version: `1.0.20`
SHA-256: `018dcec38ee4f39ef24fd0987d85e04914294651b8da770c647f21ca04029aa4`

Digest-fenced Runtime carrier:
`C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\mobilecli\v1.0.20\mobilecli.exe`

Direct Windows Runtime limited-authority execution:
- `--version`: exit 0, mobilecli 1.0.20.
- `devices --include-offline --platform ios`: exit 0, empty device list.

TDD for the second provider produced a catalog-only RED/Green cycle: the generic Windows managed-equipment seam required no further code change. This is evidence that the existing generic seam is carrying two real providers without a mobile-specific abstraction.

A fresh full `mise run workstation:verify` passed after the mobilecli binding was added.

## Runner-selection finding

`go-ios ui download devicekit` under direct limited Runtime authority successfully downloaded `devicekit-ios-runner-0.0.18.ipa` (8,920,427 bytes; SHA-256 `45457d3f11de2b5370b14ba45e6c8502328e28825ee8222e8517245898a4c57f`) from deviceboxhq.com. The artifact is download evidence only: it was not signed, installed, trusted, or executed. Current Mobile Next history shows later DeviceKit integration/fixes, so 0.0.18 is not promoted as the preferred runner.


## Generic Windows native-tool carrier materializer

Current main contains:
- `workstation/windows/native-tool-carriers.json`
- `workstation/windows/materialize-native-tool-carrier.ps1`
- `tests/test_windows_native_tool_carrier.py`

The module is intentionally non-mobile. It owns only URL -> exact archive digest -> exact archive member -> exact executable SHA-256 -> versioned `native-tools` target. The manifest currently has two real adapters: official go-ios v1.3.2 GitHub ZIP and npm mobilecli 1.0.20 TGZ. Manifest target/digest values are parity-tested against `software.toml`.

Final qualification source digests:
- materializer SHA-256: `44eeee87267b210c925fd6402b39a8602a75c1cb6f3210d5d92d403d4b8c6096`
- contract SHA-256: `c46574c0213fcdbc540b1c4f4b0d3fbc9d1dc70fe566ea55162b92b9af927262`

Live falsification on the Windows Runtime candidate proved:
- retained go-ios official ZIP -> materialized target -> direct Runtime limited `--version`;
- second invocation is idempotent and does not re-read the archive;
- pre-existing wrong target fails with exit 2 and is not overwritten;
- `..\escape.exe` contract target fails before extraction;
- mobilecli downloads over real HTTPS from npm, verifies SHA-512, extracts exactly one member, verifies executable SHA-256, materializes, and direct Runtime limited `--version` returns 1.0.20;
- PowerShell AST parser reports 0 syntax errors;
- stdout is one JSON receipt only;
- receipt self-binds `materializerSha256` and `contractSha256`;
- first materialization reports `archiveVerified=true`; unchanged replay reports `archiveVerified=false`;
- receipt explicitly does not claim Runtime admission, task authorization, or domain success.

Fresh `mise run workstation:verify` passed after the materializer and its tests were added.

## mobilecli provenance boundary

Npm registry reports `@mobilenext/mobilecli-windows-amd64@1.0.20` as latest, published 2026-10-14. Local package-lock tarball URL/integrity matches registry. A fresh `npm pack` reproduced the registry SHA-512 integrity and the tarball executable SHA-256 exactly matches the admitted Runtime carrier. Go build metadata names VCS revision `b8bd2f90d2af74b2242f5da79e87055e4056d48d` but also reports `vcs.modified=true`; therefore exact registry-binary provenance is established while clean-source reproducibility remains UNKNOWN.

## Current-main integration and remaining non-closure

The exact source candidate was replayed onto fresh main ffd2f37b0f24776d17e8b423a7e31e22eba59490, reverified, committed as c3cf38199aacbd8867029bf90a230ad61122ecc0, and integrated through tools/repo/migration/integrate-main.sh with EXPECTED_MAIN=ffd2f37b0f24776d17e8b423a7e31e22eba59490. Integration was FAST_FORWARD. Fresh post-integration repo:primary:verify reported PASS with physical primary HEAD == refs/heads/main == c3cf38199aacbd8867029bf90a230ad61122ecc0 and a clean primary worktree.

Fresh current-node Runtime evidence after integration:
- direct limited go-ios --version: exit 0, 1.3.2;
- direct limited go-ios list: exit 0, empty deviceList;
- direct limited mobilecli --version: exit 0, 1.0.20;
- direct limited mobilecli devices --include-offline --platform ios: exit 0, empty device list;
- Windows limited PnP census: VID_05AC count 0;
- Apple Mobile Device Service: Running, Automatic.

The source-owned materializer is therefore mainline, but it is not yet an automatic operational converge action. That remaining automation is not a mobile-specific subsystem requirement: add only a narrow invocation through an existing operations lane if recurring clean-node convergence actually needs it.

Physical-device closure remains open: no USB-present Apple device, tunnel, signing authority, DeviceKit/WDA runner install, UI action E2E, or reconnect/recovery qualification has been proven.

## Repository-wide gate note

Fresh mise run repo:ci on both the exact mobile candidate and the unmodified ffd2f37b base fails at the same pre-existing retirement-policy check: docs/superpowers/plans/2026-10-17-oss-contribution-operating-profile-r1.md is forbidden by next-monorepo-archive. The candidate does not touch that path. Workstation owner-native verification remains green; this repository-wide baseline drift is tracked separately and must not be misreported as a mobile regression.


## DeviceKit 0.0.34 compatibility closure

Fresh 2026-10-17 evidence tightened the runner contract from "current DeviceKit" to one exact artifact.

mobilecli 1.0.20:
- registry carrier SHA-256: `018dcec38ee4f39ef24fd0987d85e04914294651b8da770c647f21ca04029aa4`;
- build VCS revision: `b8bd2f90d2af74b2242f5da79e87055e4056d48d`;
- exact `commands/agent.go` at that revision pins `agentVersionIOS = "0.0.34"`;
- exact runner filename: `devicekit-ios-runner.ipa`;
- pinned runner SHA-256: `a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf`;
- installed runner lookup accepts a re-signed bundle by suffix, so team-prefix rewriting does not break discovery.

Fresh official release replay:
- URL: `https://github.com/mobile-next/devicekit-ios/releases/download/0.0.34/devicekit-ios-runner.ipa`;
- observed size: 12,451,974 bytes;
- observed SHA-256: `a39446db09d998289bd2f0821870bb5d9a73330a9f2a3f1f67546b2dd69370bf`;
- observed digest exactly equals mobilecli 1.0.20's pinned checksum.

Therefore the old go-ios default DeviceKit 0.0.18 download is not the selected runner for the mobilecli route. The compatible runner contract is DeviceKit iOS 0.0.34.

## Windows bootstrap currentness

mobilecli 1.0.20 documents real-iOS agent installation, but its exact `utils/resign.go` still resolves signing identity through `/usr/bin/security` and signs with `codesign`. Upstream issue `mobile-next/mobilecli#380` remains open for Windows real-device agent installation.

Local go-ios 1.3.2 help independently proves a Windows-native replacement path:
- `ios ui install (wda | devicekit) --p12file=<p12file> --profile=<mobileprovision> --path=<ipaOrZipOrApp>`;
- `ios sign app --path=<ipaOrAppFolder> --p12file=<p12file> --profile=<mobileprovision>`;
- `ios sign provision appstoreconnect ... --asc-private-key=<p8file> ...`.

No signing command was executed because no physical Apple USB device or approved signing authority is present. This is an explicit non-claim.

## Fresh physical boundary

A fresh Windows Runtime limited probe after the runner analysis still reported:
- Apple USB VID_05AC present count: 0;
- Apple Mobile Device Service: Running / Automatic.

No tunnel, signing, install, UI effect, or recovery effect was attempted.
