# Media v2 — Game Station Zero sprite consumer R6

## Purpose

Use a real non-Media consumer to force only the missing capability boundary. This episode does not create a generic Media service or cross-domain asset schema.

Consumer: `/root/projects/ordivon-game` at `413882d197c672c22898d8c7d3c0316f9eaf6997`.

Media opening revision: `dc447ccd99cbef8d33af3d36b11937b4bf2b57ff`.

## Ownership boundary

Game owns the semantic brief, Actor identities (`engineer-imani`, `medic-reyes`, `security-chen`), role mapping, hidden-information constraints, runtime integration, and gameplay acceptance.

Media owns selection of the sprite production equipment, editable-master production/export semantics, exact output evidence, and medium-level technical QC.

Workstation owns the physical Aseprite binding. Runtime owns physical execution.

## Exact equipment evidence

Workstation equipment id: `game-aseprite-e1`.

Binding digest observed during R6 preflight:

`sha256:46b347973d9eb5f4d89db82235262912c836dee56fb5ec1b78cc23f08b72e42b`

Executable digest:

`sha256:f7a08c602b4d62616769e88b1896082ae50d8033ebcb75cca3fa7b284a57aac7`

Executable path is a Workstation projection, not Media semantic authority.

## Real-production reproducibility preflight

The exact Game Lua recipe was executed in Aseprite batch mode into an isolated Media workspace, then the generated editable master was exported to PNG.

Fresh editable master:

`sha256:ca9962d66c64c0036bb615d89492cf5063da878d414daf32cff5c6b1615b473c`

Committed Game editable master:

`sha256:ca9962d66c64c0036bb615d89492cf5063da878d414daf32cff5c6b1615b473c`

Fresh runtime PNG:

`sha256:f7e2f2c6f41055e618cc1e572a060bee112a9a848fa50910121341f9682842d9`

Committed Game runtime PNG:

`sha256:f7e2f2c6f41055e618cc1e572a060bee112a9a848fa50910121341f9682842d9`

Both fresh outputs were byte-identical to the committed consumer artifacts. The PNG was independently observed as 72x24 RGBA. This is bounded reproducibility evidence for this recipe/tool binding, not a universal Aseprite reproducibility claim.

## Capability closure

R6 admits two narrow Media equipment capabilities because a real consumer now requires them:

- `sprite.source.author`
- `sprite.runtime.export`

Both resolve through the existing Workstation digest-fenced `game-aseprite-e1` binding. Media does not copy Game Actor semantics into its equipment model.

## Formal consumer acceptance

The new capability was exercised through `studio_equipment_propose`. Both `sprite.source.author` and `sprite.runtime.export` resolved to `aseprite` with `DIRECTLY_INVOCABLE`, `READY`, no blockers, and the exact Workstation binding above.

Runtime then executed the compiled two-step plan under Job `job-01a09a17-9cc1-7b20-ad73-9932f9df010a`. Both steps succeeded. The resulting source and PNG retained the exact digests listed above and remained byte-identical to the Game consumer artifacts.

An independent Game workspace at the exact consumer revision first proved that the Media-produced outputs were byte-identical to its accepted inputs, then ran `test/station-zero-v3-vertical-slice.test.ts`: 6 tests passed, including exact three-Actor mapping, runtime derivative presence, audio boundary, accessibility, and deliberation presentation.

## Destructive negatives

The isolated Game consumer workspace then deliberately changed the Engineer frame x-coordinate from `0` to `24`. The semantic test rejected the altered atlas (`actual [24,24,48]`, expected `[0,24,48]`).

A one-byte drift was appended to a copy of the runtime PNG. Exact consumer identity comparison rejected it. The consumer workspace was restored to a clean state after the negative.

These negatives prove fail-closed behavior for this bounded consumer episode. They do not claim general visual-semantic validation by Media.

## Digest-bound source replay

The consumer recipe is bound to Game revision `413882d197c672c22898d8c7d3c0316f9eaf6997` in an isolated Runtime workspace. Its exact Lua recipe digest is:

`sha256:8032fa7fe6b7cd0f8864ffd50c70a459d121e8a3821c785239980728ff591347`

Runtime replay Job `job-01a09a1e-789d-7a51-8f1c-fe96cec27bea` declared that recipe as a SHA-256 host dependency and executed the two Aseprite steps again. The resulting editable master and runtime PNG were again byte-identical to the accepted consumer artifacts.

During closure, the canonical Game repository independently advanced to a later revision and no longer retained the same Station Zero asset directory. The isolated exact-revision consumer workspace remained valid. This is positive evidence for revision/digest binding and negative evidence against ambient canonical-path currentness as an input contract.

## Standing

`GAME_STATION_ZERO_MEDIA_CONSUMER_R6 = PASS`

This closes the first real external-consumer graduation episode (G3). It does not by itself close Media v2 G2 globally, review G4, destination verification G5, or legacy retirement G6.
