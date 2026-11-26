# GitHub Source Collaboration — Thought / Logic / Capability LEGO (R1)

Status: architecture decision candidate. No new registry, GitHub service, release
authority, PR queue, or policy database is created by this document.

## First principles

GitHub is a provider, not the durable owner of every Ordivon fact.

- Git owns source bytes, commits, trees, branches and source history.
- GitHub owns its actual Issue, PR, review, check, merge queue, release and
  uploaded attestation observations.
- Host owns semantic Work/Topic/Message coordination and attention.
- Harness owns agent decision and tool intent.
- Runtime owns physical execution, Workspace and Job/Artifact observations.
- Deployment/receiving Owner owns Installed and domain acceptance evidence.

A GitHub PR can be MERGED without any Runtime service being INSTALLED, and a
green test Job cannot substitute for consumer/domain acceptance.

## Decomposition

| Thought model | Stable logic responsibility | Existing capability / natural location |
| --- | --- | --- |
| Identity-first | Source identity and original change set | Git, Runtime native Git Workspace |
| Representation-first | Cross-Agent semantic write-set conflict | Host coordination + Git diff/PR files |
| Contract-first | Source-to-consumer affected change qualification | `tools/repo/affected_owners.py`, owner native tasks |
| Counterexample-first | Positive and negative behavioral verification | owner tests, real native fixtures, fault injection |
| Evidence-calibrated | Check/merge result and absence of evidence | GitHub checks, merge queue, typed observations |
| Effect-first | Release source/Artifact/Installed separation | GitHub release+attestation, native recipient Owner |
| Reuse-first | Provider-native GitHub actions without a second broker | `gh` / official API, existing Gateway |

### Repository mechanisms: keep in the natural root owner

`tools/repo/check_github_governance.py` is the existing executable adapter
for the current monorepo policy. It remains callable by CI and its independent
consumers. The current private-module layout and behavior are source-native: inspect
the imports of `tools/repo/check_github_governance.py`, the implementation
under `tools/repo/github_governance/`, and its behavioral tests.
The architectural boundary is the existing executable adapter, not a frozen
list of private files; provider-specific logic should stay with its natural
consumer.

### Explicit non-migrations

- Keep `.github/workflows/*` as native GitHub workflow files. Extract
  reusable scripts only when the actual workflow has a behavioral consumer.
- Keep `platform/network/.../github_release_mise.py` in Network: its natural
  task is verified dependency acquisition, not PR/branch control.
- Keep `catalogs/capabilities/scripts/github_radar_incremental.py` in the
  capability discovery catalog: source observation is not repository policy.
- Keep `services/runtime` Git source-state and native Workspace code in
  Runtime, not in a duplicate GitHub manager.
- Keep `capabilities/distribution` provider tests/evidence under Distribution.
- Do not centralize credentials, protected-branch admission or the merge queue
  into a new Ordivon GitHub authorization framework.

## Operational proof obligations

1. Source identity: actual Git tree and change set, including filenames that
   contain newline and non-UTF8 bytes, must remain lossless.
2. Provider qualification: official API/CLI observations are scoped to exact
   object identity and local retrieval time; UNKNOWN is not FALSE.
3. Verifier behavior: allowed inputs pass; malformed CODEOWNERS, duplicate
   dependency owners, missing CodeQL events and missing languages fail.
4. Real CI: zero tests, skipped tests, a successful outer Job with failed
   domain assertions, and file-location-only green/red results do not count as
   verified behavior.
5. Integration: official merge queue owns the merge transition. The
   Source/Artifact/Installed/Domain states are distinct and should be observed
   through their existing native owners.

Testing is against functions and externally observed effects, not the
continued presence of a prior source file or an exact internal AST layout.

## Follow-on decomposition decisions

Extract further logic *only after* consumer analysis, with distinct patches:

- Typed CI workflow structure and required-check semantics, removing accidental
  text/filename coupling without weakening real required checks.
- GitHub Source / PR / Merge / Release provider adapters where multiple actual
  consumers need them; do not move consumer-specific code for taxonomy alone.
- Source-to-Installed independent receipt acceptance at the release recipient.
- Catalog discovery parsing/normalization/observation in its own natural owner.

Before edits: check official open PR write-sets and current protected main;
verify focused owner tests plus genuine malformed-input negatives. Do not
force-close Workspace or modify another Agent's partial source.
