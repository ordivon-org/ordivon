# Gateway live Host denial and Cloudflare trusted operator profile (R34)

Date: 2026-11-19. A genuine client-path failure, not a fabricated NO_GO.

## Actual counterexample

Frozen Gateway 0.10.17 successfully passed 702 Gateway tests,
440 monorepo tests, official installed MCP SDK verification,
a real service-user preflight, and native public ABI comparison
against the 0.10.12 installed Gateway.

The Gateway 0.10.17 release was briefly activated. Its local /health
returned 200, unauthenticated MCP requests returned 403, public
system.describe returned 0.10.17, and live Linux/Windows execution
discovery returned ready. However, a real authenticated ChatGPT to
Gateway host.status call failed with Security denied capability:
authzen-deny. The same call had succeeded on 0.10.12.

Gateway was immediately rolled back to the prior frozen 0.10.12
release and the same live authenticated Host status read succeeded
again. A successful source test or symlink update was insufficient to
declare an Agent consumer release successful.

## Root cause and minimal correction

Cloudflare Access had already verified the app JWT signature (RS256),
key id/JWKS, issuer, audience, expiry and principal. Gateway then
required a separate AuthZEN object-by-object grant for ordinary Host
status and Work/Message calls. That second PDP did not have the same
trusted operator principal and incorrectly denied legitimate work.

Gateway now has one EXPLICIT opt-in operator mode:

    ORDIVON_GATEWAY_TRUSTED_CF_OPERATOR=true

The option is consumed ONLY by the Security package. It requires
ORDIVON_GATEWAY_TRUST_CF_ACCESS=true and an existing HTTPS issuer
and configured audience; no key or password is exposed or copied.

Only CloudflareAccessMiddleware, after the real JWT verifier succeeds,
can write request-local state marker
ordivon_access_verified_by_gateway=cloudflare_access_jwt.
The Security PEP checks that exact marker and an issuer-bound
qualified sha256 principal. A verified operator therefore goes
straight to the natural Host/Runtime Owner, not to a redundant
per-object AuthZEN call. Target shape and Owner-side constraints
still apply; no invented Host Actor, Runtime result or Artifact truth.

A loopback Harness service bearer is deliberately labeled
local_service_bearer, never cloudflare_access_jwt, and still uses its
previous PDP. Missing or forged identities and non-Cloudflare
requests are not granted operator trust. The Runtime native release
tool retains authenticated HTTP and native Owner ReleaseEffect
admission constraints, without a second PDP for this opted-in operator.

## Scope and risk boundary

This mode makes verified principals admitted through the Cloudflare
Access application trusted operators. It is appropriate only if that
app's Access policy deliberately allows the desired human/service
operators. If the same Access app later admits untrusted or differently
privileged tenants, this mode must be disabled or the app policy
segmented; Gateway does not pretend there is an independent per-object
authorization layer in this single-operator deployment.

The default without explicit enablement remains the previous
AuthZEN behavior. All policy composition stays under security/.
No business module decides whether an Actor has a Security grant.

## Verification

Tests cover native signed RS256 human Access JWT and service-client
App JWT, invalid issuer/audience/signature/absence; genuine
Cloudflare ingress -> Security PEP -> Host handler;
local Harness bearer, forged Tool arguments, absent JWT marker,
wrong Principal shape, disabled mode, malformed resource targets
and Runtime release identity constraints.

This update changes package version to 0.10.18, keeps surfaceEpoch17,
42 tools and the exact same MCP SDK input/output schemas as 0.10.17.
The original 41 Tool schemas remain the same as 0.10.15.
Source tests and actual installed client readback are independent facts.
