---
schema_version: 1
id: game.ownership-boundary
title: Game LEGO Boundary
profile: engineering
lifecycle: active
source_role: canonical
visibility: public
owners: [ordivon-game]
---
# Game LEGO boundary

Game owns source-bound reusable design knowledge, not a game product or a
universal Mod framework. A future concrete product owns its specific rules
and state; external engines own rendering, scene/resource and plugin
mechanics. Reuse these native LEGO before writing new code.

Player data modifications can be validated against their relevant inputs.
An alternative compatible ruleset must satisfy its promised consumer
contract. A wholly new game may define new rules and invariants, without
preserving obsolete product restrictions. Formal checks prove only their
encoded properties, not arbitrary executable Mod safety or human enjoyment.

Old games and experiments are retired from the live repository; Git
history is the rollback path. No old product automatically becomes shared
infrastructure or a mandatory model for successors.
