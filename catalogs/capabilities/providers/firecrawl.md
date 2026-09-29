# Provider: Firecrawl

Status: **PROTOTYPE-READY / USE FOR WEB CONTEXT ACQUISITION**
Role: web search, acquisition, rendering, cleaning, crawling and structured-context provider for agents and applications.

## One-sentence understanding

**Firecrawl turns live web sources into agent-ready context by discovering URLs, acquiring pages through fetch/browser engines, normalizing noisy content into Markdown/structured outputs, and orchestrating site-scale crawl jobs behind one API.**

## When Ordivon should route work here

Prefer Firecrawl when the desired outcome is primarily **web data/context**, for example:

- turn one or many URLs into clean Markdown or structured data;
- search the web and immediately obtain page content;
- discover a site's URL structure;
- crawl a documentation/product/news site into a corpus;
- batch scrape many pages;
- parse web-hosted documents;
- gather current public-web evidence for Research, competitive analysis, enrichment or knowledge ingestion;
- perform a small amount of scripted page interaction only to reveal content before extraction.

Prefer another provider when the task is mainly:

- a simple public URL already readable through ordinary HTTP/fetch;
- a known deterministic browser test/workflow -> Playwright;
- an unknown, stateful, logged-in or transactional UI task where the Agent must repeatedly reason about browser state -> Browser Use;
- API/SaaS integration or recurring event automation -> native connector/n8n;
- whole-desktop GUI interaction -> Computer Use.

## Core primitives

### Search

Discover relevant public-web sources from a query, optionally returning scraped content with the results.

Conceptually:

`query -> ranked URLs -> acquire/clean selected pages -> agent-ready context`

Search is a discovery primitive, not an authoritative truth source; downstream work still evaluates source quality and freshness.

### Scrape

Scrape is the central single-source primitive:

`URL -> acquisition engine -> rendered/raw content -> main-content cleaning -> requested formats + metadata`

Useful outputs include Markdown, HTML/raw HTML, structured JSON, screenshots and metadata. The value is normalization: callers should not need to own site-specific rendering, boilerplate removal and format conversion for every target.

### Acquisition engine / fallback

Page acquisition is provider-owned. A mature implementation may choose between plain fetch, Chromium/Playwright/CDP and additional hosted engines/proxies/stealth strategies depending on page behavior and deployment.

Ordivon should request the desired web context, not encode a universal scraper-engine selection policy.

### Map

Map discovers URLs/site structure without necessarily fully scraping every page.

Typical sources include:

- sitemap data;
- page links;
- Firecrawl's existing URL index/cache;
- URL normalization/deduplication;
- optional relevance search/filtering.

Use Map before Crawl when the real task is to understand or select site structure rather than ingest everything.

### Crawl

Crawl is an asynchronous bounded frontier over a site:

```text
seed URL
   ↓
discover candidate URLs
   ↓
normalize/filter/dedupe
   ↓
queue/frontier
   ↓
scrape page
   ↓
discover more links
   └───────────────> frontier
```

The job stops according to configured path/domain/depth/limit/cancellation rules. Crawl status, partial results and failures belong to the Firecrawl job authority.

### Batch scrape

When the URL set is already known, prefer batch scrape instead of constructing a crawl merely to visit those URLs.

### Parse / document ingestion

Web context is not only HTML. Provider-level parsing of PDF/DOCX and similar sources belongs here when the goal is usable text/context rather than native-document editing.

### Structured extraction / Agent

Structured extraction is a semantic layer over acquired context. Current Firecrawl is moving older standalone `extract` behavior toward its `/agent` capability for higher-level autonomous data gathering.

Treat this as optional semantic extraction, not a replacement for Ordivon's Research/decision reasoning. When a deterministic schema over known pages is enough, use the narrowest scrape/structured-output feature available.

### Interact / scrape actions

Firecrawl can perform browser actions such as click, scroll, write and wait before extraction. This is useful when a deterministic interaction is needed to expose data.

