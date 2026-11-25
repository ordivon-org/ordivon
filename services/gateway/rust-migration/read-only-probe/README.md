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

## R13 protected read-only composition (Host #32753)

The independent fixture now exercises an authenticated client boundary, not
an authorization service. Operator-only commands:

    observe-protected-runtime-fixture <endpoint> <node> <credential-file> [auto|legacy]
    discover-protected-runtime-fixture <query-fixture> <endpoint> <node> <credential-file>

The original unauthenticated fixture remains for R11/R12 comparisons. Protected
commands never fall back to it. Endpoint qualification precedes credential
loading; a lexical miss skips credential loading and network observation.
The file adapter requires an absolute POSIX regular file with no group/world
permissions, uses O_NOFOLLOW and O_NONBLOCK, checks the same open descriptor
before/after a bounded 16 KiB read, and accepts RFC 6750 bearer syntax after
trimming ASCII surrounding whitespace. The credential directory is operator
trusted; this is not a sandbox, memory-zeroization proof, Windows ACL proof,
or acceptance of the full systemd credential permission contract. The token
is not a public tool argument; only a file path enters CLI arguments. The
fixture generates ephemeral synthetic credentials, never a production token.

rmcp owns the bearer header and protocol lifecycle; reqwest disables proxies,
redirects and HTTP retries. The network observation has the existing 3s
deadline and 1 MiB response bound; filesystem access is not part of the
network deadline. HTTP loopback here is only the isolated test carrier, not
an RFC6750 production TLS qualification. No Owner authentication grant,
Security PDP, public schema or installation is changed.

The independent Python MCP fixture rejects wrong credentials before business
dispatch. Tests assert zero network for invalid local credentials, zero
redirect-target request, exactly one business read when qualified, and no
synthetic token in subprocess stdout/stderr. Five additional composed
discovery cases cover positive/negative status, invalid authentication,
missing credential, and lexical miss. An authentication failure is
Unobserved, never proof of physical unavailability. Actual protected natural
Runtime, issuer/deployment identity, TLS or equivalent transport security,
Windows and systemd service credential acceptance remain separate gates.

References:
- https://systemd.io/CREDENTIALS/
- https://www.rfc-editor.org/info/rfc6750/
- https://docs.rs/rmcp/latest/rmcp/transport/streamable_http_client/struct.StreamableHttpClientTransportConfig.html
- https://github.com/modelcontextprotocol/rust-sdk/security/advisories/GHSA-9g45-5xwm-f3wc

## R14 test architecture and obligations (Host #32817 / #32824 / #32842)

The natural Owner owns the producer contract; Gateway owns its receiver
refinement, never physical readiness, authority or business completion.
Use the existing gateway:verify and gateway:formal:verify gates, not a second
test registry or scheduler. Each release claim binds exact source, toolchain,
test scope, positive/negative receipts and installed consumer separately.

| Logic / obligation | Capability / verification | Standing |
| --- | --- | --- |
| L01 route/catalog and L02 discovery | immutable metadata, proptest independent generator-labelled rank and limit oracle; Python differential, permutation and identity controls | bounded source |
| L03 readiness | generated version/booleans/unique inventory/context type; native TCP positive and malformed reports | bounded source |
| L04 binding and L05 ingress | existing Python public Action/Effect and actual SDK ingress tests; transfer obligations to native Rust | native implementation incomplete |
| L06 authorization, L07 endpoint/credential | independent Security producer + native protected TCP denial/redirect/no-secret controls | fixture only for Rust |
| L08 transport | rmcp modern/legacy, one exact business call, response bounds/timeout, explicit negative results | fixture only |
| L09 operation identity, L10 recovery | existing Runtime producer receipt and state semantics; model and generated fault traces; real accepted/observe/cancel/Artifact | native implementation incomplete |
| L11 projection, L12 error | exact Owner error, no success fabrication; Host Work historical absence and Topic cursor/epoch typed-error recipient required (Host #32826) | native Host recipient missing |
| L13 evidence, L14 evolution | OTel diagnostic not truth, exact ABI directional comparison, independent actual consumer canaries | production migration unqualified |

P0: each pure native boundary has independent domain-generated properties,
automatic shrinking and explicit malformed controls. Proptest is dev-only,
256 cases per property; default failure persistence remains enabled for real
regressions. Promote minimized genuine counterexamples as durable regression
tests. The previous full-sort comparator shares rank computation: keep it for
heap equivalence, not independent rank correctness. Generated rank labels
provide an independent narrow oracle; Python cross-language parity remains
a separate broader witness. No universal proof or performance claim.

P0: targeted mutation trials must compile and fail an actual assertion,
not be classified as killed by timeout, missing dependency or setup failure.
Use cargo-mutants when qualified; this runner currently lacks it, so the
bounded initial trial uses isolated temporary edits, disables persistence
only for deliberate mutants and restores source before final green. Test
selection and root required gates remain the Repo/Verification Owner's task.
No mutation tool is a production dependency or global requirement.

P1: add independent state-machine operation traces, exact typed error receiver
and real protected producer acceptance as the corresponding Rust adapters
arrive; keep existing TLA+ positive/negative checks and actual TCP fixtures.
P2: only retire old tests when their exact obligations and consumers are
covered by qualified native substitutes. Coverage is diagnostic, not a proof;
no automatic retries or skip-to-green. Installed/real Agent authorization
and deployment acceptance remain separate, not inferred from any fixture.

Upstream references: https://proptest-rs.github.io/proptest/ ;
https://mutants.rs/ ; https://github.com/modelcontextprotocol/rust-sdk .

## R15 temporal and protocol fault qualification (Host #32893)

Extend R14 independent point properties with a reference trace over eight
producer actions: ready, not-ready, malformed context, rotate credentials,
stale credentials, missing credentials, and a response replaced by HTTP 503
or 404 **after the independent Python SDK producer completed its tool call**.
The bounded sequence carrier accepts only "observe" on stdin, at most 256
requests, with one operator-provided loopback endpoint, node and credential
path for the entire process. It reuses the existing Rust recipient; no public
MCP tool, arbitrary dispatch, persistent credentials or production service.

The independent Python qualification covers every ordered pair of actions,
prefixing each pair with a ready observation. Each protocol mode therefore
has 192 transitions, 160 exact business calls and 32 response-fault
injections. Modern auto-negotiation and explicit legacy initialization have
separate real TCP traces. Credentials are rotated via atomic replacement;
the stale case supplies the actual previous token once rotation occurred.
The oracle is derived from the producer action, never the receiver result.
It checks outcome, exact business call count and version, no request for
missing credential, zero authenticated/business dispatch for stale token,
no re-negotiation/replay after dispatch, and no synthetic token in output.
A lost response must not be reported as a successful observation, even when
the producer completed the read. These are fixture-only bounded sequential
traces, not a proof about real effects, remote cancellation, concurrent
schedules or production authorization.

The existing gateway:verify native qualification runs the trace. Deliberate
compiled mutations in isolation must fail an assertion (not an environment
or compile failure): enable expired-session reinitialization, invent a
successful observation on transport failure, or cache a previous result.
Restore original source and run both traces again. No new test dependency
or root CI runner. Preserve native provider, installed versioned ABI and
actual Agent consumer evidence as separate release gates. Next: operation
identity/recovery reference model for actual Runtime effect receipt and
native Host typed-error receiver; test lost response, accepted receipt,
resolve by original key, cancellation and concurrent fault schedules as
those capabilities are implemented. Never use read-only fixture results as
evidence of effect-safe replay.
