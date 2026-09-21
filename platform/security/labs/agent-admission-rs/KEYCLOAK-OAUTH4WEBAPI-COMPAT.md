# Keycloak 26.7.4 / oauth4webapi 3.8.8 DPoP compatibility boundary

Status: **LAB-ONLY COMPATIBILITY SHIM — REMOVE WHEN UPSTREAMS CONVERGE**

## Problem

Keycloak 26.7.4 emits a DPoP-bound JWT access token whose `cnf` object contains
both:

```json
{
  "jkt": "<thumbprint>",
  "kc-jkt-type": "DPoP"
}
```

This is not inferred from documentation. The lab observes those exact two
members in a live token, and Keycloak 26.7.4 source sets both values in its
transient DPoP protocol mapper:

- `cnf.setKeyThumbprint(dPoP.getThumbprint())`
- `cnf.setJktType(DPOP_JKT_TYPE)`

The transient mapper is created internally and is documented by Keycloak as not
modifiable by administration users, so there is no supported client setting in
this path that removes only `kc-jkt-type` while retaining the DPoP access-token
binding.

Keycloak source authority:

- https://github.com/keycloak/keycloak/blob/26.7.4/services/src/main/java/org/keycloak/services/util/DPoPUtil.java
- https://www.keycloak.org/securing-apps/dpop

`oauth4webapi` 3.8.8 rejects a `cnf` object with more than one member before
running its normal DPoP validation. Therefore the unmodified Keycloak 26.7.4 /
oauth4webapi 3.8.8 pair is not interoperable for this Resource Server path.

## Standards basis for the narrow shim

RFC 9449 defines `cnf.jkt` as the DPoP JWK thumbprint confirmation method.
RFC 7800 section 3.1 explicitly permits other `cnf` members and says
confirmation members that are not understood must be ignored in the absence of
application-specific requirements.

As of 2026-09-21 the IANA JWT Confirmation Methods registry contains `jkt` but
does not register `kc-jkt-type`.

Authorities:

- https://www.rfc-editor.org/rfc/rfc9449.html#section-6.1
- https://www.rfc-editor.org/rfc/rfc7800.html#section-3.1
- https://www.iana.org/assignments/jwt/

## What the patch changes

`patches/oauth4webapi@3.8.8.patch` changes only the `cnf` member-cardinality
check.

It does **not** replace JWT signature validation or DPoP proof validation.

The compatibility rule is:

```text
if kc-jkt-type exists:
    require kc-jkt-type == "DPoP"
ignore kc-jkt-type only when counting confirmation methods
require exactly one remaining confirmation method
require that remaining method == "jkt"
continue through upstream JWT signature validation
continue through upstream DPoP proof validation
```

Therefore the shim does not admit another key-binding method and does not make a
non-DPoP token acceptable.

## Control evidence

On 2026-09-21 a controlled run temporarily restored the exact upstream
`oauth4webapi@3.8.8` `build/index.js` from its npm tarball while leaving all
other lab code unchanged.

Result:

```text
upstream has Keycloak shim? NO
first valid DPoP effect: expected HTTP 201, got 401
control process: non-zero as expected
```

After restoring the narrow patch, the same external pair passed the real E2E
matrix:

```text
missing DPoP proof                 -> 401
wrong DPoP key                    -> 401
new DPoP-authenticated R2 effect  -> 201
same DPoP proof replay            -> 401
fresh proof + exact effect replay -> 200
same effectId + changed payload   -> 409
R4 effect without Principal step-up -> 428
```

## Removal gate

Delete this patch immediately when any one of these becomes true:

1. Keycloak no longer emits `kc-jkt-type` for ordinary DPoP access tokens.
2. oauth4webapi natively accepts the Keycloak extension while preserving its
   normal DPoP checks.
3. The lab adopts another mature Resource Server verifier that supports the
   external token shape without Ordivon-owned cryptographic verification.

Every Keycloak or oauth4webapi version bump must rerun the real E2E and the
unpatched compatibility check before retaining this shim.

This patch is not production authorization to deploy the lab. It is evidence
that the current two mature upstreams have a narrowly characterized
interoperability mismatch.
