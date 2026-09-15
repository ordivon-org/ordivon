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

The index is disposable. Media Equipment World remains equipment/capability authority; Production and Collection records remain work authority; Artifact remains delivery-profile and consumer-acceptance authority; Workstation remains physical equipment/creative-library authority.

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
- `renders`: target renderer Equipment → DeliveryProfile.
- `evidencedBy`: Equipment or DeliveryProfile → Evidence.
- `sourcedFrom`: any projected entity → Source.

Relations are directional and evidence-addressed. Missing edges remain unknown; the builder does not infer them from similar names.

## Why a bridge exists

Artifact profiles do not and should not know all Media capabilities. Media capabilities do not and should not redefine Artifact format semantics. `research/media/creative-delivery-bridges.json` therefore contains only compatibility edges between the two owner domains. It is small, reviewable, and replaceable.

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
  --artifact-root /root/projects/ordivon-artifact-v2 \
  --workstation-root /root/workstation-lab \
  --output /tmp/ordivon-creative-index.json

python scripts/build-creative-index.py \
  --artifact-root /root/projects/ordivon-artifact-v2 \
  --workstation-root /root/workstation-lab \
  --query asset.export.gltf
```

The output is disposable cache/navigation data and is not committed as source. The Studio Agent query builds a fresh projection on demand; explicit output is only for inspection/export.
