# GitHub Global Top-1000 Contribution Census R1

Status: CURRENT SNAPSHOT / CAMPAIGN TRIAGE INPUT
Snapshot: 2026-10-17

## Source

- GitHub Search API query: stars:>0, sorted by stars descending.
- Captured exactly 10 pages x 100 rows = 1000 unique repositories.
- Star count is a discovery/ranking signal, not a contribution-value verdict.
- Full inventory: github-top1000-repository-census-r1.json; CSV projection: github-top1000-repository-census-r1.csv.

## Rank boundary

- Rank 1: codecrafters-io/build-your-own-x — 553,724 stars.
- Rank 100: browser-use/browser-use — 118,192 stars.
- Rank 500: ClickHouse/ClickHouse — 50,450 stars.
- Rank 1000: microsoft/WSL — 34,109 stars.

## Mechanical census

- Archived: 25.
- Issues disabled: 38.
- Pushed within 90 days: 810.
- Pushed within 365 days: 895.
- Sum of repository-reported open issue/PR counts: 960,710; median 245. This GitHub field includes pull requests and is not an issue-only count.

## First-pass family classification

- SOFTWARE_OR_TOOL: 844
- KNOWLEDGE_EDUCATION: 86
- DISCOVERY_CATALOG: 48
- AMBIGUOUS: 14
- CONTENT_DATA: 8

## Bug-campaign gate
- ELIGIBLE_SOFTWARE: 750
- EXCLUDE_NONSOFTWARE: 122
- REVIEW: 67
- EXCLUDE_MECHANICAL: 61

ELIGIBLE_SOFTWARE is only a screening gate: active software/tool, Issues enabled, non-archived, and at least one repository-reported open issue/PR. It does not prove maintainer contribution intent or issue validity.

## Domain distribution
- WEB_FRONTEND: 263
- AI_AGENT_ML: 244
- DEVTOOLS_LANG: 89
- KNOWLEDGE_EDUCATION: 86
- GENERAL_SOFTWARE: 70
- DISCOVERY_CATALOG: 48
- SYSTEMS_RUNTIME: 48
- CLOUD_DEVOPS: 42
- MEDIA_CREATIVE_GAME: 33
- MOBILE: 32
- DATA_DATABASE: 21
- SECURITY: 16
- CONTENT_DATA: 8

## Top languages
- Python: 230
- TypeScript: 175
- JavaScript: 105
- NONE: 86
- Go: 77
- Rust: 63
- C++: 41
- Java: 34
- Jupyter Notebook: 24
- Shell: 21
- C: 20
- HTML: 14
- Ruby: 12
- Swift: 10
- Kotlin: 10
- C#: 8
- CSS: 8
- Dart: 7
- Markdown: 6
- MDX: 4

## Top license signals
- MIT: 397
- Apache-2.0: 188
- NOASSERTION: 141
- NONE: 75
- GPL-3.0: 53
- AGPL-3.0: 52
- BSD-3-Clause: 21
- CC0-1.0: 16
- GPL-2.0: 11
- MPL-2.0: 9
- Unlicense: 8
- CC-BY-SA-4.0: 7
- CC-BY-4.0: 6
- BSD-2-Clause: 4
- ISC: 3

## Contribution-profile enrichment

- Community profile coverage: 817/817 candidate-or-review repositories, 0 API errors.
- CONTRIBUTING detected: 572/817.
- Pull request template detected: 436/817.
- Issue template detected by community-profile endpoint: 57/817.
- Community health buckets: {'75-100': 455, '50-74': 235, '0-49': 127}.

## Issue sampling

- Eligible software repositories sampled: 750/750, 0 API errors.
- Open issues retained after removing pull requests: 8897.
- Public bug-candidate seeds after conservative label/title/reproduction triage: 3221 across 608 repositories.
- Security-signal issues removed from public queue: 1590.
- This sample is intentionally not exhaustive: it uses the 30 most recently updated open items per eligible repository. Deep per-repository search happens only after a repository enters an execution wave.

## Campaign implication

The bottleneck is no longer discovery. The next bottleneck is high-quality reproduction and upstream protocol compliance. Do not fan out one patch agent per candidate issue. Admit a bounded wave, reproduce independently, then patch only confirmed issues.
