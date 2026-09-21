# Creative capability and works index — core design

## Core rule

Do not create a second truth store.

```text
owner-native registries
        ↓ ingest
entities + typed relations + evidence
        ↓ stitch
rebuildable Creative Index
        ↓ query
Agent / human production decisions
```

The index is disposable. Media Equipment World remains equipment/capability authority; Production and Collection records remain work authority; Artifact remains delivery-profile and consumer-acceptance authority; Workstation remains physical equipment authority. Creative Library is hosted by Media as a rebuildable cross-domain catalog/presentation projection; it does not acquire work identity or source-byte authority.

## Minimal entities

- `Equipment` — a tool or target renderer named by an owner.
- `Capability` — one operation an Equipment entry declares.
- `DeliveryProfile` — one Artifact delivery contract/profile.
- `Work` — one formal Production or curated work identity.
- `Evidence` — consumer acceptance or other bounded execution/creative-library evidence.
- `Source` — the exact repository/revision from which projection facts were read.

## Minimal relations

- `provides`: Equipment → Capability.
- `canFeed`: Capability → DeliveryProfile, from the small Media-owned bridge list.
- CAD follows the same owner split: Media may expose `cad.export.step`, while Artifact owns the bounded `design-3d-step-solid-r1` STEP verification profile and its `LOCAL_LIVE_PROVEN` FreeCAD/OCCT evidence. This relation does not claim assembly, PMI/GD&T, BIM, manufacturing, or universal CAD graduation.
- `renders`: target renderer Equipment → DeliveryProfile.
- `evidencedBy`: Equipment or DeliveryProfile → Evidence.
- `sourcedFrom`: any projected entity → Source.

Relations are directional and evidence-addressed. Missing edges remain unknown; the builder does not infer them from similar names.

## Why a bridge exists

Artifact profiles do not and should not know all Media capabilities. Media capabilities do not and should not redefine Artifact format semantics. `research/media/creative-delivery-bridges.json` therefore contains only compatibility edges between the two owner domains. It is small, reviewable, and replaceable.

## Works projection

Workstation Creative Library is consumed as a source-complete navigation catalog, not copied as a second archive. Each catalog work becomes a lightweight `Work` projection with identity, title, owner, source revision/path, modality/standing metadata and carrier counts. The thousands of carrier rows remain in the Workstation catalog and are never copied into the Creative Index.

When a Work already exists from a Media Production or Collection, owner-native fields win. The Workstation catalog is attached only as `catalogProjection` plus membership. Explicit `DERIVATIVE_OF` and `CONSUMER_OF` catalog relations become `derivativeOf` / `consumerOf` graph edges; no lineage is inferred from names or paths.

Derived-preview evidence remains separate from Work identity. When Workstation explicitly records exact carrier digests, shared-geometry byte equality, preview-source identity or generation evidence, the index keeps those bounded fields on the `Evidence` node; it does not promote a preview into an original carrier or physical-behavior claim.

## Standing

There is deliberately no mutable `PROVEN=true` field. A caller derives standing from graph facts:

- declared capability: an Equipment `provides` it;
- deliverable path: Capability `canFeed` a present DeliveryProfile;
- consumer evidence: the Equipment/Profile has `evidencedBy` consumer acceptance;
- known work: a `Work` node exists independently of capability standing.

Physical availability remains a fresh Workstation/Runtime observation and is not frozen into this durable projection.

## Commands

```bash
python scripts/build-creative-index.py \
  --artifact-root /root/projects/ordivon/capabilities/artifact \
  --creative-library-root . \
  --output /tmp/ordivon-creative-index.json

python scripts/build-creative-index.py \
  --artifact-root /root/projects/ordivon/capabilities/artifact \
  --creative-library-root . \
  --query asset.export.gltf
```

The output is disposable cache/navigation data and is not committed as source. The Studio Agent query builds a fresh projection on demand and returns a bounded three-hop neighborhood around lexical matches. `Source` nodes are provenance terminals: they may appear in results but are never traversed as graph hubs. Explicit output is only for inspection/export.
