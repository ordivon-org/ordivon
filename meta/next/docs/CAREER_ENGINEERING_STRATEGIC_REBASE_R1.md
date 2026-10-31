# Career Engineering Strategic Rebase R1

Status: **DETACHED REMEDIATION CANDIDATE / EXTERNAL-FIRST / NO PRODUCTION CUTOVER**
Source baseline: `origin/main@4733af25b4b3296ea75e3b370ec539f1bfd860d7`
Observed through: **2026-11-01**

## Decision

Career Engineering is not a new Career application, workflow engine, scheduler, registry, database, or scraper collection. It is a semantic/evidence composition over Ordivon's existing Runtime / Host / PostgreSQL substrate plus narrowly qualified external providers.

The semantic chain remains:

```text
Career Record
  -> Opportunity Intake
  -> Role / Competency Model
  -> Evidence & Gap
  -> Artifact Compiler
  -> Application Lifecycle
  -> External Outcome observations
  -> updated Career Record / decisions
```

A provider is behaviorally qualified only for the exact replayed boundary and retained evidence. A synthetic evaluation consumer does not establish a connected real Career Record or production activation. Repository popularity, package installation, interface discovery, and historical experiments do not by themselves create an active binding.

## Qualification states

Three states are now explicit:

```text
BEHAVIORALLY QUALIFIED
  exact pinned provider behavior was replayed against retained fixtures/invocations

INTERFACE QUALIFIED
  stable interface/schema/auth boundary was verified, but domain operations were not

DORMANT / REFERENCE / EXPERIMENT
  useful donor or prior evidence with no active consumer or incomplete qualification
```

This replaces the earlier "selected provider stack" interpretation, which was too broad.

## Stable release is the executable contract

Provider selection separates:

```text
upstream main          = discovery of possible future capability
stable release/package = executable provider identity
live hosted service    = independently currentness-observed service
```

Career-Ops supplied a concrete counterexample. Its top-level npm CLI for `@santifer/career-ops@1.38.0` scaffolds a workspace; it does not expose `keyword-match` as a package subcommand. The deterministic diagnostic lives inside the initialized stable-release workspace. That workspace's `keyword-match.mjs` rejects the newer-main-only `--url` surface. Claims are therefore bound to the actual released artifact and exact invocation, not to main documentation.

## Current qualified surfaces

### 1. Career-Ops — narrow behaviorally qualified diagnostic

Pinned provider:

- `@santifer/career-ops@1.38.0`
- release git head `115bc9873e3d43e23883f3c8f16436617facc62c`

Current admitted capability is only the deterministic JD skill-gap diagnostic from the initialized stable release.

Committed fixtures:

- `meta/next/fixtures/career/career-ops-synthetic-jd.md`
- `meta/next/fixtures/career/career-ops-synthetic-cv.md`

Replay:

```text
python3 meta/next/scripts/replay_career_provider_qualification.py
```

The replay initializes the exact stable release, verifies its git head, runs `node jd-skill-gap.mjs synthetic-jd.md`, executes the provider's built-in self-test, and executes a negative currentness probe.

Observed deterministic result:

- supported by resume prose: `TypeScript, Rust, Python, Go`
- gaps: `Spring, JavaScript, C++`
- provider self-test: **115 passed, 0 failed**
- stable release rejects `keyword-match.mjs --url ...` with `Unknown option: --url`

This is a derived diagnostic only. It is not eligibility, hiring probability, or employer judgment. Career-Ops' file-first tracker is not Ordivon durable truth. Broader Career-Ops workflow/agent behavior remains donor material, not admitted behavior.

Evidence: `meta/next/evidence/career/career-ops-1.38.0-replay-20261101.json`.

### 2. Reactive Resume — interface qualified, not behaviorally connected

Latest stable `v6.0.9` at commit `854459a44eb896ca185611bf669a65be4d5111cf` itself contains an Agent Plugins 1.0 plugin and streamable-HTTP MCP configuration. Both schemas validate against Ordivon's Agent Plugins 1.0 fixtures.

An unauthenticated probe of `https://rxresu.me/mcp` returned HTTP 401 with an OAuth protected-resource challenge. This proves a reachable guarded interface at observation time, not account access or successful resume/application operations.

Reactive Resume remains the preferred external resume/cover-letter/application product surface because duplicating that UI/product in Ordivon has no demonstrated consumer. However, this candidate claims **no authenticated Reactive Resume product behavior**.

## Demoted providers and deleted activation

### Resume-Matcher

The v1.4.0 experiment remains useful evidence: after creating and reading provider-canonical synthetic state, summary/bullet edits passed while an institution identity mutation failed with `education.identity`.

Independent review found that this did **not** match the earlier "initial admitted tools" story: the demonstrated path required stateful `create_master_resume` + `get_resume`, and the observed backend was ephemeral SQLite. It is therefore **experiment only / no admitted consumer**. The positive result also emitted `GROUNDING_REVIEW_REQUIRED`, proving structural preservation is not equivalent to factual grounding.

