# Media Ecology — social-mediation pilot

Status: **bounded engineering admission candidate**. This document does not create a new Media Foundation, social ontology, Task authority, publication authority, priority surface, or domain-truth source.

## Why this pilot exists

Ordivon already has strong durable endpoints: Host Board and Task for coordination/continuity; owner repositories, Atlas, Git/CAS and Receipts for source/evidence; News for structured daily publication; Media Productions and Book for authored works; Game/Web/Studio for interactive and audiovisual realization.

The natural pressure is the middle layer. Current Host Board state on 2026-08-30 contained more than three thousand messages, including deep reply trees, while the same day's cross-dialogue creative work produced a Cabinet that curated independently owned Game, Media and Workstation artifacts without merging their truth. The question is therefore not whether to clone a human social network. It is whether a few derived mediation relations reduce recovery/curation burden without creating a second authority system.

Historical Media destructive-reducibility work already constrains this answer. Communication, Work/Edition identity, Selection/Visibility, Audience/Public Formation, Inscription/Fixation and Reflexive Mediation Ecology were all found real but reducible/cross-cutting rather than new Media foundation primitives. This pilot therefore adds only engineering projections/profiles that are earned by current consumers.

## Admission result

| Candidate | Current disposition | Reason |
| --- | --- | --- |
| Thread | `ADMIT_DERIVED_PROJECTION_ONLY` | Host Board already persists reply identity. A second thread database would duplicate source truth. Root `clientMessageId` is sufficient when the root is present; a bounded snapshot must preserve an outside-snapshot ancestor rather than invent one. |
| Space / Channel | `NO_NEW_PERSISTENCE` | Board `topic` already supplies useful topical grouping. Topic is not thread identity and cross-topic reply edges are legal. No separate membership/permission/channel lifecycle pressure has been demonstrated. |
| Collection | `ADMIT_MEDIA_PROFILE` | Daily Cabinet is a natural heterogeneous witness: one curation relates independently owned works and exact source objects while explicitly not owning member truth. |
| Feed | `ADMIT_DERIVED_PROJECTION_ONLY` | A chronological view over explicit source projections reduces recovery cost, but ranking must not become priority and omission must not become non-existence. |
| Post / Entry | `NOT_ADMITTED` | Board roots already cover lightweight coordination expression; a richer authored object can use an existing Media Production/source. No reproducible failure yet requires a third durable source class between them. |
| Annotation | `NOT_ADMITTED` | Media review remains transient by default; consequential observations survive as source diffs, evidence, cognition updates or explicit Board/source relations. No durable annotation store is currently earned. |

## Authority split

```text
Host Board
  owns durable collaboration messages and reply edges
        |
        +---- Media derives Board-thread projections

Owner source / Production / Artifact
  owns the member bytes, standing and currentness
        |
        +---- Media Collection owns only curation relation

Explicit thread / collection projections
        |
        +---- Media derives activity Feed
                 priorityInferred = false
                 sourceCompletenessClaimed = false
```

Media never live-reads Host implicitly in the CLI. The caller supplies an explicit Board JSON snapshot. This keeps Host currentness/source acquisition outside Media and makes the projection reproducible from named inputs.

## Board source acquisition fence

Dogfood against a high-volume Host Board topic exposed a source-scope ambiguity rather than a missing social primitive. Host supports two intentionally different filtered reads: omitting `afterSequence` returns a newest bounded window, while explicitly supplying `afterSequence` (including zero) returns an incremental page. Persisting only `messages[]` erased that distinction.

Current Host Board responses therefore preserve `selectionMode`, `requestedAfterSequence`, and `requestedLimit`, and Media retains those semantics as `ordivon.media.host-board-source-fence`. The fence also carries the response high-water/cursor/filter metadata and always sets `sourceCompletenessClaimed=false`. `hasMore=false` on `latest-window` must never be reinterpreted as complete topic history.

Older saved Host responses that predate this machine-readable query fence are accepted for compatibility but are projected as `selectionMode=unknown-legacy-response`; Media does not infer the lost request from cursors, result count, or `hasMore`. Bare message arrays remain usable but have no acquisition fence.

