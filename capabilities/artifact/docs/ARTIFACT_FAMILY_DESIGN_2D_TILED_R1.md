# Artifact E2E — Design 2D / Tiled Object Map R1

## Standing

`SHADOW_PROFILE_LOCAL_LIVE_PROVEN`

R1 covers one bounded authoring-source case: a finite orthogonal Tiled JSON map (`.tmj`) composed only of object layers whose objects are rectangles or polylines, with no tilesets or external resources. Tiled 1.12.2 is the native format authority; Artifact does not introduce a parallel map AST.

Current Tiled JSON semantics use the object `type` field. Tiled 1.9 temporarily serialized this concept as `class`, while 1.10 changed the JSON field back to `type`. The current Station Zero source was migrated through Tiled 1.12.2 and the Game loader's legacy `class` fallback was removed before this profile was admitted.

## Verification chain

R1 binds exact subject bytes and an exact technical object contract, then requires:

- bounded JSON facts: finite `map`, orthogonal orientation, objectgroup-only layers, unique layer/object IDs, non-empty current `type` values, and no external resources;
- exact canonical sorted-JSON digest identity;
- native Tiled TMJ load/export with semantic equality;
- native Tiled `TMJ → TMX → TMJ` cross-format round-trip with semantic equality;
- `tmxrasterizer` non-empty RGBA readback at `map width × tile width` by `map height × tile height`.

## Current Game pressure test

At Game revision `14dfc8cf479468025ba786f5451df36ce91bfd58`, `station-zero-layout.tmj` has 2 object layers and 40 objects (20 rectangles and 20 polylines). Its canonical JSON SHA-256 is `d696373f58d2b1df95e49c3a35b5efd7c4508eef1d77d6edceeafc6aa04ba2bc`. Tiled-native TMJ and TMJ→TMX→TMJ round-trips are semantically exact, and `tmxrasterizer` produces a non-empty 1216×768 RGBA image.

The Game-owned spatial projection digest remained exactly `21efdf5b69858953aaef55abd0bb143f5eb24f5be8f3a3c3bcfe6cb86cc5b527` across the legacy-field migration, and the complete Game suite remained 432/432 PASS.

## Boundary

Artifact verifies the authoring artifact and native-tool behavior. Game remains authoritative for the meaning of Zones, Passages, custom properties, topology, pathfinding, collision, visibility, gameplay and artistic decisions. R1 does not claim support for tile layers, tilesets, image/group layers, infinite maps, templates or external resources.
