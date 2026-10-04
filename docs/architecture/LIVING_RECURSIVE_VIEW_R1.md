# Ordivon Living Recursive LEGO View R1

Status: PROTOTYPE / REBUILDABLE PROJECTION / NO NEW TRUTH OWNER

## Purpose

Ordivon is too large and too fast-moving to be rediscovered from the whole repository on
every review. R1 keeps a rebuildable view of the exact source cut and projects only the
changed and requalification frontier when Git moves.

The retained loop is:

    exact checkout
      -> SourceView
    commit/base delta
      -> DeltaView
      -> conservative source invalidation
      -> verification requalification
    owner-native observations
      -> Qualified multi-view projection
      -> UNKNOWN where required observations are absent

The compiler is tools/repo/living_view.py.

## Reused mechanisms

R1 does not recreate the earlier QOWG publication machinery. It generalizes the proven
invariants and reuses current canonical owners:

- QOWG publication_epoch.py: exact Git/tree identity and projection-only truth role.
- QOWG publication_slices.py: conservative decomposition and no independence claim.
- QOWG publication_coverage.py: exact/missing/diverged distinctions and UNKNOWN-preserving
  semantic-bridge discipline.
- tools/repo/affected_owners.py: changed path to direct repository owner.
- tools/repo/dependency_contracts.toml: explicit cross-owner source seams.
- tools/repo/convergence_plan.py: conservative interaction closure and verifier plan.
- docs/architecture/architecture-constitution-r1.json: semantic kernel, substrate owners,
  and truth-separation laws.
- Recursive LEGO R2.1 operational representation and broken-frontier laws: changed layers
  are re-entered without silently restarting unaffected layers.

The QOWG dirty workspace remains historical/prototype evidence. R1 does not wholesale copy
or promote it.

## Views

SourceView binds the exact Git commit/tree, Architecture Constitution digest, repository
owners, declared dependency seams, conservative owner components, and source MCP surface
manifests. It is source projection only and does not establish deployment or live state.

DeltaView reuses the existing convergence projection and separates owner-local changed
paths, repository-mechanics cross-cutting paths, unclassified paths, source invalidation,
and verifier requalification. Source invalidation and verification requalification are
deliberately distinct. The latter may be wider. Minimal semantic invalidation is not
claimed.

Live/provider evidence enters only through ordivon.living-owner-observation records.
An observation names its owner, subject, time, operation, standing, evidence references,
and opaque owner-native attributes. The compiler does not reinterpret those attributes.
Callers may require selected owners; missing observations remain UNKNOWN.

QualifiedView composes SourceView, optional DeltaView, and supplied owner observations
side-by-side. One facet never overwrites another.

InformationCoverage is a compact, rebuildable source/reference projection produced by
tools/repo/information_census.py. It deliberately does **not** create a universal
information object model. The current repository already contains hundreds of owner-native
top-level kind identities, so R1 keeps those identities opaque and projects only
mechanically observable facts:

- carrier family as a navigation facet, never semantic authority;
- repository-mechanics owner classification from affected_owners.py;
- top-level structured identity signals without promoting nested payload fields;
- unique, ambiguous, or unresolved references to tracked source files/directories;
- namespace-shaped references as OWNER_BINDING_UNKNOWN until an owner-native readback proves a binding;
- candidate Git revisions as current-repository exact or unresolved, without inferring
  historical invalidity.

Path resolution is conservative. Explicit ./ and ../ paths use ordinary
carrier-relative semantics. Bare owner-local paths may be searched against carrier
ancestors, but only one tracked match is EXACT_UNIQUE; multiple matches remain
AMBIGUOUS_EXACT. A missing target remains UNRESOLVED_IN_SOURCE_CUT, optionally with a
historical-context hint. For an unresolved path, a unique or multiple same-basename
tracked file may be emitted only as an alternate-location navigation hint; this does not
prove relocation or identity. None of those unresolved states by itself means dangling,
broken, stale, deleted, relocated, or semantically invalid.

The compact InformationCoverage summary is embedded in SourceView. Full reference detail
is not retained as another registry: it is rebuilt on demand from the exact source cut.
This keeps the view content-addressable while allowing later owner-native reconciliation.

## Currentness and rebuild law

For every exact Git checkout, SourceView is deterministic and content-addressed by a
viewDigest. A new commit therefore produces either the same source view or a new digest.

For a base/head pair:

    changed paths
      -> direct owners
      -> conservative source invalidation
      -> declared-seam verifier closure

Non-owner paths are emitted explicitly and are never silently assigned to an owner.

Information/reference currentness follows the same rule: source-level exactness,
ambiguity and absence are recorded separately from owner-native currentness. A namespace
prefix is only syntax: it does not identify a natural owner. Namespace-shaped references
and unresolved paths must be reconciled with an independently selected natural owner
before a semantic stale/dangling verdict is allowed.

Live currentness is not guessed from source. Owner-native probes run outside this pure
compiler and feed exact observation records back into it.

## CI

The required monorepo workflow builds the view for the exact checked-out revision on pull
request, merge-group, push, schedule and manual runs. The compact digest/frontier summary
is written to the GitHub job summary and the complete JSON projection is retained as a
workflow artifact. This does not create a second source authority; any source-only view can
be rebuilt from the exact Git revision.

## Non-goals

R1 is not an architecture database, capability/provider status registry, workflow engine,
scheduler, verifier registry, deployment controller, security/IAM authority, or domain
completion authority.

To reproduce an older SourceView, check out that exact commit and run the compiler version
at that commit. The compiler refuses to combine an arbitrary non-checked-out revision with
current repository contracts.
