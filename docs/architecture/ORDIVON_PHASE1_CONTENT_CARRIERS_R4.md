# Ordivon Phase 1 R4 — source and content taxonomy

Exact Git monorepo cut: 3c46c527543d76027c7f20479d82b9fc718641af
Unique tracked source files: 5004 / 5004.
30 explicit navigation zones. Source roles and installed runtime correctness remain UNKNOWN.
Prior 718 recursive cells are hierarchical and may nest; they are NOT 718 disjoint owner allocations.

## Source zones (source locators only)

| Navigation area | Exact Git files |
|---|---:|
| region/architecture-documentation | 113 |
| region/formal-proof-toolchain-source | 10 |
| region/lego-semantic-method-source | 2 |
| region/migration-and-historical-records | 114 |
| region/other-agent-method-sources | 37 |
| region/repository-ci-config | 4 |
| region/repository-integration-tests | 1 |
| region/repository-mechanics-source | 49 |
| region/repository-root-config | 6 |
| region/research-publication-profiles | 12 |
| region/research-reusable-profiles | 3 |
| region/retrospective-evidence | 1 |
| zone/agent-plugin-package | 2 |
| zone/agent-run-context | 729 |
| zone/artifact-distribution | 69 |
| zone/artifact-production | 426 |
| zone/capability-routing | 83 |
| zone/connectivity-and-observation | 158 |
| zone/contract-composition | 54 |
| zone/creative-production | 582 |
| zone/durable-collaboration | 98 |
| zone/endpoint-environment | 274 |
| zone/human-facing-web | 27 |
| zone/identity-policy-and-effect-fences | 173 |
| zone/interactive-game-production | 51 |
| zone/knowledge-and-problem-framing | 1016 |
| zone/long-term-preservation | 47 |
| zone/method-discovery-service | 38 |
| zone/physical-execution | 419 |
| zone/quantitative-capital | 406 |

## Observed content syntax classes

| Content envelope | Files |
|---|---:|
| JSON_OBJECT_DECLARATION | 1541 |
| MARKDOWN_DOCUMENT | 1245 |
| PYTHON_SOURCE | 641 |
| PYTHON_TEST_SOURCE | 562 |
| TEXT_OTHER_UNKNOWN_FUNCTION | 229 |
| STRUCTURED_TEXT_OR_CONFIG | 209 |
| SOURCE_SH | 91 |
| SOURCE_RS | 87 |
| SHEBANG_SCRIPT | 83 |
| SOURCE_TS | 74 |
| LARGE_OR_UNREAD_FILE | 62 |
| TOML_CONFIGURATION | 50 |
| BINARY_OR_MEDIA_FILE | 40 |
| SOURCE_PS1 | 24 |
| SOURCE_SQL | 17 |
| SOURCE_REGO | 16 |
| SOURCE_TSX | 11 |
| JSON_LIST | 6 |
| SOURCE_MJS | 6 |
| SOURCE_GD | 5 |
| SOURCE_JS | 2 |
| SOURCE_Lean | 2 |
| SOURCE_CPP | 1 |

## 60 dense groups and revision drift

Names in the bounded R4 observation seed are hypotheses based on paths; executable and semantic consumers are UNKNOWN.
The annex lists all 60 dense groups and their observed syntax classes. Changes from the earlier source cut:
- region/architecture-documentation/evidence/: 40 to 41 tracked; label architecture-convergence-and-proof-evidence-records
- region/repository-mechanics-source/@rootfiles: 39 to 43 tracked; label repository-verification-selection-and-source-tools

## Separate Git roots and nested Git source

