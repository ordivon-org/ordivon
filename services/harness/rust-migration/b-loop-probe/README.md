# Harness Rust migration: B pure turn-decision / evidence probe

## Source and current scope

This is an isolated, non-production Rust migration slice. It is NOT a
Harness Run writer, Provider dispatcher, Runtime client, or second authority.

Python source oracle: ordivon/turn_projection.py, run_contract.py,
run_recovery.py. Base c7bbeed016be16f4860fec4ba069f3ee0cb11932;
continuation from prior B commit 8d034f2d18c24e81c23a522af203849f739c69fe.

Implemented in pure Rust:
- Admitted Tool presentation subset and duplicate/outside selection rejection.
- Observation signatures and Search result/outcome sets (validated input identity).
- Python lexical path subsumption, not filesystem resolution.
- UNKNOWN, rejected, cancelled and cancel-requested observations do not
  manufacture new evidence or claimed action progress.
- Continuous no-progress / observation-only counters and gate precedence.
- Combined evaluate_turn transition from prior evidence and budget to next
  state, without external physical effect.

The native Python source-oracle tests invoke existing Python implementations,
not independently transcribed formulas. Qualification includes 400 Tool
selection / RunBudget Gate inputs and 640 stateful evidence/search-subsumption/
progress/gate transitions through native AgentToolCall,
HarnessToolObservation, _advance_turn_evidence, and
RunBudget.observation_gate_reason. Rust unit tests cover boundary cases.

The earlier Rust u64 saturating_add behavior was removed. ProgressError now
explicitly rejects integer overflow rather than silently changing the
observable Python arithmetic semantics. Unrepresentable legacy Contract
budget inputs must be rejected by a future typed adapter, not truncated.

## Commands

  CARGO_TARGET_DIR=/tmp/ordivon-harness-b-evidence-test cargo test --offline --all-targets --manifest-path services/harness/rust-migration/b-loop-probe/Cargo.toml
  cargo fmt --check --manifest-path services/harness/rust-migration/b-loop-probe/Cargo.toml
  CARGO_TARGET_DIR=/tmp/ordivon-harness-b-evidence-test cargo clippy --offline --all-targets --manifest-path services/harness/rust-migration/b-loop-probe/Cargo.toml -- -D warnings

## Explicit unproven claims

- Rust B does not independently parse/authenticate observation content or
  compute Canonical digests: the source Oracle supplies presealed evidence
  signatures and search units. A owns the proposed Canonical/PG library.
  A caller must never treat unchecked digest strings as evidence.
- No PG read/write/Lease, Provider dispatch/fence/receipt, Runtime Tool
  effect, crash/recovery or deployed consumer verified in this slice.
- Python permits integer values exceeding Rust u64; Rust must reject those
  during Contract hydration. A bounded corpus is not full-domain equivalence.
- No migration of model lifecycle, Tool Program, complete WorkingView or
  Provider-native continuation; no second Scheduler/Registry.

Next: after A and C review, integrate existing A canonical and durable PG
ports, then build a no-Tool Rust Provider Run with real receipt-loss and
reconciliation negative cases. Historical H3/H4/H5 evidence does not prove
current deployed consumer parity.
