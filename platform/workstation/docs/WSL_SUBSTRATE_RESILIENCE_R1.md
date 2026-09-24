# WSL Substrate Resilience R1

Status: production-minimum candidate for WR01-WR06.

## Problem boundary

WSL VM/process liveness is not equivalent to fresh-session admission liveness. A long-lived WSL2 VM can retain existing sessions while new `wsl.exe` sessions and Windows interop fail. The local 2026-09-24 incident showed high-order page allocation failures in the VMBus/vsock path while aggregate memory remained available.

This package does not own Linux MM, Hyper-V/VMBus allocation, WSL/HCS lifecycle, scheduling, or semantic task completion. It owns only thin observation, evidence, deterministic diagnosis, one bounded Linux-MM recovery effect, and requalification.

## LEGO circuit

1. **WR01 Fresh Session Probe** — Windows `WindowsWslProvider.ps1 -Command admission-probe` starts a bounded fresh `wsl.exe` session and requires exact marker output.
2. **WR02 Linux Physiology Snapshot** — `wsl_substrate_resilience.py snapshot` captures buddy topology, pagetypeinfo, meminfo, VM compaction/reclaim counters, memory PSI, relevant VM sysctls, and bounded kernel warning evidence.
3. **WR03 Failure Classifier** — `classify` emits `HEALTHY`, high-confidence `F1_HIGH_ORDER_FRAGMENTATION`, or `UNKNOWN`. The wider F1-F5 vocabulary is declared, but R1 refuses to guess F2-F5 without stronger evidence.
4. **WR04 Fragmentation Recovery** — `compact` accepts only an exact digest-bound classification file whose class is high-confidence F1 and whose recommended effect is `compact_memory`. It performs one write of `1` to `/proc/sys/vm/compact_memory` and records before/after evidence. It never writes `drop_caches` or persistent sysctls.
5. **WR05 Lifecycle Recovery Route** — non-F1 failures are not mutated by this provider. `UNKNOWN` routes to additional Windows/WSL forensics; owner-native WSL lifecycle recovery remains a separate Windows authority/effect.
6. **WR06 Requalification** — after any recovery, run a new Windows admission probe and pass that receipt to `requalify`; recovery is confirmed only when fresh admission succeeds and Runtime/Host/Gateway are active.

## Truth separation

- process/service liveness is not admission liveness;
- an error string such as `accept4 failed 110` is observation, not diagnosis;
- Linux physiology is evidence, not authority to perform a Windows lifecycle effect;
- `compact_memory` returning successfully is effect execution, not recovery proof;
- only a post-effect fresh-session probe plus control-plane requalification can confirm recovery.

## Explicitly rejected

- periodic or routine `drop_caches`;
- blind `accept4 failed 110 -> compact_memory` mapping;
- permanent `vm.compaction_proactiveness`, `defrag_mode`, or `min_free_kbytes` changes without controlled experiments;
- custom memory manager, watchdog daemon, scheduler, event bus, or database;
- hiding UNKNOWN behind an arbitrary recovery action.

## Research lane, not production R1

Persistent compaction/defragmentation tuning belongs to controlled workload experiments. The long-term structural solution belongs upstream in Linux Hyper-V/VMBus, where fragmentation-tolerant buffer allocation can remove the fragile high-order contiguous-page prerequisite. When an upstream ring-buffer fix reaches a WSL kernel used locally, validate it A/B and delete mitigation that is no longer necessary.
