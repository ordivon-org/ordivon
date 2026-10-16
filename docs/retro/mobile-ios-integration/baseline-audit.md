# Mobile iOS Integration Baseline Audit

Source cut: current isolated Workspace at 4a191669dc3bc24c0d876c633da585b75ce16e85.

Observed current-source baseline:
- No go-ios/mobilecli/Mobile MCP binding is present in current mainline Workstation source.
- Workstation declares Windows desired state through WinGet Configuration/DSC and exposes caller-selected exact bindings through tool_binding.py.
- Runtime's Windows env template deliberately restricts Ordivon executable admission to the materialized Runtime root rather than the whole C:\ProgramData\Ordivon tree.
- test_windows_runtime_service_materializer.py explicitly guards that restriction.
- managed_equipment currently resolves with pathlib.Path only and therefore has no Windows-native path projection.
- professional_software already has a Windows path projector, but does not encode an expected artifact digest in the declaration.

Observed live baseline:
- go-ios 1.3.2 source carrier exists at C:\ProgramData\Ordivon\Mobile\go-ios\v1.3.2\bin\ios.exe with SHA-256 c99b04f1d615fa716637efae457d5c554f32259f9d249375de0086e3cc1a1df5.
- The original Mobile root is outside Runtime executable admission and direct execution from there fails.
- Windows Runtime already has a versioned native-tools pattern and restrictive inherited ACLs.
- During this retro, the exact existing go-ios byte was copied to C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\go-ios\v1.3.2\ios.exe with the same SHA-256.
- A fresh direct Runtime limited-authority execution of that exact target returned go-ios version 1.3.2 with exit code 0.
- No physical USB Apple device is currently visible, so no device effect was attempted.

Baseline interpretation:
Executable materialization is now physically possible through the mature Runtime carrier tree. The remaining current-source repair is to express the exact node-local binding without inventing a new mobile subsystem.
