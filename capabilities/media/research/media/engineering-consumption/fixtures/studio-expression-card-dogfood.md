# OMPC-v0 Fixture B — Studio transformation / provenance dogfood

## Why this fixture is materially different

Fixture A tested one Host continuity truth projected into different observer surfaces. Fixture B uses a real Studio Production and stresses a different axis:

```text
exact historical source Claim
→ semantic Production / Asset identities
→ exact editable-source Blob
→ declared transformation
→ exact rendered Output Blob
→ lifecycle / publication standing
```

The source is `productions/studio-expression-card/`, introduced by Git commit `1061d740c01aec9272fd3bc50bdbf8a32da2c1b1`. The Production binds historical Ordivon Studio revision `90e2b5d46b0f16171d242633454714017a14f2f2`.

The repository has since undergone the M0 owner inversion and is currently recovered at `/root/projects/ordivon-media`. The current locator and owner topology do not rewrite the historical source fence.

## Grounded lineage

### Historical source fence

- bound source identity recorded by the Production: `ordivon-studio`;
- exact bound Git revision: `90e2b5d46b0f16171d242633454714017a14f2f2`;
- the bound commit is present and is an ancestor of observed Media main `10a17e94945f0fea0fb839dd819e1a3c491b23c2`;
- all Claim source/evidence paths tested for this fixture exist at the bound revision.

This is mechanical Git relation only. The fixture does not infer floating current semantic applicability from ancestry.

### Editable source

- Semantic Asset ID: `studio-expression-card-svg`
- Role: `editable-vector-source`
- Exact Blob: `sha256:a8ed35e9f9e4ab993a9e62ad6935e4a111eba3c391ea1854e954036364824128`
- Size: 4,532 bytes
- Media type: `image/svg+xml`

The live file hash exactly matches `assets.json`.

### Selected rendered realization

- Semantic Asset ID: `studio-expression-card-png`
- Role: `selected-publishable-card`
- Parent Asset: `studio-expression-card-svg`
- Renderer: `rsvg-convert` at 1200×630
- Exact Blob: `sha256:fc19d4cf27982fd177c9411245fb994a970551e105866348ee03e9deed6bcce4`
- Size: 115,196 bytes
- Media type: `image/png`

The exact selected PNG is also the Production Output `studio-expression-card-publishable`, whose Output status is `approved` while the parent Production status remains `review`.

## Destructive tests

### B1 — Historical source fence survives owner inversion — PASS

The Production remains bound to exact Studio revision `90e2b5d...`. Current project recovery occurs through `/root/projects/ordivon-media` after owner inversion. The locator change does not rewrite the old Claim to current Media authority.

Retained law:

```text
current recovery locator != historical source identity/fence
```

### B2 — Semantic identity and Blob identity remain distinct — PASS

`studio-expression-card-svg` and `studio-expression-card-png` are semantic Asset IDs with production roles. Their selected Blobs have separate exact SHA-256 identities. Studio's existing model explicitly permits an Asset to select a different Blob without pretending the previous bytes never existed.

Retained law:

```text
semantic Asset identity != exact Blob identity
```

### B3 — Declared transformation lineage is mechanically reproducible — PASS

A fresh `rsvg-convert --width 1200 --height 630` render from the exact tracked SVG produced the exact selected PNG digest:

`sha256:fc19d4cf27982fd177c9411245fb994a970551e105866348ee03e9deed6bcce4`.

The rerender was byte-identical to the committed Output.

This proves this bounded transformation path is reproducible in the observed environment. It does not make the Output source-owner truth.

### B4 — Different source Blob bytes can yield the same rendered Output bytes — PASS

A temporary copy of the real SVG received one XML comment only. Its source Blob digest changed from:

`sha256:a8ed35e9...` → `sha256:71ad25b5...`

Rendering that byte-different source with the same renderer/settings still produced the exact selected PNG digest `sha256:fc19d4cf...`.

Retained law:

```text
source Blob identity != rendered realization identity
```

Scope is deliberately narrow: an ignored XML comment under this renderer is not evidence that arbitrary byte-different SVGs are semantically equivalent.

### B5 — Rendered realization does not preserve editable-source structure — PASS

The SVG source mechanically exposes 59 XML/SVG elements and 19 non-empty text nodes. The selected Output is a 1200×630 RGB raster PNG.

The PNG preserves the selected rendered appearance, not the SVG element tree/text/vector edit structure as an editable source.

Retained law:

```text
rendered Output != editable source
```

This is a concrete `Loss/Omission Disclosure` case: successful transformation can intentionally discard source structure.

### B6 — Output approval does not lift Production standing — PASS

`production.json` records:

```text
Production.status = review
Output.status = approved
```

OMPC must preserve that distinction. One approved deliverable does not imply the whole Production is published or closed.

Retained law:

```text
approved realization != published/closed Production
```

### B7 — Byte reproducibility does not currentize semantic authority — PASS

The selected PNG can be reproduced exactly today, while its Claim remains bound to historical Studio revision `90e2b5d...` and the repository/project owner has since become Ordivon Media.

Retained law:

```text
reproducible bytes != current source authority
```

## OMPC consequence

Fixture B does not require a new seventh OMPC role. It does require an explicit **Identity Non-Collapse** invariant spanning SourceBinding, RepresentationBody, and Transformation/ProvenanceTrace:

- source/authority identity;
- semantic Production/Asset identity;
- exact Blob identity;
- realization/transformation relation;
- current recovery locator;

must not silently substitute for one another.

## Extraction decision after Fixture B

Fixture A and Fixture B both independently require:

- exact source binding/fencing;
- observer/projection scope;
- provenance/lineage;
- omission/loss disclosure;
- authority/standing non-lifting.

That is meaningful repeated pressure, but still only two consumer shapes. **No shared Media implementation is admitted yet.** A third materially different fixture should test another direction—preferably Runtime operational state projection or a Web interactive state/action trajectory—before implementation extraction.
