# Two real Kenney Abstract Platformer appearance resources

Original author/CC0 authority: https://kenney.nl/assets/abstract-platformer
Binary delivery mirror: https://github.com/shorepine/kenney
Pinned upstream materialization commit 3694c6879e487c108f55677be7dd2ca75b07cc3b.
Source mirror paths:
- 2d/Abstract Platformer/Players/Player Blue/playerBlue_stand.png
- 2d/Abstract Platformer/Players/Player Green/playerGreen_stand.png
Local identity:
- player_blue_stand.png SHA-256 b5c4268e846fea66b8aeb34375cfd22a9399a81cc1c57be1e8e4643c7e211e31
- player_green_stand.png SHA-256 0a185f900898b21532908083f6c64695887f06d4d9baeeebf3173f615102bb55

Both PNG bytes are independently verified as equal to the already-published
Game provider PR #1422 exact SourceCut 42ffaf0d8438d6b58620b94b4b93065579d57a9b.
The mirror is a materialization channel, not proof of official ZIP byte identity.
No unrelated pack LICENSE is copied because it belongs to another pack.
Product-native consumer: scene HUD TextureRect Resources loaded via Godot import;
real gameplay hides/enables enemy portrait as the Rules phase changes. Alternate
HUD swaps the two resources without rewriting combat rules. Native headless tests
prove pixels and replacement, not screen visibility or human art quality.
