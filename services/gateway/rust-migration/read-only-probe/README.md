# Gateway Rust read-only refinement probe

A bounded G01d/G05a/G08 candidate, not a second production Gateway. No
production Owner credentials, authorization, Job creation or deployment.
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

The existing `mise run gateway:verify` queue runs these native Rust and Python
qualification steps; a missing compiler or failed probe is not a skipped test.


## R11 native Owner observation refinement (Host #32664)

The direction is pure typed logic -> real SDK adapter -> protected Owner
consumer -> native public tool surface -> staged replacement of Python.
Python remains an independent behavioral oracle during migration. This
stage does not claim authenticated production use or a complete native ABI.

The operator-only command `observe-runtime-fixture <endpoint> <node> [auto|legacy]`
is a bounded loopback qualification carrier, not a public MCP tool. The
endpoint must be explicit IPv4 loopback HTTP /mcp with a port, no userinfo,
query or fragment. reqwest is configured without proxies, redirects or HTTP
retry; rmcp is configured without expired-session replay, with 1 MiB JSON
and SSE event bounds. Auto negotiation and explicit legacy initialization
are separate modes. The outer three-second observation window includes
negotiation, the one exact runtime.describe(schemaVersion=1) call, and SDK
cleanup; it is not proof of remote cancellation or a hard real-time bound.

`Observation::Reported` preserves strict configured/available booleans
only after exact expected node, native Linux, version and complete unique
target inventory qualification. `Unobserved` is not a negative physical
readiness result. No arbitrary text fallback or whole-schema proof is
claimed. No token is read or forwarded. Production Linux route declares a
bearer and is deliberately not exercised by this unauthenticated fixture.

`qualify_owner.py` uses the independent Python MCP SDK with actual TCP:
modern and legacy lifecycle, exact business request count, valid true/false,
wrong version/node, duplicate/contradictory/ill-typed inventory, absent
target, tool error, text-only result, timeout and oversized response.
The existing Gateway queue runs this alongside the earlier native server
and pure differential checks. Next: producer-owned credential and endpoint
adapter, qualified Runtime output contract, protected real recipient,
versioned public discovery surface, then effect identity/recovery and
consumer migration. No new authority or generic effect transport.

## R12 compiled index and native discovery composition (Host #32701)

The native search batch compiles immutable complete metadata once, validates
unique capability identities and the exact ordered identity of every
request-local observation vector, then uses a bounded standard BinaryHeap for
the best K matches while counting all matches. Equal rank/name uses source
position as the final tie breaker. This is O(M log K) ranking (for K >= 2),
O(K) retained rank entries, not a bound on the metadata or batch input size.
UNKNOWN observations remain eligible when known-unavailable items are filtered.
No observation or grant is cached. The single-query evaluator and batch
qualifier share the same ranking implementation.

The operator-only discover-runtime-fixture command composes this plan with
the R11 native MCP adapter for the single execution.linux metadata fixture.
A lexical miss makes zero Owner RPCs. A match makes exactly one business
runtime.describe call and projects fresh reported or unobserved evidence.
It rejects other route identities and invalid query bounds. This does not
provide a production endpoint or a full capability.search ABI; the Owner is
an independent loopback SDK fixture, not an authenticated production Runtime.
No credential or authority has been added.

The existing qualify.py compares 1,044 real Python search results in both
single and compiled batch modes, plus identity and changing-observation
controls. Rust tests independently compare 252 cases against the former full
sort. qualify_owner.py covers five composition scenarios, including a zero-RPC
miss. The optional local debug benchmark uses seven alternating samples at
19 and 1,900 synthetic metadata rows; it is not a timing gate or a production
end-to-end benchmark.
