# Evidence

This directory contains point-in-time observations, experiment outputs, acceptance receipts, and other historical evidence. Evidence records what was observed or accepted under a particular subject/revision/environment; it does not become current runtime configuration or live semantic authority.

Lifecycle rules:

- preserve historical evidence; supersede or append rather than rewrite an old observation to match the present;
- bind consequential evidence to the exact subject, revision, artifact, provider, or experiment condition it supports;
- treat acceptance receipts as point-in-time claims with explicit boundaries, not as perpetual deployment health;
- keep experiment and campaign outputs in their domain-native shapes when no mature interchange format naturally owns them;
- prefer mature native formats when they do exist, such as SARIF for static-analysis results and SLSA/in-toto attestations for applicable build provenance, rather than wrapping the same result in a second Ordivon evidence format;
- generated projections and caches must be reproducible from their source records and must not become a second source of truth.

Current source, schema, provider state, and executable validation must establish current behavior. Historical files under `evidence/` may be used as explicit test fixtures or research inputs, but production runtime behavior must not depend on an old acceptance receipt merely because it once recorded a passing standing.
