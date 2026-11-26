# R22 — native fork and route trade-off
Host #33334/#33349. Mission/Space (Dormans; TU Delft mixed-initiative
mission/space generation https://publications.graphics.tudelft.nl/papers/261);
native Resource data https://docs.godotengine.org/en/stable/classes/class_resource.html.
Scope: one explicit mission fork, not a spatial map or general dungeon engine.
Thought: meaningful choice, separation of topology and combat, consumer-first,
finite native reachability, evidence before production tuning.
Logic: route catalogue -> two ordered room sequences; common-prefix combat ->
existing EncounterRules; fork admission -> product-scoped Rule subclass;
projection -> native scene and buttons; evaluation -> R19 shared native search;
consumer -> actual scene and isolated exported input. No duplicated combat.
I: original Trial tuning, direct [1,3,4] and gradual [1,2,2,3], total 8 foes.
O: both native winning witnesses, route choice after clearing first room,
mechanical action/health trade-off and playable private preview.
S: native Rule-owned active tuning; selected route derived from room and
active sequence (no second mutable route state). pre: cleared room1 and valid
route ID; post: atomic admitted suffix and native advance; inv: no early,
unknown or duplicate route, no direct advance at fork, no health/stamina/turn
change when choosing; restart resets to undecided; no save/restore capability
exposed in this prototype, reject inherited restore. eff: isolated native scene
and exports; c: 48 actions/cap100000 per search; epsilon: finite deterministic
mechanical scope, not a general graph proof or Human preference.
prov: exact source/route resource identities, native observations, manifest.
Unfold: existing Rules, RefCounted search, Godot Scene/Resource, existing
native process/export/XTEST tools. Preserve regular product and R20/R21.