### JobSync

No verified slice consumes JobSync. The demonstrated Opportunity Intake path used the official Greenhouse API directly. JobSync is therefore **reference only** for discovery patterns; there is no active binding or parallel tracker product.

### JobSpy

The prior candidate plugin was based on package/entrypoint smoke only. No live-board request or MCP behavior was accepted, and no current consumer requires it. The Ordivon JobSpy plugin activation is therefore deleted. JobSpy remains only a dormant fallback candidate.

### Other donors

AI-Job-Search remains a method reference; JSON Resume an interchange reference; RenderCV an on-demand renderer. None is an active binding without a consumer.

## Opportunity acquisition order

```text
official ATS API / employer structured source
  -> Schema.org JobPosting / provider-native structured page
  -> official employer career page
  -> qualified external discovery provider with a concrete consumer
  -> generic browser/scrape only when justified
```

The first demonstrated live opportunity path used the official Greenhouse API directly.

## Historical evidence is not admission proof

Two earlier slices are retained because they contain useful observations, but their role is explicitly reduced:

- `cloudflare-8245211-career-ops-vertical-slice-20261031.json` = **historical live observation, not replay-complete admission proof**.
- `resume-matcher-1.4.0-artifact-compiler-slice-20261101.json` = **experiment only, not an active provider binding**.

The new committed Career-Ops replay is the current provider-native behavioral qualification.

## Independent review and blockers

A genuinely independent read-only Codex CLI review examined exact head:

`baf7f557e0bf29866f231cf1af4b8a4a58632257`

Evidence:

`meta/next/evidence/career/independent-codex-review-baf7f557-20261101.json`

Verdict: **BLOCK**.

It identified:

1. Resume-Matcher's demonstrated stateful preservation path did not match the earlier admitted-tool boundary.
2. The unit tests were mostly snapshot assertions over our own evidence JSON and could not establish provider behavior.
3. The earlier vertical slices lacked enough retained input/invocation material for independent replay.

The remediation in the current dirty candidate addresses those findings by demoting Resume-Matcher/JobSync/JobSpy, deleting the JobSpy plugin activation, separating snapshot tests from provider-native replay, and committing exact Career-Ops fixtures plus replay invocation.

A fresh independent read-only Codex review inspected the post-remediation implementation commit 21d2c38b15ace4f39ed657a186f29ead8a956efe and returned **PASS_WITH_FINDINGS**, with C1/C2/C3 CLOSED within synthetic qualification scope. It noted stale baseline references and a synthetic consumer phrased too strongly; those metadata findings are corrected here. A final review of the corrected commit and separate owner-native acceptance remain required before integration.

A second Claude CLI review attempt produced no review because that local CLI was not authenticated. It is not counted as evidence.

## Testing semantics

`meta/next/tests/test_career_external_provider_stack.py` is now intentionally a **snapshot/composition consistency suite**. It checks that:

- only the narrow Career-Ops capability is behaviorally qualified;
- interface qualification does not masquerade as provider behavior;
- dormant providers remain dormant;
- the prior independent BLOCK is preserved;
- committed replay evidence is bound to the exact fixture hashes;
- historical experiments are not promoted into active bindings.

Provider behavior is established by the explicit replay command, not by assertions over stored JSON.

## Formal / type-driven invariants

```text
StableProviderCapability => observed in exact released artifact
BehaviorallyQualified     => replayable provider-native behavior + retained input
InterfaceQualified        != BehaviorallyQualified
PackageSmoke              != ActiveBinding
HistoricalExperiment      != ActiveBinding
SubmittedApplication      => observed external effect OR UNVERIFIED_USER_CLAIM
ExternalOutcome           => external/provider observation OR UNKNOWN
ArtifactClaim             => supported by evidence OR marked unsupported
IrreversibleEffect        => HumanApproval
UNKNOWN                   != FAIL
Drafted                   != Submitted
ProductCaseState          != EmployerTruth
ProviderScore             != HiringProbability
DurableCareerState        => existing Ordivon/PostgreSQL authority
```

## Delete-by-default result

Current candidate deliberately does **not** add or retain a custom:

- Career runtime/scheduler/queue;
- second global registry;
- resume/application UI;
- canonical Career SQLite store;
- parallel JobSync tracker;
- active JobSpy wrapper/plugin;
- Resume-Matcher application store;
- generic scraper where first-party ATS data suffices.

## Integration gate

Remote `main` advanced from the earlier `ffd81854...` baseline to `277a62019b49...`. The intervening remote diff had no observed Career-provider overlap. The implementation candidate is now based on `277a620...` before rereview.

The earlier independent review verdict was **BLOCK**; the subsequent read-only review of 21d2c38 returned **PASS_WITH_FINDINGS** and closed C1/C2/C3 in synthetic scope. Metadata correction and owner-native integration still require final verification. Therefore:

```text
mergeAdmitted = false
freshIndependentReviewRequired = true
```

No production cutover or external application effect has occurred.
