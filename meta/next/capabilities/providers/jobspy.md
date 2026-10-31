# Provider: JobSpy

Status: **PINNED MCP PLUGIN CANDIDATE / PACKAGE SMOKE VERIFIED / LIVE BOARDS UNVERIFIED**
Observed package: `python-jobspy==1.4.1`
Upstream: `speedyapply/JobSpy`
License: MIT
Role: multi-board job discovery fallback after official/structured sources.

## Why Ordivon adopts it

JobSpy already owns the brittle board-specific acquisition logic Ordivon should not reimplement. Upstream publishes a Python library, a `jobspy` CLI and an `mcp-jobspy` server. The MCP surface is intentionally narrow:

- `search_jobs`
- `get_job_details`

The Career-specific GitHub census on 2026-10-31 observed about 4.6k stars, recent 2026-10 maintenance, 32 default-branch commits in the preceding 30-day window and release 1.4.1 in October.

## Direct adoption

The candidate Agent Plugin at `extensions/ordivon-career-discovery/` invokes the upstream package rather than copying its scraper implementation:

```text
uvx --from python-jobspy[mcp]==1.4.1 mcp-jobspy
```

Version pinning is deliberate. Provider-current discovery may recommend a later stable release, but a durable Ordivon execution should not silently float to `latest`.

## Smoke evidence

`meta/next/evidence/career/jobspy-1.4.1-provider-smoke-20261031.json` records an isolated `uv` package smoke. It observed:

- distribution version exactly `1.4.1`;
- console entry point `jobspy = jobspy.cli:main`;
- console entry point `mcp-jobspy = jobspy.mcp:main`;
- `jobspy --help` exit code 0.

No job-board request was made by that smoke.

## Routing precedence

```text
official ATS API / company structured feed
    -> structured JobPosting or official career page
    -> selected provider-native adapter
    -> JobSpy
    -> generic browser/scraping only when justified
```

JobSpy therefore does not displace Greenhouse/Lever/Ashby or other first-party interfaces when those are available.

## Authority and safety boundary

JobSpy owns acquisition mechanics for its supported boards. External sites remain authoritative for their live content and policies.

A successful JobSpy query means only that the provider returned an observation. It does **not** prove:

- the vacancy is still open;
- the listing is complete or unique;
- scraping is permitted for the caller/region/board;
- the employer received an application;
- a rank/match score predicts hiring;
- future calls will remain compatible with anti-bot behavior.

Proxy credentials, if ever needed, must remain execution-time secrets and must not be written into the portable plugin package.

## Ordivon ownership

Ordivon owns source selection, normalization, evidence/currentness labels, deduplication semantics, downstream role/evidence reasoning and acceptance. Runtime/Host own durable execution and evidence. Career does not copy JobSpy HTTP/scraper internals into Core.
