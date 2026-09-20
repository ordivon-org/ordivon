# Artifact E2E — Web Archive Family R1

## Standing

`SHADOW_PROFILE_LIVE_PROVEN`

Web Archive R1 proves one bounded ISO 28500:2017 WARC/1.1 HTTP response capture. It deliberately does not claim complete-site capture or replay fidelity.

## Profile

`web-archive-warc-response-r1`

The object contains exactly one uncompressed WARC/1.1 `response` record with exact target URI, capture date, record ID, HTTP status/content type and payload SHA-256.

## Evidence topology

- `warcio 1.8.1 check` validates stored WARC payload/block digests;
- Python warcio independently exposes record/capture facts;
- Node warcio.js 2.4.12 independently exposes the same facts and decoded payload bytes;
- the object contract binds the expected capture semantics.

Both parser views agree exactly on the live smoke record, including payload SHA-256.

## Capability binding

Python warcio 1.8.1 is installed as a relocatable `--target` carrier at `/opt/ordivon/external/warcio-py/1.8.1`. An initial moved-venv carrier failed because its CLI shebang retained a `/tmp` interpreter path; that carrier was rejected and replaced rather than patched in place.

Node warcio.js 2.4.12 is frozen at `/opt/ordivon/external/warcio-js/2.4.12` with package-lock identity.

## Live proof

Runtime job: `job-01a0962a-2971-76e1-87ba-48627d054292`

Exact WARC:

- size: 519 bytes;
- SHA-256: `8ee5c7be3e806e18f266346dbcfd03618bd55898e5f3a521d916d127f8e2c356`;
- contract canonical digest: `a07d75dac4d47241ccf86f65f4206cf5634b4bc39bbe6a3e10b1dc4c72d26212`;
- payload SHA-256: `e16b28b7a997b1cfa6288bbc31491580ebc750f7381731aaafe4bd74c10c040b`.

## Falsifiers

Seven focused tests pass:

1. exact WARC/1.1 response + matching contract → PASS;
2. valid WARC but wrong target URI contract → FAIL;
3. valid WARC/1.0 → digest integrity PASS but R1 profile FAIL;
4. valid WARC with an extra response record → integrity PASS but single-record profile FAIL;
5. payload byte corruption → digest checker FAIL;
6. both parsers agree on payload, but contract expects a different payload digest → FAIL;
7. frozen parser-carrier identities match.

Therefore:

```text
WARCIntegrity != CaptureContractSatisfied
ParserAgreement != ExpectedCaptureIdentity
```

## Boundary

R1 does not prove browser DOM state, JavaScript/network dependency completeness, crawl completeness, replay fidelity, legal/policy compliance, WACZ packaging or CDX indexing.
