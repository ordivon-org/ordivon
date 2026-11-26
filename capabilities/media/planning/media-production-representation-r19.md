# R19 Production representation convergence
Host #33226, extends #33213 and R17 #33053.
RED real Production Context, operation lineage and review loader accepted
duplicate identity keys. Review separately hashed the descriptor after
interpretation. Reuse strict_json.decode_object in read_bound_object.
| Thought | Logic | Capability |
|---|---|---|
| Representation-first | one strict raw object | existing standard library hooks |
| Evidence-first | exact interpreted bytes | read_bound_bytes/read_bound_object |
| Native composition | selected lineage and review | existing domain consumers |
| Independent falsification | duplicate, nested/escaped, nonfinite/overflow, extra document | actual consumer matrix |
I selected raw JSON; O admitted object and exact SHA256; S none;
pre unique UTF8 finite object; post digest identifies bytes interpreted;
inv no duplicate identity, no descriptor replacement relabeling review;
eff read-only admission, existing review output unchanged; c one read,
one parse and SHA; epsilon not atomic filesystem or media input proof;
prov actual context/lineage/review RED/GREEN, 18 negative representations,
controlled review source replacement; unfold read -> admit -> project.
Existing Model/Asset/Receipt readers migrated to read_bound_object by
R16/R17 inherit strict admission when composed. Remaining independent
model loader for schema documents is not in this slice. Do not replace
arbitrary external provider parsers globally. Review media input lifetime,
other selected decisionContext references and native receipts remain
separate obligations. No third-party dependencies.
Refs https://www.rfc-editor.org/rfc/rfc8259
https://docs.python.org/3/library/json.html