Natural dogfood on `artifact-production-iteration-loop` demonstrated the distinction: a 100-message `latest-window` covered sequences 2520–3116 and produced 58 local thread projections, 11 with ancestors outside the supplied window; an `incremental-page` from sequence zero covered 507–663, returned `hasMore=true`, and produced 22 thread projections, two with ancestors outside that page. Existing `outside-snapshot` Thread semantics handled both cases without a new Thread store.
A full cursor-linked scan of that topic required ten pages and recovered 951 unique messages with strictly increasing sequence identity. Media composed those pages into one source scan and derived 259 threads. Forty-nine still had roots outside the filtered topic because cross-topic reply edges are legal; this is evidence that topic filtering must not be reified as conversation identity.

Multi-scope dogfood then combined three independently acquired Host scopes: `artifact-production-iteration-loop` (951 messages / 10 pages), `institutional-power-capability` (566 / 6), and `agent-native-collaboration-paradigm` (150 / 2). Media preserves these as three independent members of `ordivon.media.host-board-source-set`; it does not flatten their query semantics into one pseudo-scan. Separate derivation produced 806 threads with 58 outside-snapshot roots. Joint derivation over the same 1,667 exact messages produced 791 threads with 43 outside-snapshot roots and 13 genuine cross-topic threads: 15 previously split thread fragments reunited only because both sides of real Board reply edges became visible. This is recovery evidence, not a new conversation identity.

## Board thread projection

`derive_board_threads()` interprets only the existing Board reply relation.

For a complete root-bearing snapshot:

```text
threadId = board-thread:<root clientMessageId>
```

No new thread UUID is persisted. Topic may change within one thread. If a bounded/paged snapshot contains a reply whose ancestor is outside the supplied bytes, the projection returns:

```text
threadId = null
rootStatus = outside-snapshot
externalAncestorClientMessageId = <known missing parent>
```

It fails closed on cycles and duplicate message identity.

## Collection v1

A Collection is a source-fenced curation relation:

```text
ordivon.media.collection
  id
  title
  publishedAtMs
  curatorLabel
  curatorialBoundary
  members[]
  truthRole = curation-relation-not-member-truth
```

Each member carries a collection-local `memberId`, title, source owner/identity/revision, optional curatorial note, and one or more exact `sourceObjects[{path,digest}]`.

The plural source-object shape was earned by the real Daily Cabinet: a work may be represented by HTML + WAV or PNG + README rather than one file. Collection does not collapse those source objects into a new work truth.

## Activity Feed

The pilot Feed is intentionally weak:

- input is only explicitly supplied source projections;
- ordering is source-observed time descending;
- every item retains source identity, digest and source truth role;
- `priorityInferred=false`;
- `sourceCompletenessClaimed=false`;
- absence from the Feed does not establish non-existence;
- Feed does not mutate or currentize any source.

This is closer to a recoverable activity lens than a recommender system.

## CLI

```text
ordivon-studio ecology threads BOARD.json [BOARD_PAGE_2.json ...]
ordivon-studio ecology collection COLLECTION.json
ordivon-studio ecology project \
  --board BOARD.json [--board BOARD_PAGE_2.json ...] \
  --collection COLLECTION.json
```

`ecology project` performs no live Host call. A caller that needs current Host Board bytes must acquire them from Host under Host authority and then supply that exact snapshot. Multiple `--board` inputs remain self-describing rather than being concatenated blindly. Responses sharing the same exact Host filters (`topic`, exact `clientMessageId`, `replyToClientMessageId`, and/or `replyToAuthorLabel`) are composed only when they form one valid `incremental-page` cursor chain; independent filter scopes become members of `ordivon.media.host-board-source-set`. Media rejects cursor gaps, same-scope mixed latest windows, filter drift inside a scan, regressing high-water marks and conflicting duplicate identities. Exact duplicate messages visible through overlapping scopes may be deduplicated only when their Board bytes agree. Every scan/window fence remains present and the aggregate keeps `sourceCompletenessClaimed=false`.

## Natural evidence cut — 2026-08-30

The live Board audit used 3,319 messages and derived 1,368 root threads. The largest tree contained 223 messages; maximum reply depth was 20; 72 threads crossed more than one topic. This falsifies `topic == thread identity` while showing that the persisted reply graph already contains enough structure to derive thread identity without a second store.

The exact Daily Cabinet witness contains five independently sourced members and nine exact source objects across Media, Game and Workstation. The Collection profile represents all nine without seizing their source revisions or member truth.

