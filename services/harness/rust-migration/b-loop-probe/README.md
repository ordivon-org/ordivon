# Harness Rust migration: B turn-decision probe

SourceCut: c2ab551a4c858d8a960a117eba66a0d9d9310a6a

This is a non-production, pure Rust decision slice. It is not another live
Harness Kernel, Run Store or execution writer. Three exact Python sources:
- ordivon/turn_projection.py: select_turn_tool_working_set
- ordivon/run_contract.py: RunBudget.observation_gate_reason
- ordivon/run_recovery.py: observed names and progress counters only

The event-identity/search-subsumption scorer is NOT ported: the caller must
supply a previously verified new_evidence boolean. C must independently test
that source equivalence holds. The execution admission, PG and canonical data
contracts remain owned by A.

Run where Rust is installed:
cargo test --manifest-path services/harness/rust-migration/b-loop-probe/Cargo.toml

UNVERIFIED: Rust compile and test (no cargo/rustc on current Windows service
PATH), Python-oracle differential, PG admission, Provider response loss, Tool
receipt failure, consumer acceptance and deployed Linux/Windows behavior.

Next: wire this code only after A fixes exact Store/Lease/dispatch interfaces
and C supplies independent negative cases. Never dual-write one Run.
