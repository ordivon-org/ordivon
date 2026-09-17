# Browser Security Witness Source R1

Status: **neutral/read-only Harness observation adapter**

## Purpose

Harness owns browser/provider observation. Security-v2 owns canonicalization, sensitive-field rejection, observation digests, bundle validation, and drift comparison.

This adapter emits the source-manifest shape accepted by Security-v2; it does not import Security-v2 and does not make Security an execution authority.

```text
Harness / Network observation authority
        -> Browser Security source manifest
Security-v2 canonicalization authority
        -> canonical witness bundle
Security-v2 comparison
        -> infrastructure / detector / subject drift
```

## Non-provider experiment boundary

The default collector does **not** visit ChatGPT or another protected provider, does not interact with a challenge, and does not cross SEND. Its `challengeStanding` is always `null`.

Targets used by the current collector are:

- an ephemeral loopback HTTP server for request-header order;
- `tls.peet.ws` for normalized browser TLS/HTTP2 presentation;
- Cloudflare's public trace endpoint for coarse network geography;
- the current Browserless browser itself for page-visible presentation and execution-context shape.

A provider preflight can be recorded separately as an outcome observation, but it is not an input detector oracle.

## Authority split

One Browserless carrier lease spans the whole collection.

Host-side facts are collected before the browser-network child starts:

- Browserless container image identity;
- exact Chromium executable SHA-256;
- container font resolution;
- non-secret persistent-profile cookie row and distinct-host counts.

The Playwright/network child is then executed inside the endpoint's configured Network-v2 namespace and observes:

- browser TLS/HTTP2 fields;
- neutral main-document request-header order;
- browser JS presentation;
- CDP Runtime execution-context shape;
- coarse network trace.

`podman` remains on the host side. The Network-v2 namespace is not treated as a Podman/cgroup control-plane authority.

While the child Browserless session is live, the host parent observes the actual Browserless Chromium process command line. The collector records `effectiveLaunchArgvNormalized` in `controlLayer`; only transient `--remote-debugging-port=<number>` is normalized to `--remote-debugging-port=<ephemeral>`. This makes Browserless/Puppeteer default launch-argument drift part of `controlLayerDigest` without binding a random port into every witness.

## Detector coverage

Current detector version: `harness-browser-security-r2`.

```text
CF02  normalized browser JA4 / PeetPrint / HTTP2 / TLS version
      JA3 deliberately excluded because R1 measured within-arm variability

CF03  neutral main-document request header order

CF04  webdriver / UA / platform / locale / hardware / geometry / timezone

CF05  Runtime execution-context count and normalized context shape
      broader protocol-domain subscription state remains uncovered

CF06  network geography + explicit network observer identity
      browser timezone/locale/geometry + container font resolution

CF07  cookie row count and distinct host count only
      no cookie value is read into the witness
```

Cloudflare trace's `observer` is explicitly recorded as `python-urllib`. Its `http`/`tls` values describe that coarse trace observer, not Chromium's browser transport; browser transport belongs to CF02.

## Invocation

```text
PYTHONPATH=. python scripts/browser_security_witness_source.py \
  --endpoint-id chatgpt-carrier-11 \
  --witness-id <stable-observation-id> \
  --output source-manifest.json
```

Feed the resulting manifest to Security-v2:

```text
PYTHONPATH=src python scripts/build_browser_security_witness.py \
  source-manifest.json --output witness-bundle.json
```

Then compare only like-for-like detector versions for subject-drift claims. A detector-version or coverage change is `DETECTOR_DRIFT`.

## R2 acceptance evidence

Two consecutive live observations of `chatgpt-carrier-11` were recorded as:

```text
evidence/browser-security-witness-source-r2-run1-20260918.json
evidence/browser-security-witness-source-r2-run2-20260918.json
```

Both used the same current Chromium binary, Network-v2 authority, Browserless image, and normalized effective launch surface. Security-v2 comparison of the two canonical bundles reported:

```text
browserBinary change   false
controlLayer change    false
networkAuthority change false
changedFamilies        []
detectorDrift          []
publicObservationChanges []
rootCauseEstablished   false
```

That establishes repeatability of this detector version under the measured two-run sample; it does not establish a Cloudflare or provider challenge cause.

## Pool runner

`browser_security_pool_runner.py` turns the per-carrier collector into one neutral/read-only pool operation while preserving the Harness/Security authority split.

```text
Harness pool runner
  -> verify Security-v2 pool-index + each baseline bundle SHA-256
  -> collect carrier-11 current source manifest
  -> Security-v2 canonicalize carrier-11
  -> collect carrier-12 current source manifest
  -> Security-v2 canonicalize carrier-12
  -> collect carrier-13 current source manifest
  -> Security-v2 canonicalize carrier-13
  -> Security-v2 pool classification
```

Harness does not reimplement drift semantics. The Security-v2 result is embedded unchanged in the run receipt.

Example:

```text
python scripts/browser_security_pool_runner.py \
  --run-id pool-check-20260918 \
  --security-root /root/projects/ordivon-security-v2
```

Use `--artifact-dir` when the candidate manifests, canonical bundles, comparison manifest, and final receipt should be retained. The runner verifies the digest-fenced LKG bundles before collection and refuses pool-index paths that escape the configured Security-v2 root.

The R1 live dogfood receipt is sealed at:

```text
evidence/browser-security/pool-runner-r1-acceptance-20260918.json
```

That run used all three production Browserless carriers and returned `NO_OBSERVED_DRIFT` with CF02-CF07 unchanged, no detector drift, no browser/control/network authority drift, `providerChallengeVisited=false`, and `providerSendAttempted=false`.
