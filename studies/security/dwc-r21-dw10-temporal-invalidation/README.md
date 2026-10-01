# DWC R2.1 DW10 — Temporal Performance & Dependency-Aware Invalidation

Status: **EXPERIMENTAL DWC-LOCAL STUDY / NOT A SCHEDULER / NOT SECURITY AUTHORITY**
Date: 2026-10-01
Host Work: `work:security:dwc-r21:dw10-temporal-invalidation:20261001`

## Objective

DW10 is the cross-cutting temporal and invalidation projection for one Defense Window
Convergence epoch. It answers two bounded questions:

1. **What changed, and which already-derived claims actually depend on that change?**
2. **Given explicit observed/policy timing only, where is the current critical path and what
   latency has actually been observed?**

It deliberately does not execute remediation, schedule work, grant authority, refresh owner
truth, or establish security/domain acceptance.

## Owner boundary

```text
DW01..DW09 natural owners
        |
        | exact state digests + owner identities + explicit dependency edges
        v
DW10 Defense Epoch projection
        |
        +-- changed support set
        +-- selective invalidation closure
        +-- stale-support risk projection
        +-- T0..T7 / Tc..Te..Tr observed latency
        +-- explicit-duration critical path
        +-- policy-grounded slack
        |
        v
advisory evidence only

Temporal/CACAO workflow owner -> waits / retries / loops / timers / durable orchestration
Host                       -> semantic Work continuity
Runtime                    -> Workspace / Job / Attempt / Artifact execution truth
Security/domain owners     -> applicability, authority, effect and consequence truth
```

CACAO 2.0 is used as the external workflow-semantics reference because it already defines
sequential, parallel, conditional and temporal workflow constructs. DW10 therefore does not
grow a second workflow engine.

NIST SP 800-61r3 is an outcome anchor for keeping detection, response, eradication/recovery
timing visible as incident-response evidence rather than collapsing everything into a single
"cyber score".

## Defense Epoch contract

One epoch is a disposable task-local object:

- `epochId`: exact local epoch identity;
- `nodes`: exact source/derived bindings;
- `edges`: explicit dependency relations;
- `milestones`: observed `T0..T7`, `Tc`, `Te`, `Tr` timestamps in a common elapsed-time basis;
- `policyDeadline`: optional exact DW03 policy budget and source ref.

Every node carries:

- `id`;
- `role = source | derived`;
- `kind`;
- `ownerId`;
- `stateDigest`;
- `standing`;
- `revalidationCostUnits` (a qualification fixture cost unit, never a global priority score);
- optional `durationMs` + `durationBasis = OBSERVED | POLICY_BUDGET`.

Every edge independently carries two semantics:

- `invalidatesOnChange`: a changed source/producer makes the consumer's old support stale;
- `temporalDependency`: the edge participates in critical-path precedence.

This separation matters. An observation/display relation can be useful without invalidating a
security claim, while a temporal precedence relation must not silently become an authority or
semantic dependency.

## First qualification dependency graph

The synthetic qualification fixture uses this explicit DWC-local graph:

```text
subject -> DW01 -> DW02 -> DW03 -> DW06 -> DW07 -> DW08
             |       |       ^      ^
             |       |       |      |
             |       +-> DW04 -> DW05
             |           |
             +---------->+-----------> DW09
threat  ------------> DW02
policy  -------------------------> DW03
```

More exactly:

- DW02 consumes DW01 subject binding plus threat-source evidence;
- DW03 consumes DW01/DW02 plus policy;
- DW04 consumes DW01/DW02;
- DW05 consumes DW04;
- DW06 consumes DW03/DW04/DW05;
- DW07 consumes DW06;
- DW08 consumes DW07;
- DW09 consumes DW01/DW02/DW04 and remains independent of verified protection.

This is a qualification graph derived from the current DW01-DW09 Work contracts. It is not a
global or permanent Security dependency registry. Real owner outputs must supply the exact
edges for each production epoch.

## Selective invalidation semantics

A node is changed when any support identity component changes:

```text
stateDigest
standing
ownerId
role
kind
```

Adding/removing/changing an **invalidating** edge also changes its consumer. DW10 then walks
only `invalidatesOnChange=true` descendants.

