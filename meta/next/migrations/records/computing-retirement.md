# Computing retirement

- Source: `/root/projects/ordivon-computing`
- Final archive commit: `8329fb91ffd808155a3cfecccf28a263ca971f4c`
- Closed: 2026-09-14
- New-model disposition: **ARCHIVED HISTORICAL CORPUS / NO CURRENT COMPUTING OWNER**

## Decision

The broad `ordivon-computing` owner is retired. Ordivon no longer maintains a permanent shared Computing/world-model authority, project-family navigation authority, cross-project protocol-development root, or generic Observation plane merely because those abstractions once existed.

Current cross-domain classification and migration/disposition belong in Ordivon Next. Concrete repositories and mature external systems keep their own state, semantics, execution, observability, and domain authority. New research routes through the current Research capability and the relevant mature domain methods/tools.

## Residuals handled before archive

The repository was not archived until its real current consumers were resolved:

1. Harness was the actual current code consumer of `ordivon-protocol`, but active Harness source used only the legacy `anc_canonical` identity primitive. A direct RFC 8785 replacement was experimentally rejected as byte-incompatible for some Unicode key orderings and integers beyond the IEEE-754 safe domain. Harness therefore localized the exact compatibility implementation as an owner-local shim and removed the cross-repository Protocol dependency. Harness main after cutover: `359ab392ae9bc8aa6a404ed77d14c3679365948a`.
2. Runtime's optional `scripts/observation_export.py` was the only remaining current code consumer of `ordivon-observation-core`. It had no service, CLI, deployment, or product API consumer, so the experimental cross-owner exporter was deleted instead of migrating a custom Observation layer. Runtime main after deletion: `4907d72c7b2d5b43dc5869bc67529136fe9a1cff`; 137 Runtime script tests passed.
3. `ordivon-content` had no external current consumer and remains only inside the archived corpus for historical managed-document reproducibility.

## Current-entry cleanup

Current navigation was also detached before archive:

- Runtime stopped advertising Computing as the current project-family map: `94e6166a4d06ac64517be44ae1884e1cc054d6ee`;
- Game stopped advertising Computing as the current project-family map: `bd2c2ba9a54f7bcd6f48c253759996b105174797`;
- Operations removed `/root/projects/ordivon-computing` from its default mise trusted project paths: `0bb6d36b6721ebaedcf8afcacb53621c3df66c28`;
- Web marks Computing as historical and no longer uses it as the site's current source/authority root: `32a2a1ca14a7bb837551e5ef30f37d551cb28b83`.

## Preserved historical value

Retain the Git history for exact experiments, negative results, contraction evidence, research-method history, immutable `ordivon-protocol` 0.3.0 release bytes/Schemas/vectors, Observation/content-engineering experiments, Game fixtures, Media source maps, Web exact-revision articles, and other revision-bound provenance.

Historical references do not reactivate current ownership. The archived repository's own owner gate passed after closeout, proving internal reproducibility of the preserved corpus rather than current architectural authority.

## Future rule

A shared cross-system mechanism may be admitted again only when concrete repeated failures survive mature external baselines and at least two materially different real consumers require the same residual responsibility. If that happens, place the mechanism with the narrow concrete owner that can prove it; do not reactivate Computing by default.
