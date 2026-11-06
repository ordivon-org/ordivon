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


## External-world learning: Human entry

Use the [external-world evidence review Skill](../../.agents/skills/external-world-evidence-review/SKILL.md)
when an externally confirmed event or counterexample might change a **named**
current domain hypothesis or decision. Choose the real previous baseline,
issuer/original source, affected model or consumer, and the next observation
that would disprove the proposed change. The relevant natural Owner, not this
catalog, decides whether to revise that model. For routine daily news reading,
the existing daily-world-brief procedure remains the correct entry.

## External-world learning: Agent entry

Discover and read the exact installed `external-world-evidence-review` Skill
when activated. Reuse the domain's native research and verification tools
and W3C PROV / CloudEvents / OpenLineage only where their semantics are needed.
Preserve source dates, uncertain status, direct support scope, independent
counterevidence and actual consumer read-back. Do not construct an extra
persistent event registry, automatic promotion daemon or custom arithmetic
validator. A no-consumer observation may remain a human-readable report.

The earlier `external_world_delta.py`, dated BoE sample and self-referential
tests are retired because the only live references were their own demo, README
and root CI invocation; ordinary source/date/decimal comparison is handled
by mature, task-selected methods. Git retains the past source if needed.

## Lifecycle

`knowledge/` is not a construction diary. A source-code implementation wave, acceptance closeout, or architecture delta does not automatically earn a permanent lesson.

Retain a lesson when it carries reusable knowledge beyond the current implementation or remains an explicit provenance dependency of maintained evidence. When current source/tests have absorbed the behavior and no current consumer depends on the explanatory construction record, remove that lesson from the working tree and rely on Git history.

Historical graph/delta files may remain when point-in-time evidence explicitly references them. Such files are provenance companions, not current runtime configuration or deployment prerequisites.
