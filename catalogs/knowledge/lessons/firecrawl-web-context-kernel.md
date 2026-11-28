# Firecrawl Web Context Kernel — extracted design lessons

Status: **REGISTERED / PROTOTYPE-READY**  
Registered: 2026-09-14

## One-sentence model

**Firecrawl is a web-context pipeline: discover web sources, acquire them through the cheapest reliable engine, normalize them into clean agent-ready representations, and scale the same primitive from one page to bounded asynchronous site crawls.**

## Why this matters to Ordivon

Most Agent tasks that need the web do not actually need an interactive browser. They need **current, usable context** from the web.

Firecrawl demonstrates that web access is better decomposed into distinct concerns:

- discovery;
- acquisition;
- rendering;
- cleaning/normalization;
- site mapping;
- bounded crawling;
- structured extraction;
- interaction only when necessary to reveal data.

This gives Ordivon a cleaner routing boundary than treating every live-web problem as browser automation.

## Mechanism 1: separate discovery from acquisition

A query and a URL are different starting conditions.

### Query-first

`query -> Search -> candidate sources -> Scrape selected sources`

### URL-first

`known URL -> Scrape`

### Site-first

`site/domain -> Map -> choose pages OR Crawl`

Do not crawl an entire site merely because the target URL set is unknown. Map first when URL discovery alone may answer the planning problem.

## Mechanism 2: acquisition should use the cheapest reliable engine

Not every page needs Chromium.

A sensible engine strategy is conceptually:

```text
plain fetch
   ↓ if insufficient
browser render / Playwright/CDP
   ↓ if insufficient
specialized hosted/proxy/anti-bot engine
```

Engine selection belongs to the web-acquisition provider, not to Ordivon's global architecture.

General lesson:

**Escalate rendering complexity only when the observed page requires it.**

## Mechanism 3: normalize before giving content to an Agent

Raw HTML is usually a poor Agent context format because it includes navigation, scripts, CSS, ads, duplicated chrome and other irrelevant tokens.

Useful normalization is:

```text
raw/rendered page
      ↓
main-content selection
      ↓
clean structure
      ↓
Markdown / JSON / metadata
      ↓
Agent / downstream system
```

The important design goal is not Markdown itself; it is **token-efficient preservation of the source information needed for the task**.

Keep source URL and metadata with the normalized representation so provenance is not lost during cleaning.

## Mechanism 4: Map and Crawl solve different problems

### Map

Answers:

> What pages appear to exist on this site, and which are relevant?

It can combine sitemap, discovered links, cached/indexed URLs and relevance filtering without fully ingesting every page.

### Crawl

Answers:

> Acquire a bounded set of pages by recursively following the site's link structure.

The distinction matters because URL discovery is much cheaper than page rendering/extraction.

## Mechanism 5: a crawler is a bounded frontier, not a magical recursion

The minimal crawler state is:

```text
frontier queue
seen set
scope/filter policy
page/depth limits
results/errors
job state
```

Loop:

```text
pop URL
  ↓
acquire + normalize
  ↓
extract links
  ↓
normalize/filter/dedupe
  ↓
enqueue unseen URLs
```

Keep crawl controls explicit:

- domain/subdomain scope;
- include/exclude paths;
- depth;
- page limit;
- URL deduplication;
- cancellation;
- concurrency.

This is enough to implement a prototype. The difficult production work is reliability, rendering and scale, not the graph traversal primitive.

## Mechanism 6: known URL sets should use batch acquisition

If URLs are already known, batch scrape is conceptually cleaner than pretending the task is a crawl.

Choose the operation according to uncertainty:

```text
one known URL -> scrape
known URL list -> batch scrape
unknown site URL set -> map
need bounded content corpus -> crawl
unknown web sources -> search
```

This reduces unnecessary orchestration.

## Mechanism 7: interaction is subordinate to data acquisition

Firecrawl now supports click/scroll/write/wait-style interaction before extraction. The important boundary is **why** interaction is occurring.

If the interaction is merely a deterministic step to reveal the desired content:

`interact -> extract context`

then it still fits Firecrawl.

If the desired result is itself a stateful UI effect requiring adaptive reasoning, such as navigating an account application, editing settings, making a purchase or dealing with unknown multi-step UI state, use an agentic browser provider such as Browser Use instead.

This prevents capability overlap from turning into architectural ambiguity.

## Mechanism 8: acquisition success is not source truth

