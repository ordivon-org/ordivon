# R21 exact selected processing plan identity
Host #33393. Actual RED: native TTML receipt qualified with empty closure,
missing Host Dependencies, arbitrary adapter digest or arbitrary closure digest.
Thought: in-toto exact material/product rules, SLSA consumer expectations,
representation-first, shared canonical encoding, explicit authority boundary.
Logic: closed manifest -> canonical SHA256 -> selected profile/adapter identity
-> unique exact Host commitment projection -> existing retained receipt checks.
Capability: existing owner-local adapter/source dependency declarations,
processing_plan_identity pure operators, existing plan compiler and qualifier.
I selected plan, local Media root; O internal consistency or reject;
S none; pre caller-selected source closure and input; post exact inventory,
canonical encoding, adapter/profile and input/commitment agreement;
inv missing/extra/duplicate/conflicting representations cannot qualify;
eff no source-byte read during validation of the closure, no runtime effects;
c O(n log n) projection; epsilon not an execution witness, signature,
historical-version compatibility or complete installed-environment proof;
prov actual TTML RED, twelve mutated real plan controls including coherent
missing/extra helper rehash, four native adapter positives and AV negative;
unfold inventory->encode->project->consume.
No new third-party dependency or registry. Existing source dependency set
remains sole declaration; plan must match current declared contract.
References https://github.com/in-toto/specification/blob/master/in-toto-spec.md
https://slsa.dev/spec/v1.2/build-provenance