A non-invalidating observation edge does not trigger revalidation.

The projection refuses:

- dangling dependencies;
- cycles in the invalidation graph;
- non-boolean invalidation/temporal flags;
- missing owner identity.

The projection keeps previously-positive invalidated descendants in
`staleSupportRiskNodeIds`; it never silently keeps an old VERIFIED/PASS/SATISFIED standing
after its support changed.

## Temporal metrics

DW10 exposes observed latency without inferring missing attacker or organization timing:

- adjacent `T0 -> ... -> T7` segment latencies when both endpoints exist;
- `TTVP = T7 - T0`;
- `compromiseToEradication = Te - Tc`;
- `compromiseToRecovery = Tr - Tc`;
- `eradicationToRecovery = Tr - Te`.

Missing endpoints produce `null`, not interpolation.

Critical path is calculated only when every involved stage has an explicit duration and basis.
If any duration is missing:

```text
criticalPath.standing = PARTIAL_UNKNOWN
criticalPath.slackStanding = UNKNOWN_DURATION
criticalPath.slackMs = null
```

A numeric slack is emitted only when:

1. stage durations are explicit; and
2. DW03 supplies an exact policy deadline source.

Unknown attacker timing is never converted into slack. The projection always emits
`schedulerAuthorityEstablished=false`.

## Acceptance fixtures

### Synthetic selective invalidation

Changing only the policy source invalidates:

```text
DW03 -> DW06 -> DW07 -> DW08
```

The fixture's deliberately-simple cost accounting is:

- full revalidation = 37 units;
- selective revalidation = 20 units;
- saved = 17 units (~45.95%).

These are **synthetic qualification units**, not measured production CPU/time savings.

### Synthetic timing

The complete timing fixture yields:

- TTVP = 9000 ms;
- compromise -> eradication = 9000 ms;
- compromise -> recovery = 11000 ms;
- critical path = `DW01 -> DW02 -> DW03 -> DW06 -> DW07 -> DW08`;
- critical-path duration = 9000 ms;
- explicit DW03 synthetic deadline = 12000 ms;
- policy slack = 3000 ms.

Again, these values validate calculation semantics only.

### Exchange 2021 public replay negative control

Microsoft publicly released Exchange security updates on 2021-03-02 for vulnerabilities it
said were being used in ongoing attacks. CISA issued ED 21-02 / an alert on 2021-03-03.

DW10 uses those dates only as **public historical source anchors**. They do not reveal any
specific organization's internal detection, applicability decision, authorization, patch,
verification, compromise, eradication or recovery timestamps. Therefore the public-only
fixture intentionally returns:

- local TTVP = UNKNOWN;
- local compromise -> recovery = UNKNOWN;
- critical path = PARTIAL_UNKNOWN;
- slack = UNKNOWN_DURATION;
- attacker timing assumed = false.

This negative control prevents public historical dates from being laundered into fake local
performance evidence.

## External anchors

- OASIS CACAO Security Playbooks v2.0:
  https://docs.oasis-open.org/cacao/security-playbooks/v2.0/security-playbooks-v2.0.html
- NIST SP 800-61 Rev. 3:
  https://csrc.nist.gov/pubs/sp/800/61/r3/final
- Microsoft MSRC Exchange resource center (2021-03-02):
  https://www.microsoft.com/msrc/blog/2021/03/multiple-security-updates-released-for-exchange-server
- CISA Exchange ED 21-02 alert (2021-03-03):
  https://www.cisa.gov/ncas/current-activity/2021/03/03/cisa-issues-emergency-directive-and-alert-microsoft-exchange

## Verification

```bash
python3 -m unittest discover \
  -s studies/security/dwc-r21-dw10-temporal-invalidation/tests \
  -p 'test_*.py' -v

python3 studies/security/dwc-r21-dw10-temporal-invalidation/scripts/run_fixture.py

python3 -m compileall -q studies/security/dwc-r21-dw10-temporal-invalidation
```

Before any shared-Composition promotion, DW12 must show repeated cross-case benefit over full
recomputation and a reduction in stale-support defects without authority violations, false
closure, unacceptable attention cost, or recovery regressions.