A reliable scraper can faithfully return unreliable information.

Keep these predicates separate:

```text
page acquired successfully
!=
content is current
!=
source is trustworthy
!=
evidence is sufficient for a claim
```

Research and decision workflows must evaluate source quality independently of Firecrawl execution status.

## Mechanism 9: web context is an external/untrusted input surface

Fetched web content may contain:

- malicious instructions / prompt injection;
- tracking and hidden content;
- private/personal data;
- manipulated metadata;
- adversarial links.

Therefore:

- preserve the distinction between web content and Agent/system instructions;
- constrain downstream tools independently;
- respect robots/site policies and applicable terms/law;
- keep credentials/provider auth out of scraped content;
- avoid automatically turning scraped links/text into privileged actions.

## Mechanism 10: self-hosting changes the problem

A prototype web scraper is small. A production web-context platform is not.

The current upstream self-host stack includes multiple operational components around API/workers, browser rendering, queues, cache/datastore and optional backends.

Therefore the correct question is not:

> Can Ordivon self-host Firecrawl?

but:

> Is there a concrete requirement that justifies Ordivon owning availability, upgrades, capacity, persistence, network security and scraping-engine operations?

Default answer should remain **no** until evidence says otherwise.

## Relationship to Browser Use

The cleanest distinction is:

```text
Firecrawl
web -> context/data

Browser Use
web UI -> adaptive actions/effects
```

Examples:

- “Read these 200 product pages and build a dataset” -> Firecrawl;
- “Find all docs pages and ingest them” -> Map/Crawl;
- “Search for current competitors and read the top sources” -> Search + Scrape;
- “Log into this dashboard and change the billing setting” -> Browser Use;
- “Run this known UI regression flow” -> Playwright.

## Relationship to Research

Firecrawl can be a Research acquisition provider, but it is not the Research methodology.

A research workflow may use:

```text
research question
    ↓
source strategy
    ↓
Search / Map / Crawl / Scrape
    ↓
clean source material
    ↓
quality appraisal / synthesis / analysis
    ↓
claim + evidence
```

Do not mistake corpus acquisition for literature review, causal inference or scientific validation.

## What Ordivon should not copy

- scraping-engine waterfall internals;
- browser pools;
- proxy/stealth infrastructure;
- rate-limit and credit systems;
- crawl job queues/workers;
- Redis/PostgreSQL/RabbitMQ/FoundationDB topology;
- content-cleaning implementation details;
- hosted index/search infrastructure;
- model-provider abstractions inside extraction/agent features.

These are mature provider responsibilities.

## What Ordivon should retain

1. **Route web work by desired output: context/data vs interactive effect.**
2. **Separate discovery from acquisition.**
3. **Escalate fetch -> browser -> specialized engine only as needed.**
4. **Normalize noisy external state before placing it in Agent context.**
5. **Map before Crawl when site structure may be enough.**
6. **Model crawling as a bounded queue/frontier with explicit scope.**
7. **Use batch acquisition when URLs are already known.**
8. **Keep source provenance attached to normalized content.**
9. **Acquisition success does not establish source truth or evidential sufficiency.**
10. **Hosted mature infrastructure is preferable to self-hosting until a real requirement justifies ownership.**

## Minimal prototype

A small prototype can be implemented with:

```text
Search provider (optional)
       |
       v
HTTP fetch ----fallback----> Playwright
       |                         |
       +-----------+-------------+
                   v
               raw HTML
                   v
          main-content cleaner
                   v
           Markdown converter
                   v
        URL + metadata + content
```

Add:

```text
Map = sitemap + links + normalize + dedupe
Crawl = Map-like discovery + bounded queue + Scrape
```

No LLM is required for the core prototype. Semantic structured extraction can be layered later.

## Project-study acceptance

### One-sentence test

PASS: Firecrawl is a web-context pipeline that discovers, acquires, cleans and scales live-web content into Agent-ready data.

### Prototype test

PASS: the search/scrape/map/crawl primitives and fetch/render/clean pipeline are explicit enough to implement a minimal compatible concept without studying the production queue/proxy/browser internals further.

## Verdict

**PASS — USE AS WEB CONTEXT PROVIDER + EXTRACT ROUTING/NORMALIZATION RULES.**

Further study should be demand-driven around a real need such as self-hosting, large-scale crawling, anti-bot reliability, compliance, authenticated data acquisition or a specific Firecrawl Agent/Interact feature.
