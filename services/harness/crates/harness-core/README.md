# Ordivon Harness Rust core — Canonical JSON compatibility slice

**Status: experimental, not a production writer or a complete Harness.**

This crate tests byte-level compatibility with the existing Python
services/harness/src/anc_canonical/canonical.py representation and sha256:
digest format. It does not implement the PG Journal, Run leases, Agent Loop,
Tool dispatch, Provider effects, or any deployed consumer.

Current surface: strict JSON parse; sealed validated document; deterministic
Python-style JSON UTF-8 bytes; SHA-256 digest. Integer data uses decimal text
rather than silently narrowing to i64, u64 or floating point.

The committed fixture was produced with Python 3.15.1 by directly invoking
anc_canonical.loads_strict, canonical_bytes, and canonical_digest.
It contains 38 input vectors, including 19 accepted byte/digest fixtures and
19 rejected inputs. Offline Cargo tests verify the frozen oracle.

Run: CARGO_TARGET_DIR=/tmp/ordivon-harness-rust-core cargo test --offline
--manifest-path services/harness/crates/harness-core/Cargo.toml

Known limits / pending independent falsification:

- The parser bounds nesting to 512. Python's runtime recursion limit and
  configured maximum decimal integer digits may differ between deployments.
- The Rust contract currently fixes the observed Python 3.15.1 default
  integer digit limit of 4300; changes to Python settings are not modeled.
- Cross-language parity is established only for the included inputs. Wider
  fuzzing, arbitrary legacy PG BYTEA readback, source schema compatibility,
  privacy, lease/fencing, recovery, and consumer acceptance are UNKNOWN.
- This format is not RFC 8785/JCS. Do not silently change the object
  digest or run identity by substituting another JSON canonicalizer.
- This package makes no side-effect request. Python and Rust must never
  operate as simultaneous writers of the same Harness Run.

Collaboration: A owns the semantic/PG port; B owns Loop/Provider/Tool
integration; C owns independent legacy-consumer and failure-case acceptance.
The Host coordination Work is work:ordivon:harness-rust-migration-r1:20261110.
