# Mobile iOS Integration Target Design

## Target shape

Consumer/domain semantics
  -> existing Harness/Gateway execution seam
  -> Runtime execution.windows
  -> exact Workstation-bound Windows native tool
  -> go-ios / mature upstream runner
  -> physical Apple device

## This slice

Deepen the existing Workstation managed-equipment module rather than add a new mobile module.

Desired managed binding behavior:
1. A declaration names an exact executable, execution target, and expected SHA-256.
2. local_linux keeps the existing pathlib behavior.
3. windows_native reuses the existing Windows drive-path projection used by professional software.
4. Binding verifies exact bytes before returning AVAILABLE.
5. The binding remains non-semantic: no device authority, no task success, no Runtime admission claim.

go-ios is one adapter/materialization at this existing seam. No generic mobile interface is introduced until a second real device backend proves what actually varies.

## Carrier policy

Do not broaden Runtime to C:\ProgramData\Ordivon.
Use the already admitted, ACL-controlled, versioned native-tools subtree of the current Windows Runtime root.
The live candidate path is C:\ProgramData\Ordivon\RuntimeCandidateR6\native-tools\go-ios\v1.3.2\ios.exe.
Promotion/cutover path naming remains an operator/deployment concern and must not be inferred as a universal mobile abstraction.


## Provider roles after the second real adapter

- `mobilecli 1.0.20`: preferred high-level mobile automation provider candidate; standalone Windows executable; agent/device lifecycle surface.
- `go-ios 1.3.2`: low-level Apple transport, tunnel, pairing, signing, DeviceKit/WDA acquisition/install primitive and fallback.
- Workstation `managed_equipment`: exact executable/digest binding for both.
- Runtime `execution.windows`: execution truth for both.

This role split is evidence-driven, not a new routing ontology. A domain-level mobile capability is still deferred until real-device execution shows which operations actually need provider selection.


## Native-tool carrier realization

Two real Windows-native providers now justify one narrow realization seam. `native-tool-carriers.json` owns source/archive/member/executable/target commitments; `materialize-native-tool-carrier.ps1` owns the common staged transaction. Provider-specific mobile behavior is deliberately absent. Runtime remains the execution owner and the managed-equipment catalog remains the exact node-local binding projection.

The materializer is explicit rather than a new daemon or workflow system. Existing exact target bytes return unchanged without network access; mismatched versioned targets fail closed rather than being overwritten.