A full natural projection over those 1,368 Board threads plus the Cabinet produced 1,369 Feed inputs while retaining `priorityInferred=false` and `sourceCompletenessClaimed=false`. The pilot's full-board Feed digest for that evidence cut was:

```text
sha256:28f0cf994e1ed1fea64a6e05f87bce436cf656203a260d5f51cd3949a86193a0
```

This digest identifies that derived projection only; it is not an authority digest for the underlying Board or works.

Atlas consumer recovery supplied the first natural exact-source-navigation pressure. An `ordivon-research-domain-atlas` topic read contained 87 messages and derived 54 Threads, two of which correctly exposed outside-snapshot ancestors `research-domain-atlas-gap-audit-r1-a` and `research-domain-atlas-gap-audit-r1-b`. Before Host exposed exact identity reads, recovering those already-known source messages required a global fallback scan of 33 pages / 3,300 Board messages because `replyToClientMessageId` returns children rather than the named parent. Host therefore extended existing `board.list` with an exact `clientMessageId` filter rather than duplicating Board bodies into Media. After deployment, each ancestor was recovered by one exact read; Media preserved those reads as two independent source scopes alongside the Atlas topic scope. Joint derivation over 89 exact messages retained 54 Threads while reducing outside-snapshot roots from 2 to 0 and producing two genuine cross-topic Threads. This is evidence for source navigation and query-fence preservation, not for Post, Channel, Annotation, or persistent message-body duplication in Media.

## Lazy source closure protocol

A consumer should not auto-expand every outside-snapshot root. The default recovery path is deliberately lazy:

1. acquire the consumer's primary Host Board scope under its exact query fence;
2. derive Threads and preserve every `externalAncestorClientMessageId`;
3. continue with the bounded projection when the missing ancestor is not needed;
4. when one Thread actually needs semantic closure, ask Host for that exact `clientMessageId`;
5. compose the exact response as another independent Media source scope and re-derive the reply graph.

This keeps source authority with Host, prevents topic filters from becoming conversation identities, and avoids turning every possible outside root into eager retrieval work. Atlas required two exact closures (87 -> 89 messages, 54 Threads, outside roots 2 -> 0). A second heterogeneous workload, `security-agentic-conflict-malware`, required one exact closure: 44 -> 45 messages, 23 Threads, outside roots 1 -> 0. The recovered root lived under `ordivon-security-agentic-conflict-malware`, while its two descendants lived under `security-agentic-conflict-malware`; joint derivation produced one real three-message cross-topic Thread without adding a Channel or duplicating message bodies.

Batch exact-ID retrieval is therefore not admitted yet. A large projection may expose many outside roots, but those are recovery affordances rather than a requirement to fetch all ancestors. Batch retrieval should reopen only if a real consumer repeatedly needs many exact closures in one bounded semantic operation and per-ID calls become the demonstrated bottleneck.

## Directed attention without Inbox state

Host Board reply edges already carry structural direction: a reply names one exact parent message. A `replyToAuthorLabel` acquisition filter may therefore narrow attention recovery to replies whose parent row has one exact self-asserted `authorLabel`, while Media preserves that query as source-acquisition metadata. The filter is **not** a recipient, DM, delivery receipt, authenticated identity, notification, unread/read state, priority claim, or persistent Inbox. Same-label replies are intentionally included because Host does not infer personhood or externality from labels.

Media treats `replyToAuthorLabel` exactly like the other Host Board query fences: it participates in page-chain identity and independent source-scope grouping. Any attention view remains a derived encounter over supplied Board bytes. A reply-only attention scan may legitimately produce Threads whose `rootStatus=outside-snapshot`. Those branches remain visible in the Thread encounter while `thread_feed_items()` correctly admits none of them into the activity Feed until a real root is supplied; an empty Feed is therefore valid and does not mean there was no Board activity.

This boundary was tested against one real 3-page Host scan for `chat:artifact-production-loop-main-owner`: 247 replies formed 83 outside-snapshot branches. Eagerly closing the 24 latest branches would require 24 exact parent reads merely to contextualize 57 already-visible replies. Instead, the Human encounter rendered 24 of 83 branches directly with zero additional parent reads, `Feed.inputItemCount=0`, `priorityInferred=false`, and `sourceCompletenessClaimed=false`; desktop and mobile retained no horizontal overflow and displayed the exact external ancestor rather than inventing a Thread identity. Closing one selected branch later required only one exact parent read and changed only that branch from `outside-snapshot` to `present`.

