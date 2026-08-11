# R0-R3 Cultural Observatory acceptance — 2026-08-11

## Question

Can Studio begin observing culture at machine scale, preserve the distinction between artifact structure and attention-world selection, compare winners with controls, and use the result to drive a reversible real creative intervention without requiring a human gate or learning a false popularity law?

## Source boundary

The experiment began from exact source revisions:

- Studio `bbb4e6eaeecb4cbf0ffe03573aa1c35e78b623c8`;
- Web `cb39939ec868385548bb77b97e19c8a324c95dfa`;
- World `8ddbb6a646a77a9180f4d988a23ccbf314aef044`.

World's existing retained-boundary rule rejected a new generic connector layer because Cultural Observatory had only one real consumer. Studio therefore admitted minimal direct adapters and kept their external-provider mechanics replaceable.

## R0 — observation model

Accepted one reference/metadata observation envelope that separates:

```text
artifact identity
selection mechanism
encounter form
available signals
context
acquisition / byte ownership
```

Five focused tests passed before live collection. Credentialed or permissioned sources are projected as `capability-only` instead of being represented by fake live fixtures.

## R1 — live world observation

One live collection produced **840 observations with zero provider failures**:

| Provider | Count | Selection families |
| --- | ---: | --- |
| Hacker News | 400 | 160 top-ranked + 240 non-overlapping new controls |
| Apple Marketing Tools | 100 | Top Songs chart ranks |
| Guardian Open Platform | 340 | section most-viewed + editors' picks + newest controls |

Semantic snapshot identity: `sha256:cf6dba1598ca30cc1566a8d99e33f3f2d330cda4757baba6de8844b579173919`.

The exact 990,011-byte JSON snapshot was admitted to the existing local Studio CAS as:

`sha256:4d730f6d13345a2585eaa971acfeef5d14abaff6c10187b755d08c5769102594`.

No external article body, music track, or video bytes were downloaded into the corpus. Every cultural observation declared `bytesOwned=false`.

## R2 — matched-control and clustering pressure

The deterministic R2 analysis produced eight broad metadata/title neighborhoods and **266 matched pairs**:

- 160 Hacker News `top-ranked ↔ new-control` pairs;
- 106 Guardian `most-viewed ↔ same-section newest-control` pairs.

The largest shallow paired standardized differences were small:

| Feature | candidate − control mean | paired standardized difference |
| --- | ---: | ---: |
| number in title | +0.102 | +0.176 |
| title words | +0.207 | +0.098 |
| parenthetical | +0.030 | +0.097 |
| dash | −0.041 | −0.095 |
| question | −0.019 | −0.052 |
| colon | +0.019 | +0.032 |
| title characters | +0.154 | +0.010 |

This is a useful falsifier: shallow title form does **not** separate the selected groups strongly enough to become an optimization rule.

Apple's top chart quartile was materially more recent than its bottom quartile in the same Top 100 snapshot, while title length and genre-count differences were negligible. Because every item was already selected into a Top Songs chart, this remains rank correlation rather than a winner/loser or causal comparison.

Semantic analysis identity: `sha256:3749ecefc006e1f8b4a5c738485b782fd9c2ac228d30fa6586c14d077f3efc1e`.

The exact 21,295-byte report was admitted to local Studio CAS as:

`sha256:4b2b014d7985c55c3fea5ede10a5bce29c7f9d05d59198c6c986568d6f83b3da`.

A proposed DeepSeek semantic-title probe was **not** forced through Studio after the execution boundary rejected an experiment script that would load local provider secrets directly. The correct next route is Harness/Host provider authority, not a new Studio secret path.

## R3 — reversible Web intervention

R2's strongest shallow signal, numeric title presence, was deliberately used only as a weak hypothesis. The selected Web artifact was the existing article:

`/writing/runtime-after-core`

Baseline title:

`How Ordivon Runtime Grew Beyond Its Ten-Tool Core`

Candidate:

`How Ordivon Runtime Grew Beyond Its 10-Tool Core`

The substitution preserved the factual proposition and changed only one title-form family.

### Render evidence

Baseline source-tree digest:

`sha256:7bc9c5f16e35554a9cda7ca1c337efcf32d9663647ba11e74508815b654e284c`

