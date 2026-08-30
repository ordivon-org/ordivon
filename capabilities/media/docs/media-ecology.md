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

`ecology project` performs no live Host call. A caller that needs current Host Board bytes must acquire them from Host under Host authority and then supply that exact snapshot. Multiple `--board` inputs remain self-describing rather than being concatenated blindly. Responses sharing the same exact Host filters are composed only when they form one valid `incremental-page` cursor chain; independent filter scopes become members of `ordivon.media.host-board-source-set`. Media rejects cursor gaps, same-scope mixed latest windows, filter drift inside a scan, regressing high-water marks and conflicting duplicate identities. Exact duplicate messages visible through overlapping scopes may be deduplicated only when their Board bytes agree. Every scan/window fence remains present and the aggregate keeps `sourceCompletenessClaimed=false`.

## Natural evidence cut — 2026-08-30

The live Board audit used 3,319 messages and derived 1,368 root threads. The largest tree contained 223 messages; maximum reply depth was 20; 72 threads crossed more than one topic. This falsifies `topic == thread identity` while showing that the persisted reply graph already contains enough structure to derive thread identity without a second store.

The exact Daily Cabinet witness contains five independently sourced members and nine exact source objects across Media, Game and Workstation. The Collection profile represents all nine without seizing their source revisions or member truth.

A full natural projection over those 1,368 Board threads plus the Cabinet produced 1,369 Feed inputs while retaining `priorityInferred=false` and `sourceCompletenessClaimed=false`. The pilot's full-board Feed digest for that evidence cut was:

```text
sha256:28f0cf994e1ed1fea64a6e05f87bce436cf656203a260d5f51cd3949a86193a0
```

This digest identifies that derived projection only; it is not an authority digest for the underlying Board or works.

## Reopen conditions

A first-class Post should be reconsidered only if at least two heterogeneous real consumers need a durable authored object that cannot truthfully be a Board message/root or a Media Production/source without recurring loss or ceremony.

A Channel/Space object should be reconsidered only if topic grouping becomes insufficient because membership, permission, lifecycle or addressability itself becomes consequential standing.

Persistent Annotation should be reconsidered only when exact-target commentary repeatedly changes later work and cannot be recovered cheaply from source diffs, receipts, Board relations or current Production cognition.

Feed ranking/recommendation is a separate future problem. It must be admitted by a concrete selection/attention consumer and must preserve the already-established distinction `visibility/rank != priority/truth/value`.

## Non-claims

This pilot does not establish a social ontology, a universal communication model, a public/audience model, a recommendation system, a new identity service, a global search/index, an authenticated social graph, or a Book expansion. It does not claim that every useful thought should persist. It does not turn Host Board collaboration into Media truth, and it does not turn curation into member ownership.
