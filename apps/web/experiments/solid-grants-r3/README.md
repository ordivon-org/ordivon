# Solid 2 / UI SDK Grant observation — R3 research candidate

This is an isolated, opt-in research consumer, not a production UI or an
installed/deployed capability. It uses the Web Owner's actual authenticated
GET /api/security/agents/grants with its additive principalId and observedAt
metadata. The server-rendered /operator/grants remains the baseline.
The only Agent action is a local filter. The test bridge is exposed on
window exclusively in the test build, not registered via WebMCP or routed
to any model. No Agent domain mutation or external credentials are added. R5 adds a human-only sign-out control using the existing native session endpoints.

## Reproduce

Use the existing Web mise pin, install Web and Security verifier dependencies
as in the normal Web verification, then from this directory:

    mise exec -- pnpm install --frozen-lockfile --ignore-scripts
    mise exec -- pnpm typecheck
    mise exec -- pnpm test
    mise exec -- pnpm build
    ORDIVON_WEB_CHROMIUM_EXECUTABLE=/absolute/path/to/chromium mise exec -- pnpm probe

The experiment uses its own package/lock/config; its release-age policy
is defined by pnpm-workspace.yaml, not the Web production package.
No package Agent skill was approved or activated. Review upstream code,
license, publishing provenance and dependency scope before production adoption.

Browser test creates a fresh in-memory WebStore with two Principals and
uses a seeded host-only cookie (not a claim of physical WebAuthn). It serves
built assets only within the disposable test Fastify process. It checks
actual owner data, foreign-row isolation, human and Agent filters, invalid
action denial, unchanged effect quota, and delayed old successful GET
after a newer denial. Browser tests use the actual route and a deliberately
held response, not a fake client-only response. R4 adds synthetic pagehide /
pageshow event interleavings and a browser-native back navigation after
server-side session revocation while the document is away. BFCache restoration
is reported independently through the trusted pageshow event. R5 additionally
uses two real browser tabs in the same storage partition and the existing
CSRF + POST /api/session/logout routes. It holds a real prior authorized GET
until logout has completed, then verifies the peer's invalidation fence.
A second test commits logout once but discards its response; the sender
reports unknown rather than success/retry, while a fresh owner GET denies.

## Reconciliation

Every refresh clears visible data and increments a request generation.
Only one settlement of the current loading generation is accepted.
Denied/unavailable observations retain no rows. On pagehide or hidden
visibility, the generation is invalidated and visible rows/filter cleared.
On restoration/visibility return, fetch a new owner observation; a late
response from the earlier page lifecycle cannot settle. Identity can change
between observations, and a new page observation does not rely on a
browser-provided identity claim. This does not mean that a
browser can guarantee continuous revocation visibility without a new owner
observation, nor is generation a server revision or authority token.
The read projection retains only fields used by this consumer.
No durable client cache; no effect admission logic.

R7 native Solid 2.0.3 probe (Node browser export, synthetic values) directly
compares async createMemo and createDeferred. Both suppress a late older
completion after a newer denial; both also retain the earlier settled answer
during refetch, including latest(), while isPending() is true. That retention
is useful for ordinary non-sensitive content but cannot replace this
consumer's immediate lifecycle/identity invalidation. Keep the small explicit
generation transition; no extra Query/cache package is justified here.
Run the pinned native witness with pnpm probe:native-async. This is a native
reactive observation, not browser authorization proof or a requirement on
future Solid versions. See Solid's createDeferred and Loading documentation:
https://docs.solidjs.com/reference/solid-js/reactivity/create-deferred/
https://docs.solidjs.com/reference/solid-js/components-jsx/loading/

The browser probe also checks the named combobox, listbox and five options,
keyboard opening/selection, Escape close and focus restoration, and actual
table row changes. This tests a subset of the WAI-ARIA combobox pattern, not
a full accessibility or screen-reader conformance audit:
https://www.w3.org/WAI/ARIA/apg/patterns/combobox/

A same-origin BroadcastChannel carries only the literal session-changed hint
after a human sign-out attempt (including response loss). It cannot carry
identity, authorization, or business state. Recipients clear rows and pending
generations, without claiming logout or automatically fetching. An unsolicited
hint cannot prevent the next authenticated owner observation. The sender
clears data before logout; only the native positive receipt confirms logout.
The channel closes on pagehide and reopens on pageshow, preserving the
tested BFCache path. Do not poll authenticated GETs: they extend the owner
idle deadline. This is not a continuous revocation guarantee, a cross-browser
notification service, or protection against arbitrary same-origin script
execution. An unobserved remote revocation still requires an owner read.

## Bounded model

ObservationGenerationR1 models at most three generation advances (including
suspend/resume/peer hint) and three response outcomes. TLC safe configuration checks
five semantic invariants; three legacy configs demonstrate denial resurrection,
hidden-page restoration and peer-hint resurrection. Four reach configs check
observed/denied/suspended/hinted remain reachable. The hint model checks the
receiver fence, not logout transport, message delivery or authentication. Duplicate-completion and wire
validation are covered by native TypeScript tests. Model proof is not a
source-refinement or distributed authentication proof.

Use the existing pinned TLC 1.7.4 JAR and its expected SHA256 supplied by
the root toolchain composition. Run all seven expected negative/reachability
controls as well as the safe model; temporary state is removed automatically:

    ORDIVON_TLA_TOOLS_JAR=/absolute/path/to/tla2tools.jar \
      ORDIVON_TLA_TOOLS_SHA256=<locked-sha256> bash formal/check.sh

## Remaining qualification

Independent review, identity changes/revocation outside the cooperating same-origin tabs (without a new observation),
production supply-chain admission, explicit operator authentication flow,
native installed owner/API access, usability/accessibility and end-to-end
performance remain unqualified. No production install or release.