Baseline viewport pixels:

- desktop: `sha256:e8ce0c867dc6c438a45cef7dcd8eb968db59f10f5f3e10bb9d0c42588c7ca386`;
- mobile: `sha256:75c8bbaf0e3de51f26fc19552eb627c56fc32eb6e3cf5019d2ef91fa9ced34e0`.

Candidate source-tree digest:

`sha256:0a19b009c3bcc36b44b4a90e975e71b7c188418b9a996cd9ac79078d14696c30`

Candidate viewport pixels:

- desktop: `sha256:082b42bd0c030c8c27f7510416f25eca94e9e2b5c2be84143be0fb0fb896bfd8`;
- mobile: `sha256:10d5709d9a4dffd2bf9f73faf9c26fd274a90a58abd24946e4f5a4f8af139b55`.

Both variants passed HTTP/browser/overflow mechanical review at 1440×1000 and 412×915.

Agent pixel inspection found a real but ambiguous compositional difference: desktop kept `10-Tool` together but isolated `Core` on the next line; mobile still broke after `10-`. No observed task, comprehension, attention, or behavioral consequence favored the candidate.

### Decision

**No-op / reject candidate.**

The external matched-control effect was too weak and observational, and render evidence showed only a trade in line-breaking behavior. The article source was restored to the baseline title rather than promoting a change merely because an experiment existed.

This is a positive acceptance for autonomous creative work: the Agent generated, rendered, inspected, compared, and rejected a weak intervention without requiring a human approval gate.

A final rebuild after restoring the baseline title re-materialized the exact original viewport bytes. The final review packet reported source-tree digest `sha256:c322dad4c7c1c250d2853cb9b0bddafe8423419e9a13b570f6ca20b6aaddc89e`, the baseline `Ten-Tool` browser title on both profiles, the same baseline pixel digests above, HTTP 200, and no horizontal overflow. Runtime Job: `job-019fefb0-d33c-79e3-9c9d-84d1795b9a89`.

## Incidental Web falsifiers

The experiment exposed two separate hidden browser-equipment preconditions in disposable Runtime Workspaces.

First, browser review aborted because Chromium's generated `SingletonSocket` exceeded the Unix socket path budget under the long Runtime temporary directory. An explicit short `TMPDIR=/tmp` proved the cause. Web's review tool was changed to detect an overlong ambient temp root, fall back to `/tmp`, and record the effective temp root.

Second, the ordinary Playwright smoke suite tried to resolve a browser inside the disposable Workspace-local cache even though an exact provisioned Chromium already existed in the user's Playwright cache. This made 132 browser-dependent tests fail at launch rather than exercise the site. Web now runs smoke tests through a narrow `run-playwright.mjs` equipment wrapper that discovers an existing provisioned cache, binds `PLAYWRIGHT_BROWSERS_PATH`, and applies the same short-temp invariant instead of downloading a browser per Workspace.

The final `pnpm check` ran with no caller-supplied browser/TMP environment and passed **138/138** Playwright smoke/accessibility tests after publication, type, lint, build, and budget verification. Runtime Job: `job-019fefad-4b22-7232-ab7a-b1bcd66256f3`.

These repairs belong to Web review/test equipment, not to the cultural hypothesis.

## Rejected models

R0-R3 rejects, for now:

- winner-only corpora;
- popularity as aesthetic truth;
- one universal virality score;
- shallow title heuristics as a production optimizer;
- a new generic World connector for one consumer;
- a Studio-local model-provider secret path;
- mandatory human review on every creative iteration;
- mandatory promotion after a successful experiment run.

## What R0-R3 actually establishes

The slow outer loop is no longer only architectural prose. Studio can now acquire a bounded live cultural snapshot, preserve multiple selection mechanisms, construct controls, perform cheap large-sample structural analysis, turn one result into a reversible production hypothesis, inspect the real rendered consequence, and retain `no-op` when evidence is insufficient.

The next pressure is not a larger framework. It is materially richer observations: admitted video/music/article semantics through legitimate provider/perception equipment, semantic decomposition through Harness/Host model authority, and owned-surface consequence data such as retention, CTR, comprehension, or return behavior when those signals become available.
