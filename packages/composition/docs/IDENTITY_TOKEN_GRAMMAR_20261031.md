# COMPOSITION-TOKEN-20261031: exact token admission

Source baseline: c1b42a27ed63149a388ae18abbcd4a767ba6ce6c.
Registration: existing Composition planning nodes C01, C02, C03 and C05 in
`planning/lego-plan-r1.json`. This issue note is evidence, not another registry.

## Representation and obligation

An identifier is a member of the language
`[A-Za-z0-9][A-Za-z0-9._:/-]*`; a digest is the literal prefix
`sha256:` followed by exactly 64 lowercase hexadecimal characters.
Gate evidence is one nonempty non-whitespace token; interface evidence has the
fixed `interface-compatibility:sha256:` prefix and exactly 64 hexadecimal characters.
Membership consumes the entire JSON string. For a valid token t and any nonempty
line-break suffix b in {LF, CR, CRLF, U+2028, U+2029}, t+b is inadmissible.

The previous start/end-anchored patterns used dollar as if it meant absolute end.
Python's native regular-expression semantics also allow dollar before a final LF.
The production Draft202012Validator therefore admitted 21 malformed cases across
ten schemas. Valid token identity and the wire commitment were no longer the
same representation.

## Repair and actual consumers

Use the ECMA-262-compatible negative lookahead `(?![\\s\\S])` for absolute end.
Do not normalize, strip, or silently repair caller identities. Do not add a
second validator or Python-specific regex escape to the portable JSON schemas.

The schema-consuming path is the existing Composition validator in
`cognitive_circuit_r1.py`, reused by interface, verification-obligation and
successor contracts. Existing source consumers include the Research artifact
gate and timeout-obligation scripts in `meta/next`; their imports establish
source consumption, not installed or domain acceptance.

## Native witnesses and scope

- RED: job-01a19079-a976-7bd3-9bb2-f886af2749b2; native validator reproduced
  all 21 trailing-LF admissions before the schema repair.
- GREEN: job-01a1907b-db61-70d0-bdb5-35ccab853a57; all 126 token cases and
  the Composition owner's complete `mise run verify` passed.
- Existing TLA+ owner-boundary and effect-replay models and their negative
  controls passed in that owner verification. They prove only their declared
  bounded model properties; they are not a proof of regex engines or deployment.
- The regression suite exercises the actual upstream Draft202012Validator.
  Its finite witnesses do not constitute a universal Unicode-language proof.

Authority references:
[Python regex dollar semantics](https://docs.python.org/3/library/re.html)
and [JSON Schema regular-expression portability](https://json-schema.org/understanding-json-schema/reference/regular_expressions).