| Observed source | Prior physical role hypothesis | Tracked paths in own Git cut | Standing |
|---|---|---:|---|
| ordivon | PRIMARY_MONOREPO | 4971 | EXACT_LOCAL_GIT_TREE |
| ordivon-media | MEDIA_SEPARATE_SOURCE | 550 | EXACT_LOCAL_GIT_TREE |
| ordivon-research-v2 | RESEARCH_SEPARATE_SOURCE | 2904 | EXACT_LOCAL_GIT_TREE |
| ordivon-paper1-emse-r3-frozen | PAPER1_FROZEN_SOURCE | 673 | EXACT_LOCAL_GIT_TREE |
| ordivon-paper1-r25-reviewer-risk-closure-20260922 | PAPER1_REVIEW_SNAPSHOT | 2646 | EXACT_LOCAL_GIT_TREE |
| ordivon-paper2 | PAPER2_SEPARATE_SOURCE | 1940 | EXACT_LOCAL_GIT_TREE |
| ordivon-r21-blind-eval-private-20261001 | BLIND_EVAL_PRIVATE_CORPUS | 20 | EXACT_LOCAL_GIT_TREE |
| ordivon-r21-blind-eval-public-20261001 | BLIND_EVAL_PUBLIC_CORPUS | 114 | EXACT_LOCAL_GIT_TREE |
| ordivon-sts2mcp | GAME_INTEGRATION_EXPERIMENT | 265 | EXACT_LOCAL_GIT_TREE |
| SillyTavern | UPSTREAM_EXTERNAL_DEPENDENCY | 1010 | EXACT_LOCAL_GIT_TREE |
| oss-e2-uptime-kuma-7984 | UPSTREAM_OSS_CONTRIBUTION | 819 | EXACT_LOCAL_GIT_TREE |
| xby-analysis | OTHER_LOCAL_ANALYSIS_UNCONFIRMED | 84 | EXACT_LOCAL_GIT_TREE |
| lizardbyte-common-sun5870 | OSS_DEPENDENCY_REFERENCE_UNBORN_HEAD | unknown | UNRESOLVED_HEAD |
| sunshine-5870-src | OSS_CONTRIBUTION_SUNSHINE | 621 | EXACT_LOCAL_GIT_TREE |
| uptime-kuma-7984-src | OSS_CONTRIBUTION_UPTIME_KUMA | 819 | EXACT_LOCAL_GIT_TREE |
| e4-neovim-42424-source | OSS_CONTRIBUTION_NEOVIM | 3940 | EXACT_LOCAL_GIT_TREE |
| cli-anything | EXTERNAL_CLI_TOOL_REFERENCE | 1872 | EXACT_LOCAL_GIT_TREE |
| rea | EXTERNAL_TOOL_OR_ALGORITHM_REFERENCE | 5569 | EXACT_LOCAL_GIT_TREE |
| solidcraft | EXTERNAL_GAME_LIBRARY_REFERENCE | 2302 | EXACT_LOCAL_GIT_TREE |

Do NOT sum nested Git counts into parent physical directory file totals. Local monorepo checkout is not current SourceCut. Exact source commits are in the companion report; consumers are not established.

## Other physical source carriers, excluding Git stores and common transient caches

| Physical carrier | Observed files | Excluded cache or Git subtrees |
|---|---:|---:|
| ordivon-corpora | 1500 | 0 |
| ordivon-upstreams | 9738 | 3 |
| paper1-successor-rerun-r1-20260928 | 401 | 5 |
| oss-contrib | 3940 | 4 |

The prior unfiltered paper rerun directory count was much larger because it included an excluded virtual environment; the two numbers do not measure equivalent file sets.

## Remaining Phase 1 classification constraints

1. Parse full content only for currently size-skipped files if evidence materially changes the name. Never treat filename, JSON kind string, Markdown heading, or source location as proof of behavior.
2. Assign actual functional facet, evidence lifecycle, source producer, and real consumers separately. UNKNOWN is a first-class result, not a misc category.
3. Reconcile monorepo branches and independent Research, Paper, Media, OSS and installed Windows/Linux source identities separately. Preserve exact Git cuts and overlap rules.
4. Do not implement LEGO, change proof programs, move directories, or mutate runtime/Host resources during Phase 1.
