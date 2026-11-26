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

## Actual native route result and delivery

Initial search job-01a21573-255c-762b-bb12-92401d0ba31b exit0.
Direct 20818 exact/2204 reduced states, frontier 28 actions/9 HP.
Gradual 20691/2286, frontier 29/11 and 30/12. Equal respective
frontiers and actual shared opening (45 HP, stamina2, turn2) at fork,
exact one native branch state event. Both native Scene witnesses won.
Early, unknown, bypass, repeated choice and restore rejection preserve
state; restart resets to undecided. Selected route is not a mutable
shadow field. Source experiment job-01a21573-eb2d-7141-90b3-5c24a95104dd
exit0, nine actual receipt corruption axes rejected, 2.099s final search.
No human preference, physical space generator, save/load, or audio claim.
Minimal native graybox UI; route preview not regular product.

Final product source 2982f1bd59b3a9863998d164c8dda0f58c328422,
job-01a21574-8df0-7663-bdb9-b5a4c7e3094a exit0. Actual exported Linux
both complete paths via isolated XTEST (67 observed action events including
rejections/restarts), 9 window-local RGB observations; common fork equal,
different selected and won images, restarts equal initial; exact terminal
direct ROOM3/3 HP9 turn25, gradual ROOM4/4 HP11 turn25. No human input.
Linux EXE d1222c94ed6aa801b1fa5ddb789a2300bc606776a51d23b2f65fed0af06c20f7
and archive c5c088be44ad5aca65f9b09d2bf46f31c7b62e473a15966542fe1fccebe2af8b.
Windows EXE c5744045563b3591059748d49039b46316a7c726b658f0c0e41f146377bb2ab0
and archive ccd81ec80854e26f2463eb9c08ee9317a59e88ec2f20978db82b1b86714a77e8.
Godot official matched 4.7.2 editor/template identity; shared archive operator
explicit inventory includes engine native license/copyright metadata
a2b685e8787315814cf6ba505d5c6af7945396589754b9facec85744bd090537
from matched editor, not a claim that editor and export libraries are identical.
See https://docs.godotengine.org/en/stable/about/complying_with_licenses.html .
Both native archives and receipt copied and checked in Windows Downloads
Ordivon-Game-R22-Route-Fork-20261126, manifest
9ec6302252bdc7e0b7ba0aa10440203340fc7663f9a1a51be6831e30cfcef862,
receipt 1e3a6c7809a3ec478941e7d37d6dbf2b343682f5b2426ff0433064b1a2df703b.
Windows native manifest readback job-01a21576-ffdf-7f12-ae00-4996f507af11,
exact delivered EXE native startup job-01a21577-6f8f-7dc0-9c7d-e28edd9b7345
Session1 PID19420 HWND3081482 exit0, independent FFmpeg qualification
job-01a21577-a790-7090-888c-09492dc44f7c exit0, 8 nonuniform frames
1152x648, RGB d31588e2ac0d289028fde8e150b92de6c46a6430f27a6982d048a1d6da897bc6,
NVIDIA RTX5060 Laptop. Original immutable receipt is Windows export-only;
this separate startup witness does not imply Windows full route input.
Reproduce: mise run experiment:route-fork;
GAME_ROUTE_OUTPUT=/absolute/fresh/path mise run factory:content:route-fork.
No required CI lane or public release; no regular Rule/scene/config edit.
