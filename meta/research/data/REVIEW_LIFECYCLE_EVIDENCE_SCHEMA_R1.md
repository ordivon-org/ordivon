# Review Lifecycle Evidence Schema R1

The shared unit is not a reviewer score. It is a typed evidence relation.

```text
Concern
  |\
  | \ ARIES: annotated correspondence
  |  -> Revision
  |
  +---- DISAPERE: explicit local context ----> Response
```

R1 intentionally does **not** connect `Response -> Revision` across corpora. ARIES and DISAPERE are different populations, licenses, annotation systems and document identities. Their common interface is virtual and provenance-preserving.

The four shared kinds are `concern`, `response`, `revision`, and `correspondence`. Source-native labels remain attached as `nativeLabels`; they are never silently translated into a universal reviewer ontology.

Every observation carries source asset + immutable snapshot identity + source record key + annotation origin + rights standing + `authority=evidence_only`. Reviewer and annotator identity fields are excluded from the shared adapter surface.

DISAPERE is CC BY-NC 4.0 and is therefore hard-blocked from commercial product/service use under the current admission. ARIES remains separately bound to its ODC-BY source terms. Raw bytes are not merged.
