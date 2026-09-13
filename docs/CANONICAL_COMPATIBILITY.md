# Canonical JSON compatibility boundary

Date localized: 2026-09-14

Harness carries `src/anc_canonical/` as an owner-local compatibility shim. Its bytes were copied from the exact former `ordivon-protocol` dependency at Computing revision `420dc356cb664d75db0f34f356156baebe5843db`.

This shim is **not RFC 8785 / JCS**. It intentionally preserves already-issued Harness identities: JSON numbers are restricted to integers, arbitrarily large Python integers remain representable, object keys use Python Unicode code-point ordering, duplicate object keys and unpaired surrogates are rejected, and digests are `sha256:` over the resulting UTF-8 canonical bytes.

A direct RFC 8785 substitution was tested before localization and is not byte-compatible: supplementary-plane/BMP key ordering can differ and RFC 8785 rejects integers outside the IEEE-754 safe domain. Therefore changing this algorithm is a versioned identity migration, not dependency cleanup.

The shim owns no cross-project protocol semantics. It exists only to preserve Harness-local durable identity compatibility while the former broad Computing/Protocol owner is retired. New cross-system contracts should use mature standard canonicalization where compatibility permits rather than extending this shim.
