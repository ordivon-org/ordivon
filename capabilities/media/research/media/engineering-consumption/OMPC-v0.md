# OMPC-v0 — Ordivon Media Projection Contract

**Status:** technology-neutral reference contract / first dogfood candidate. Not a production schema, API, database model, SDK or protocol.

## Purpose

OMPC-v0 defines the minimum semantic responsibilities required when source-owned truth is projected into an observer-facing Media representation without transferring source authority to Media.

The contract is intentionally role-based rather than field-name-based.

## Six semantic roles

### 1. SourceBinding

Identifies the source owner, referent and exact source fence used by the projection. Owner-specific authority/currentness semantics remain external truth; Media references them rather than inventing a universal `current=true` flag.

### 2. ObserverScope

States the intended observer, purpose and relevant capability/context boundary. Different observers may receive different representations of the same source.

### 3. ProjectionEnvelope

Declares which source claims/relations/state are selected into the projection and what scope those selected claims retain. Selection never transfers authority.

### 4. RepresentationBody

The actual observer-facing realization: text, structured object, HTML, diagram, audio, video, scene, tool result or another medium. Representation bytes may differ radically across observers.

### 5. Transformation / ProvenanceTrace

Records the lineage from source binding through selection, compression, rephrasing, transformation and realization. It declares material omission, semantic loss or unresolved transformation risk.

### 6. ActionExposure / Disclosure

Describes any action affordance shown by the projection and names the external authority responsible for admission/execution. It also carries material currentness, omission, uncertainty and owner-boundary disclosures.

## Binding invariants

1. **Source Authority Conservation** — projection is never source authority.
2. **No Semantic/Standing Lifting** — a projection cannot make a source claim stronger, broader, more final or more authoritative than the source.
3. **Exact Fence Traceability** — the projection can identify the exact source fence from which it was derived.
4. **Observer Relativity** — distinct observers may receive distinct realizations without implying distinct source truths.
5. **Loss/Omission Disclosure** — material compression or omitted source regions are discoverable rather than silently presented as exhaustive source knowledge.
6. **Currentness Non-Fabrication** — Media cannot declare a source fence current merely because a projection is recently rendered or available.
7. **Action Non-Execution** — displayed affordance, requested action, external admission and committed effect are distinct states.
8. **Cross-Modality Semantic Equivalence** — projections in different modalities may differ in bytes/form, but shared source claims, source fence, authority boundary and material uncertainty must remain equivalent.

## Negative laws

OMPC-v0 rejects these equivalences:

```text
projection == source truth
latest render == current source
visible metric == underlying reality
affordance == authorization
request == admission
success presentation == committed effect
summary == exhaustive source
same source == same observer representation
```

## First fixture family

The first dogfood binds one exact Ordivon Host Task revision and creates:

- a Human/Web-oriented projection;
- an Agent/structured projection.

Both projections bind `task:ordivon-media-project-inception-m0-m1-20260818` at Host revision `3`, with checkpoint digest `sha256:695cf6a3cba795a3a93c774c65517b6741f093fd953d6ca20978fcffff7988b0`.

See `fixtures/host-task-rev3-human.md`, `fixtures/host-task-rev3-agent.json`, and `fixtures/host-task-rev3-dogfood.md`.

## Extraction gate

Passing this fixture does not admit shared Media code. A shared implementation capability requires repeated structurally equivalent pressure from materially different real consumers, with owner-local duplication or boundary failure demonstrated first.

## M2 refinement — identity and locator non-collapse

Studio transformation dogfood exposed a distinction that OMPC-v0 must state explicitly without adding a new implementation object or schema primitive.

A projection or transformation lineage may involve several independent identities:

```text
source / authority identity
semantic Production / Asset identity
exact Blob byte identity
realization / transformation relation
current recovery locator
```

None is generally interchangeable with another.

- a repository/path rename may change a current recovery locator without changing an exact historical source fence;
- an Asset may retain a semantic production role while selecting different Blob bytes;
- different source Blob bytes may produce byte-identical output under a transformation;
- a rendered Output may have an exact Blob identity while not preserving the editable/source structure from which it was rendered.

### 9. Identity Non-Collapse

OMPC projections and transformation traces MUST NOT use one identity class as silent proof of another. In particular:

```text
same semantic ID != same bytes
same bytes != same semantic standing
same rendered bytes != same editable source
same current locator != same historical owner identity
repository/path rename != source-fence rewrite
```

This refinement strengthens `SourceBinding`, `RepresentationBody`, and `Transformation / ProvenanceTrace`; it does not admit a seventh semantic role.

## M3 refinement — temporal coverage non-collapse

Web interaction dogfood shows that endpoint-equivalent projections may still represent semantically different encounters when intermediate action, state, latency or feedback carries meaning.

### 10. Temporal Coverage Non-Collapse

A projection that supports an encounter/trajectory-level claim MUST disclose the temporal coverage on which that claim rests. Matching initial/final state cannot silently stand in for the omitted trajectory when intermediate state/action/feedback may be material.

```text
same initial state + same final state != same encounter
static endpoint coverage != trajectory coverage
omitted transient feedback != evidence of its absence
```

This strengthens `ProjectionEnvelope`, `RepresentationBody`, and `Transformation / ProvenanceTrace`; it does not add a seventh role or a Media event runtime.
