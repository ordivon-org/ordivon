# Kenney CC0 — native Godot visual-composition LEGO

This executable Godot 4.7 sample consumes **two real PNGs** from Kenney's
*Abstract Platformer* pack using Godot's own Texture2D, Sprite2D and
PackedScene primitives. It does not introduce a rendering engine, universal
asset registry, game product, or additional runtime.

## Direct consumer

Run within this directory (Godot CLI installed via root mise configuration):

    godot --headless --path . --editor --import
    godot --headless --path . --script res://acceptance.gd
    godot --headless --path . --quit-after 2

The main scene renders the blue sprite; alternate_avatar.tscn supplies the
green appearance with the same Avatar scene-node contract. The acceptance
script loads both through the native importer, checks real image pixels and
dimensions, then substitutes the alternate Sprite2D in the live scene tree
without changing its position or creating another root. Headless execution
confirms loading/substitution, not visual quality or human usability.

## Exact source / licensing

- Original author and licensing authority: Kenney, https://kenney.nl/assets/abstract-platformer — CC0.
- Original licensing FAQ: https://kenney.nl/support .
- Binary delivery mirror (not upstream authority): https://github.com/shorepine/kenney ,
  exact commit 3694c6879e487c108f55677be7dd2ca75b07cc3b.
- Source mirror paths: 2d/Abstract Platformer/Players/Player Blue/playerBlue_stand.png
  and 2d/Abstract Platformer/Players/Player Green/playerGreen_stand.png.
- player_blue_stand.png SHA-256 b5c4268e846fea66b8aeb34375cfd22a9399a81cc1c57be1e8e4643c7e211e31
- player_green_stand.png SHA-256 0a185f900898b21532908083f6c64695887f06d4d9baeeebf3173f615102bb55

The mirror is a materialization source, **not evidence of byte identity with a
separately downloaded official zip**. File-level source identity, CC0 upstream
license claims and native runtime use are separate propositions. The mirror root
license names a different kit, so it is intentionally NOT copied here; the
licensing authority for these assets is the linked Kenney pack page.

## Composition contract (bounded)

Inputs are a Godot PackedScene whose Avatar child is a Sprite2D, and an
importable PNG-compatible Texture2D. The exact tested precondition is that
both textures decode to non-empty images and differ in pixel data. Natural
image dimensions may differ; this is not an interface error. Replacement
changes only presentation resources; the scene tree retains one Avatar at
the same position. Source material and license digest are pinned above.

A concrete game's rules, transitions, camera/UI and player experience belong
to that game; they are not implied by this appearance-only sample. To reuse,
copy the native scene and replace its source PNG with another properly licensed
texture, then run the native consumer acceptance again.
