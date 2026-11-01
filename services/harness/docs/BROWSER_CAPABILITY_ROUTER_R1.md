# Browser Capability Router R1

## Role

Browser Capability Router is a browser-domain, pre-execution route planner. It does not infer
requirements from natural-language tasks, grant provider authority, execute browser effects, or
define Harness/Runtime success.

The caller supplies explicit requirements. The router returns one exact currently-ready route or a
typed HOLD.

## Composition axes

A browser route is composed from three independent coordinates:

1. executor — who decides/executes browser operations;
2. substrate — where browser state/processes live;
3. providerFlow — whether the route is generic browsing or a provider-specific materialization
   flow.

Current R1 routes:

| route | executor | substrate | providerFlow |
| --- | --- | --- | --- |
| jev-fast-windows-v1 | jev_fast | windows_chrome | generic |
| browser-use-browserless-v1 | browser_use_structured | browserless | generic |
| cft-human-session-v1 | cft_human_session | systemd_cft | generic |
| chatgpt-agent-automation-browserless-v1 | chatgpt_provider_flow | browserless | chatgpt_agent_automation |
| visual-browser-v1 | visual | unbound | generic |

Browserless is therefore not treated as a peer reasoning engine to Browser Use or Jev. It is a
browser/session substrate. The ChatGPT route remains a specialized provider flow because it owns
SEND fencing, provider-effect ambiguity fencing, and ChatGPT-specific authenticated carrier continuity.

Generic human-assisted browsing is a separate capability. cft-human-session-v1 is selected only
when callers explicitly require human-handoff; it does not replace the ordinary Jev or structured
Browser Use routes. Its readiness adapter is projection-only and composes Workstation v2's exact
browser:playwright-chromium equipment binding with systemd, native loopback CDP, Xvfb, x11vnc,
and noVNC/websockify. Browser lifetime is therefore independent of the attaching Playwright client.

## Selection contract

The request supplies providerFlow, requiredFeatures, preferredFeatures, and optional
explicitRouteId. The router does not parse a goal string to guess these fields.

Admission rules:

- every required feature must be declared by the route;
- readiness is observed at plan time;
- preferred features affect deterministic ranking only;
- explicit route selection never silently falls back;
- no compatible ready route returns HOLD.

A route plan is not provider authorization and is not browser-effect authority.

## Readiness

R1 reads existing owner-native surfaces:

- Jev: Workstation Windows Jev provider status plus presence-only credential gates;
- Browser Use: exact configured executable, Browserless substrate, and operator systemd mask state;
- ChatGPT Agent Automation: existing Browserless Automation doctor;
- Visual: explicitly NOT_MATERIALIZED.

Operator systemd masks are policy boundaries. A fully masked generic Browser Use lane reports
POLICY_DISABLED; the router does not unmask or wake it.

Jev text-entry additionally requires the configured text-model credential because upstream Jev
delegates generated field values to that helper.

## Authority boundary

Current Harness deliberately has no generic Provider Use Policy/capability registry. Provider route
authorization belongs before Harness Contract construction. This router follows that boundary and
does not resurrect retired Harness policy ontology.

Harness continues to own exact Run execution/effect continuity after a caller/domain has selected
an admitted route. Runtime continues to own physical Job/Attempt truth.

## Current machine standing — 2026-09-18

Observed during R1 dogfood:

- Jev Windows physical provider: healthy; route blocked only by missing TYPESAFE_API_KEY;
- generic Browser Use executable binding: repaired to the installed uv tool environment;
- generic Browser Use browser-agent-21: intentionally operator-masked, therefore POLICY_DISABLED;
- ChatGPT Agent Automation: healthy with chatgpt-carrier-11 available;
- visual browser executor: not materialized.

A generic navigate + click request therefore correctly returns HOLD_NO_READY_ROUTE under the
current operator/credential state.

## Non-claims

R1 does not establish:

- website compatibility;
- provider semantic equivalence;
- a global capability registry;
- natural-language capability classification;
- task authorization;
- browser semantic success;
- Runtime physical completion.


## 2026-11-02 real-consumer browser LEGO audit: node-identity before effect

This incremental source audit compares the current `browser_use_browserless.py`
adapter and its benchmark route consumer against browser-owned accessibility
snapshots, Playwright snapshot-scoped refs, and Playwright actionability.
It is **not** a new browser registry, provider, Skill, or readiness policy.

The previous Browser Use click/input contract re-enumerated AX nodes at
execution time and checked only `index + role + accessible name`. Two
same-named buttons can exchange an index, or one can be replaced by another
with the same role and name. The old guard would admit a coordinate action
on the wrong physical node. A native red test reproduced that missing
identity witness.

The current candidate adds `backendDOMNodeId` from the existing Chromium
`Accessibility.getFullAXTree` observation and requires the exact positive
integer ID on click/input. Before a coordinate effect, the generated program
re-observes and checks both semantic fields and the exact node ID.
Changed target identity raises `affordance-identity-changed`; there is no
relocation, retry, or fallback. The existing Browser Benchmark adapter now
passes the observed node ID, retaining the one real in-tree consumer.

R2.1 narrow LEGO representation:

- `I`: selected route and observed index, role, name, browser-provided node ID.
- `O`: either a single attempted click/input or a fail-closed refusal;
  the action receipt remains non-semantic until outcome observation.
- `S`: ephemeral Browser Use daemon/session and current Chromium document.
- `pre`: exact Browserless lane and captured target binding, available CDP.
- `post`: no coordinate effect on a mismatched/replaced AX node at the
  guard point; an observed CLICKED status alone is **not** task success.
- `inv`: no caller-chosen action retargeting, no silent index-only fallback.
- `eff`: read AX+box model, then one browser action when admitted.
- `c`: bounded page AX projection of up to 160 affordances; no new model.
- `epsilon`: DOM can mutate after guard; overlays, hit testing, OOPIF and
  unchanged node with changed *surrounding meaning* are **UNKNOWN**.
- `prov`: existing Browser Use source and actual benchmark consumer;
  red/green tests and exact source SHA/Job receipts accompany publication.
- `unfold`: upstream CDP AX/DOM observation -> ephemeral identity check ->
  existing action helper -> independent outcome witness.

An unrelated but real doctor failure was also reproduced: missing optional
Browserless/ChatGPT Automation adapter imports crashed the *whole* router.
The source now returns `ADAPTER_UNAVAILABLE` for only the unavailable lane.
Live doctor is an observation: `READY_ON_DEMAND` and `READY` do not
authorize browser operations or imply site compatibility.

**External standards to reuse rather than copy**: WAI-ARIA and AccName for
roles/names; Playwright for actionability/autowait and isolated test contexts;
Browserless for reconnection/session TTL and cleanup; Chrome remote-debug
security requires a dedicated nondefault profile/explicit user consent;
Superpowers TDD/verification and ECC browser-qa for independent falsification.

**Open hard kernels, not hidden as PASS**: prove a full decision-bound
semantic witness for the same physical DOM node after nearby context changes;
document/frame generation under navigation and OOPIF; stable hit-test before
coordinates; recipient verification beyond action status; browser session
isolation and explicit cleanup under concurrent/reconnect/lost-response cases.
Only add implementation complexity after a real owner consumer and failing
reproduction, not from speculative framework symmetry.
