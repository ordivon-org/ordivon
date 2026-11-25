# Gateway Rust read-only refinement probe

A bounded G01d/G05a candidate, not a second production Gateway. No Owner
network client, authorization, credential handling, Job creation or deployment.
The canonical Python Gateway at the checked-out SourceCut generates the route
fixture and its actual public system.describe tool schema; Rust independently
computes the description and exposes it via the native rmcp/Axum HTTP carrier.
Copied test-fixture schema is not independently derived Rust ABI proof.

From the repository root:

    cargo build --locked --manifest-path services/gateway/rust-migration/read-only-probe/Cargo.toml
    uv run --locked --project services/gateway python services/gateway/rust-migration/read-only-probe/qualify.py

The qualifier uses Python's actual GatewayService, route table, status and
reference functions, and actual MCP SDK. It checks configured-bit combinations,
malformed and contradictory inventories, exact route digest, and the only
exposed tool over modern and legacy MCP protocol modes. It starts only an
ephemeral loopback listener and terminates it before exit. The binary can also
be passed explicitly as the script's first argument.

Acceptance: exact finite differential equality and schema/result equality for
one read-only tool; no Owner effects. Full 42-tool ABI, discovery, authentication,
PEP/PDP, recovery, actual consumers, installation and performance remain
unqualified. Do not add this probe to production service configuration.

R4 extends the pure offline evaluator with lexical matching/ranking over supplied
metadata and observations, not a production capability.search endpoint. It
uses ICU4X full default case folding and the existing ASCII token contract.
The ICU range excludes 2.4 until Python's Unicode contract advances: ICU 2.4.0
changed 21 scalar folds relative to Python Unicode 17. The qualifier checks all
1,112,064 Unicode scalars against the actual Python interpreter, then compares
ranking/filtering/limits against the public Python Gateway using deterministic
read-only Owner fixtures. This is not a full Rust readiness/Owner adapter.
