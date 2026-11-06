# Knowledge

This directory stores curated metadata and mappings to human knowledge. It is not intended to mirror the world's documents.

Expected records include:

- problem taxonomies;
- standards and versions;
- domain bodies of knowledge;
- methods and applicability conditions;
- algorithms and solver families;
- tools/capabilities;
- benchmarks and validators;
- provenance and source authority metadata.

Open upstream sources may be pinned or mirrored where redistribution permits. Restricted standards should be represented by metadata, version, official source references and permitted derived mappings rather than copied content.


## External world observations

[Claim–Evidence–Delta R1](docs/EXTERNAL_WORLD_DELTA_R1.md) defines a bounded,
read-only source comparison with an explicitly unaccepted domain decision. The
[November 2026 BoE example](observations/boe-rate-20261105.json) preserves both
primary-source dates and units, and the stdlib consumer can reproduce its
arithmetic without creating a news database or changing Capital state.

## Lifecycle

`knowledge/` is not a construction diary. A source-code implementation wave, acceptance closeout, or architecture delta does not automatically earn a permanent lesson.

Retain a lesson when it carries reusable knowledge beyond the current implementation or remains an explicit provenance dependency of maintained evidence. When current source/tests have absorbed the behavior and no current consumer depends on the explanatory construction record, remove that lesson from the working tree and rely on Git history.

Historical graph/delta files may remain when point-in-time evidence explicitly references them. Such files are provenance companions, not current runtime configuration or deployment prerequisites.