Do not automatically route open-ended browser-operation tasks here merely because interaction exists. If the primary problem is adaptive UI operation, Browser Use remains the clearer provider boundary.

## Web-provider routing rule

Prefer the thinnest interface that satisfies the task:

```text
native API / direct HTTP
        ↓ if insufficient
Firecrawl scrape/search/map/crawl
        ↓ if deterministic UI interaction is needed
Playwright / Firecrawl actions
        ↓ if adaptive stateful browser reasoning is needed
Browser Use
        ↓ if outside-browser GUI is needed
Computer Use
```

For site-scale data acquisition, Firecrawl may be preferred directly over local browser automation because it already owns crawl frontier, normalization, retries, rate limiting, rendering and extraction concerns.

The machine-readable `web-interaction-r1` profile deliberately distinguishes **studied/known** from **currently available**. On the 2026-09-14 local census no Firecrawl executable/service is admitted, so a site-scale acquisition request returns `NO_ADMITTED_PROVIDER` unless the current caller supplies a real connected Firecrawl capability; it is not silently rewritten into a loop of local HTTP fetches.

## Authority boundary

Firecrawl owns:

- acquisition-engine choice;
- rendered/raw page retrieval;
- crawl/map job state;
- crawl frontier/deduplication;
- web-content normalization;
- provider retry/rate-limit/proxy mechanics;
- Firecrawl execution/job history.

External websites remain authoritative for their live content.

Ordivon owns:

- why the context is needed;
- source-quality requirements;
- provider selection;
- downstream domain reasoning;
- acceptance/verification of the actual research/business outcome.

A successful scrape/crawl only establishes acquisition success; it does not establish that the sources are correct, complete, unbiased or sufficient for the domain claim.

## Hosted vs self-hosted

Default to a hosted/mature Firecrawl provider when web-context acquisition is needed and policy permits it.

Self-hosting is a significant operational commitment: the current upstream stack includes API/workers, browser scraping, queue/datastore/cache components and optional queue backends. Self-host only when a real requirement such as data control, custom engines, economics, policy or scale justifies owning those operational responsibilities.

Do not pull Firecrawl's queue/browser/proxy/datastore architecture into Ordivon merely to avoid an external API.

## License boundary

The main Firecrawl server repository is primarily AGPL-3.0; SDKs and some client/UI components use more permissive licenses such as MIT. Use Firecrawl as an external provider or review component-level licensing before incorporating source into a commercial Ordivon product.

## Prototype recipe

A minimal Firecrawl-like prototype is sufficient to demonstrate the architecture with four operations:

### Scrape

1. accept a URL;
2. fetch it directly when possible, otherwise render with Chromium/Playwright;
3. obtain final HTML and metadata;
4. remove obvious boilerplate/non-main content;
5. convert the selected content to Markdown;
6. return source URL, title/status and Markdown.

### Map

1. read sitemap when available;
2. collect same-domain links from seed pages;
3. normalize URLs;
4. deduplicate and filter;
5. return the URL inventory.

### Crawl

1. seed a bounded queue with the starting URL;
2. pop URL -> scrape -> emit result;
3. extract links -> normalize/filter/dedupe -> enqueue unseen URLs;
4. enforce domain/path/depth/page limits;
5. expose job status/results/errors until completion.

### Search

1. use a search provider to obtain ranked URLs;
2. optionally scrape the top results;
3. return search metadata plus clean page context.

This prototype is enough to understand Firecrawl. Production reliability comes from the mature provider's renderer fallbacks, anti-bot/proxy handling, concurrency, queues, retries, caching, document parsing, observability and hosted infrastructure; Ordivon should normally consume those rather than rebuild them.

## Prototype readiness gate

**PASS.** Search, scrape, map, crawl, acquisition, normalization and async-job boundaries are understood well enough to implement a small functional prototype and to route real workloads to Firecrawl without further architectural study.
