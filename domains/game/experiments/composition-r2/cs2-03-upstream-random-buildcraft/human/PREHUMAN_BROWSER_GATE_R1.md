# CS2-03 Pre-Human Browser Gate — R1

Status: **PASS / HUMAN EVIDENCE STILL UNOBSERVED**

## Purpose

Remove mechanical/browser/UI defects before spending Human attention. This gate deliberately separates deterministic browser regression from agentic browser perception.

```text
Playwright
  -> full 4 runs x 4 choices
  -> reflections
  -> JSON export
  -> deterministic mechanical gate

Browser Use
  -> accessibility-tree observation
  -> discover Begin without selector knowledge
  -> click through CDP coordinates
  -> re-observe changed page
  -> discover challenge state + module controls
  -> agentic perception gate

Human
  -> only irreducibly Human experience / learning evidence
```

## Accepted local evidence — 2026-09-14

### Playwright full regression

- Playwright `1.62.0`;
- explicit existing Chromium: `/root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`;
- 4 runs / 16 choices completed;
- both information-timing conditions exercised;
- four reflection pages completed;
- session JSON exported successfully;
- initial Schedule B export was `20671` bytes with SHA-256 `103efb12f07d36579cd5f865cd10446380fa3c6f408e81f944cdbbb21c8bcb29`;
- Human C0 validator accepted the session structure while still reporting `humanMechanismStanding=UNASSESSED_C0_ONLY` and `conditionEffectStanding=NOT_ASSESSED_AT_C0`.

Initial direct regression job: `job-01a09ea2-ddfe-7610-a18f-3264485b2e0f`.

Reusable repository gate script independently repeated the full 4×4 flow successfully under Runtime Job `job-01a09eae-6a66-7781-890e-5b37d4309020` (Schedule A), so both A/B schedules have now been mechanically exercised and the checked-in gate itself is executable rather than only the one-off prototype command.

### Browser Use perception probe

Browser Use local package `0.13.10`, harness CLI `0.1.13`.

Observed independently through Browser Use / CDP:

1. page title `Buildcraft Timing Study`;
2. accessibility tree exposed `Begin` as a button;
3. Browser Use derived the button box from `backendDOMNodeId` and clicked it by coordinates;
4. after re-observation, the page exposed a timing condition and three module buttons with their stats;
5. no pre-authored CSS selector was needed for the state transition.

Runtime Jobs:

- discovery: `job-01a09ea6-afec-74b2-8490-990be683e161`;
- state transition / re-observation: `job-01a09ea7-ba97-7283-858d-7d3477a8af4a` (concealed / DOWNSTREAM observed);
- checked-in bounded probe repeatability: `job-01a09eae-270f-7093-9305-4888f6f74046` (visible / UPSTREAM observed).

Across the independent probes Browser Use therefore observed both declared timing states without relying on a CSS selector for the `Begin → first decision` transition.

### Browser Use full-run stress attempt

A deliberately broader 16-choice Browser Use run hit the Runtime 90-second deadline:

`job-01a09ea8-3106-7d91-a196-72eb2cec11c0` -> `DEADLINE_EXCEEDED`.

This is **not** treated as apparatus failure and is not required for admission. Repeating a deterministic 4×4 regression through the slower agentic perception layer provides little additional evidence once Playwright already owns the full mechanical gate. Browser Use therefore remains the exploratory/perception provider, not the deterministic regression authority.

## Standing

```text
Deterministic browser mechanics      PASS
Agentic browser perception/action    PASS_BOUNDED
Session export / validator boundary  PASS
Human apparatus evidence             UNOBSERVED
Human mechanism evidence             UNASSESSED
Condition effect                     NOT_ASSESSED
Product / G0                         NOT_AUTHORIZED
```

## Reusable commands

Full deterministic gate (run with a Python environment that has Playwright):

```bash
python scripts/prehuman_playwright_gate.py \
  --chromium /root/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome
```

Bounded Browser Use perception probe, after binding Browser Use to an already-authorized CDP endpoint:

```bash
BU_CDP_URL=http://127.0.0.1:<port> scripts/prehuman_browser_use_probe.sh
```

## Boundary

Passing this gate proves the apparatus is mechanically reachable by mature browser tooling and that the Browser Use observation/action abstraction can discover the intended controls. It does not prove that a Human understands the design, adapts strategically, experiences agency/mastery/fun, or prefers either condition.