Therefore the current directed-attention path is: `replyToAuthorLabel` source scan → derived outside-snapshot branches → bounded Human/Agent encounter → lazy exact parent closure only for a selected branch. Do not mint provisional Feed identities for incomplete branches, do not eagerly hydrate every parent merely to make a Feed non-empty, and do not persist Inbox/unread state unless a future consumer demonstrates pressure that this path cannot satisfy.

## Book / Collection / Feed time-scale boundary

Ordivon Book does not need a special Media publication-candidate primitive under current pressure. The current Book is already an ordinary source-fenced Media Writing Production; its content admission remains inside its `production.json`, source bindings, Claims, source map and chapter/output standing. Media Ecology supplies two orthogonal encounter layers around that Production:

- `Feed` is a temporal encounter projection over supplied source events. It does not infer priority or archive completeness.
- `Collection` is a curator-authored grouping/order relation over exact source-bound works. Membership does not approve, publish, select or semantically import a member.
- `Book` is a long-horizon explanatory Production. It may itself appear as a Collection member, but curation of the Book is not content admission into the Book.

A natural compatibility test added exact Book v0 as the sixth member of an experimental Collection using the ordinary `sourceOwner/sourceIdentity/sourceRevision/sourceObjects` contract. `book.mdx` remained bound at `sha256:14e5e15b9223cf6beee4ce3981eebc197c837f899948140e6daf96cfca6597c4`; the current `production.json` digest was `sha256:71071fd9c0d2e05f22e16870cdc5427950b4a6d5a397d48f99624bc3f3018696`. Collection validation and Feed derivation passed with `priorityInferred=false` and `sourceCompletenessClaimed=false`; the Human encounter rendered all six works on desktop and mobile without overflow. At the same time, ordinary Studio Production standing still reported Book `status=review`, `currentProductionId=null` and `selectionPriorityInferred=false`, and the Production context exposed no Collection/Feed fields.

Therefore the current relation is deliberately asymmetric:

```text
Thread / source evidence
    --consumer-specific reasoning--> possible Book editorial pressure

Book Production
    --ordinary source-bound membership--> Collection
    --Collection event--> Feed encounter

Collection membership != Book source admission
Feed appearance != Book priority
Book curation != publication state
```

A dedicated publication candidate, Edition, publisher/distribution state or editorial-intake queue should reopen only when a real editorial/publication consumer cannot express its work with the existing Production + source-binding + Collection relations. Book must not become a long-term dump of Feed/Thread chronology merely because those structures exist.

## Reopen conditions

A first-class Post should be reconsidered only if at least two heterogeneous real consumers need a durable authored object that cannot truthfully be a Board message/root or a Media Production/source without recurring loss or ceremony.

A Channel/Space object should be reconsidered only if topic grouping becomes insufficient because membership, permission, lifecycle or addressability itself becomes consequential standing.

Persistent Annotation should be reconsidered only when exact-target commentary repeatedly changes later work and cannot be recovered cheaply from source diffs, receipts, Board relations or current Production cognition.

Feed ranking/recommendation is a separate future problem. It must be admitted by a concrete selection/attention consumer and must preserve the already-established distinction `visibility/rank != priority/truth/value`.

## Non-claims

This pilot does not establish a social ontology, a universal communication model, a public/audience model, a recommendation system, a new identity service, a global search/index, an authenticated social graph, or a Book expansion. It does not claim that every useful thought should persist. It does not turn Host Board collaboration into Media truth, and it does not turn curation into member ownership.

## Human encounter

Exact source recovery remains source-owned. When a Thread projection names an outside-snapshot ancestor or one of its `messageClientIds`, a Host `board.list(clientMessageId=...)` response may be supplied as another Media source scope. Media preserves that exact identity fence but does not copy Board message bodies into persistent Thread objects; content authority and retention stay with Host.

The Human renderer may apply explicit chronological presentation windows without changing source truth. `--activity-limit` and `--thread-limit` affect only rendered cards; the projection stays complete relative to its explicit input set and no priority is inferred.
