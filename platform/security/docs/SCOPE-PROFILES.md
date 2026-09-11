# Security v2 scope profiles

Security v2 separates *what is being admitted as a product* from research/reproduction material. The separation is implemented with provider-native path selection and exclusion mechanisms; Ordivon does not define a generic suppression DSL.

## product

The product profile evaluates the repository's current implementation, tests, scripts, workflows, and dependency manifests while excluding these non-product surfaces from product admission:

- `research/`
- `evidence/`
- `docs/`
- `fixtures/`
- `scenarios/`

Those paths are not declared safe. They are simply outside the product admission claim and may be scanned under a separate research/reproduction review when relevant.

Provider-native mechanisms:

- Gitleaks config path allowlists;
- Semgrep `--exclude`;
- Trivy `--skip-dirs`;
- Syft `--exclude`;
- OSV-Scanner `--experimental-exclude`.

A path exclusion is therefore part of the named profile, not a global Security truth or a reusable Ordivon exception.
