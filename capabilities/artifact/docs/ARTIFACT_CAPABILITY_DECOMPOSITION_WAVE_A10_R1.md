# Artifact Capability Decomposition — Wave A10 R1

## Standing

`WEB_VERIFIER_OWNER_EXTRACTED_COMPATIBILITY_PRESERVED`

Wave A10 removes Web conformance/browser verification implementations and the HTML Playwright/axe runner from the historical Delivery owner and assigns them to `artifact_verifiers.web`.

## One-sentence boundary

Web Verification owns local HTML conformance checking, local browser execution evidence, Chromium accessibility evidence, exact subject-digest binding, and Web verifier toolchain selection; it does not own deployment, remote-origin behavior, profile policy, delivery effects, trust, or workflow durability.

## New package

```text
artifact_verifiers/web/
├── __init__.py
├── conformance.py
├── browser.py
├── toolchain.py
└── node/
    └── verify_html.mjs
```

### `conformance.py`

Owns Nu HTML Checker execution:

- exact HTML artifact fact binding;
- Nu Html Checker JAR selection consumption;
- Java executable selection consumption;
- JSON result parsing;
- validator version and JAR digest;
- message census;
- bounded diagnostics;
- PASS only when process/result/message conditions all pass.

Its truth boundary remains syntax/content-model conformance only.

### `browser.py`

Owns Python-side browser verifier execution:

- Node executable selection;
- verifier runner selection;
- Node package-root binding;
- exact artifact path invocation;
- JSON verifier result parsing;
- subject SHA-256 equality check;
- fail-closed digest binding;
- bounded diagnostics.

The profile-level decision about which browser targets are required remains in `artifact_verification.stage`.

### `node/verify_html.mjs`

The actual Playwright/axe runner moves with its verifier owner.

It owns local execution of:

- Chromium;
- Firefox;
- WebKit when supported on the host;
- Chromium axe accessibility analysis;
- browser version/executable evidence;
- page title and H1 count observations;
- exact source-byte SHA-256;
- Playwright and axe package versions.

The shared Node package/dependency root remains under the existing Artifact tooling location because it also serves SVG/OGG verification. A10 moves the Web runner, not unrelated shared Node dependency management.

### `toolchain.py`

Owns:

- Nu Html Checker 26.9.7 global path;
- local VNU fallback path;
- Java selection;
- Node selection;
- global Node package root;
- shared local Node package root;
- Web runner path.

Delivery no longer owns `GLOBAL_VNU` or `GLOBAL_NODE_PACKAGE_ROOT`.

## Verification-stage wiring

A5 verify-stage now binds directly to:

```text
verify_html_conformance=web_verify_conformance
verify_web_local=web_verify_local
```

so Web verification no longer routes through Delivery compatibility wrappers.

The stage still owns profile-specific assembly of:

- conformance receipt;
- structural receipt;
- accessibility receipt;
- target-renderer receipt;
- pending required gates.

This preserves the distinction between verifier implementation and verification orchestration.

## Delivery compatibility surface

Historical callers retain:

```text
_vnu_jar                 2 lines
verify_html_conformance  2 lines
verify_web_local          2 lines
```

All three delegate to `artifact_verifiers.web`.

## Truth boundaries retained

Nu HTML Checker PASS does not establish browser behavior, accessibility, or deployed-origin behavior.

Local Playwright/axe PASS does not establish that every profile-required renderer passed; the verification stage evaluates required renderer policy.

Unsupported-host WebKit remains non-PASS and is never silently promoted.

Local browser evidence does not establish remote deployment behavior.

## Monolith reduction

Measured on the A10 candidate:

```text
artifact_delivery.py at decomposition start: ~3922 lines
after A2:                                       3458
after A3:                                       2822
after A4:                                       2242
after A5:                                       2028
after A6:                                       1737
after A7:                                       1616
after A8:                                       1546
after A9:                                       1520
after A10:                                      1442
```

A10 removes another ~78 net lines from Delivery while moving the 105-line Web runner out of the Delivery-owned node directory.

## TDD / verification evidence

A10 tests were written before implementation and observed RED because:

- `artifact_verifiers.web` did not exist;
- Web conformance/browser implementations remained in Delivery;
- the Playwright/axe HTML runner remained under `artifact-delivery/node`;
- Delivery still owned VNU/Node package-root constants;
- verification-stage still wired through Delivery.

After extraction:

- A10 decomposition tests: **6 PASS**;
- legacy `test_artifact_delivery.py`: **79 tests, 0 failures, 2 conditional skips**;
- A2–A10 + OpenXML environment + OCI targeted bundle: **65 PASS**;
- Temporal Artifact delivery contract: **12 PASS**;
- full Artifact regression: **366 tests, 0 failures, 4 conditional skips**;
- `compileall`: PASS;
- `git diff --check`: PASS before final commit gate.

Candidate full-regression Runtime Job:

`job-01a0b37d-9663-76c0-87c6-7a307ada69a4`

## Architectural standing after A10

All major concrete verifier families previously embedded in Delivery now have explicit owners:

```text
artifact_verifiers/
├── presentation/
├── document/
├── pdf/
├── openxml/
└── web/
```

`artifact_verification.stage` remains orchestration, not a verifier implementation monolith.

At this point the next work should stop creating verifier packages and instead target residual coupling:

1. OCI compatibility imports from Delivery;
2. Temporal's Delivery-CLI-specific operation contract;
3. remaining CLI/cross-format compatibility helpers;
4. final facade reduction and compatibility retirement planning.

The next bounded wave should therefore focus on **OCI decoupling from Delivery** rather than inventing another verifier layer.
