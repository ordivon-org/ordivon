# Game standalone source-carrier retirement acceptance — 2026-09-21

Standing: **RETIRED_ARCHIVED**

Scope: retire the legacy standalone Game source carrier at /root/projects/ordivon-game after exact source relocation to /root/projects/ordivon/domains/game, current-consumer cutover, preservation of non-Git state, recovery proof for two dirty orphan worktrees, and live Workstation configuration cutover.

This retirement does not remove the Game capability, rewrite historical Game evidence, publish a game, perform a store upload, mutate an external provider, or claim Human/player-value evidence.

## Canonical source identity

Immediately before physical retirement:

- legacy path: /root/projects/ordivon-game
- legacy main: a4fdaa065f8daee963154c4647a920c6bc9e75a5
- legacy tree: 183db41b8ccfc23a6b43fbefef5c54e3fd0575a8
- canonical path: /root/projects/ordivon/domains/game
- canonical tree: 183db41b8ccfc23a6b43fbefef5c54e3fd0575a8
- tree identity: exact
- transaction-observed monorepo main: d665d00a89063f343306b425e2531d694ebad203

The standalone root was clean. The monorepo owner had the exact source tree before removal.

## Current-consumer cutover

Two executable/test consumers still used the standalone path:

- platform/workstation/tests/test_workstation_consequences.py
- capabilities/artifact/tests/test_artifact_verify.py

They were changed to derive Game from the canonical monorepo owner.

Targeted verification before integration:

- Workstation Game/Media package-manager consequence test: PASS
- Artifact frozen Ogg Game consumer readback: PASS
- Artifact frozen Godot Linux ELF producer readback: PASS
- canonical producer-evidence hashes: exact

Artifact full-suite failures in Blender headless and GDAL GeoPackage conformance were reproduced on the unmodified base with the same failing tests, so they are existing environment/tool gates rather than regressions from Game path relocation.

The consumer cutover commit is 89299365589005478f16dd0bbb63ad1d7aee775c and was integrated without overlapping parallel changes.

## Current metadata and Workstation live configuration

A deeper reference census found current owner metadata that was not executable Python but still represented live/current topology:

- Workstation Home Manager mise trusted-config paths
- six external-authority registrationBasis records
- Game capability package current-source description

Historical records with exact legacy revisions were deliberately preserved.

The current-source migration commit is d665d00a89063f343306b425e2531d694ebad203.

Authority Catalog was deterministically rebuilt after the six authority-record changes:

- record count: 168
- observation count: 173
- standing: PASS_LIGHTWEIGHT_PROGRESSIVE_DISCOVERY
- structured non-deferred dogfood IDs resolved: 27
- generated records digest: sha256:24b433258a8021f66699f6ca3ad77f53b966ee71b719e3ef2d4227d0596dbc50
- authority tests: 7 PASS

Workstation Home Manager source now trusts only:

- /root/projects/ordivon/domains/game
- /root/projects/ordivon/capabilities/media

Nix flake check passed. The committed source built the same validated Home Manager generation as the candidate:

/nix/store/141ga95qgjjzn63jzqn89y5bcwmha912-home-manager-generation

Before activation, the old/new Home Manager home-files diff contained exactly one changed managed file:

.config/mise/config.toml

The previous live mise config and previous Home Manager generation were preserved under the Game retirement backup directory.

The new generation was activated through its native Home Manager activation script. Live mise configuration then contained exactly the two canonical monorepo paths above and no old Game, Media, Web, or Computing standalone path. The live Workstation consequence regression passed.

## Dirty orphan worktree preservation

Runtime projected zero open Game workspaces, but Git still retained two physical dirty worktrees:

- ws-game-causal-lag-loop-r1-20260918
- ws-game-pc01-e03-human-canary-r1-20260918

They were not treated as garbage.

For each worktree the retirement backup preserves:

- base HEAD
- porcelain status
- binary tracked patch
- untracked path manifest
- untracked tar archive
- ignored path inventory
- metadata

The causal-lag worktree had 13 dirty/untracked files whose bytes matter. Its 930 ignored entries were entirely node_modules cache/dependency material. The human-canary worktree had one untracked test and zero ignored entries.

A real recovery proof cloned the Game bundle, checked out each base revision, replayed the tracked patch, extracted the untracked tar, required exact restored Git status, and compared represented file bytes.

Recovery result:

- causal-lag compared files: 13, all exact
- human-canary compared files: 1, exact
- restore standing: PASS
- restore proof SHA-256: b2a9f552d42d38a69928ea696b70a836b4fcb169c4208148195088123b417160

Only after this proof, and after confirming zero process references, were the two orphan worktrees removed. The standalone Game repository then had exactly one worktree: its own clean root.

## Complete Git preservation

A complete all-refs bundle is preserved at:

/root/ordivon-migration-backups/2026-09-21-game-retirement/game-all-refs.bundle

SHA-256:

848c0f6552e6d5aaf07ecc43a721e9368bda2b875302477abd04c9d38a89d582

A full ordinary refs manifest records 413 Git refs:

/root/ordivon-migration-backups/2026-09-21-game-retirement/game-all-git-refs.tsv

SHA-256:

e8b34929da3a6fecb85ffa7f265226053e31504b288c1511d0670c2dae76506f

Before deletion, all 413 refs were present in the bundle with missing=0 and mismatch=0.

After physical deletion, the bundle was cloned into a temporary mirror repository and all 413 refs were checked again:

- missing: 0
- mismatch: 0

The temporary recovery clone was then removed.

## Non-Git Game state preservation

The standalone repository contained unique ignored Game state that was not safe to classify as cache:

- two Station Zero G4 calibration JSON records
- station-zero.sqlite3
- SQLite shm/wal companions

These bytes were preserved in:

/root/ordivon-migration-backups/2026-09-21-game-retirement/game-main-local-payload.tar.gz

Archive SHA-256:

9dc3da38be5e5916742b82758b78f07c8c58269a1812442d4dc561c50a7dd891

Payload manifest SHA-256:

e8a3337e711d71e50a0a4a8864a3ce5849d5368ef86276579dff13b3894e37f3

The Station Zero database SHA-256 is:

963fc71b2d259ea54c7978eab0ac51c79ceac06eaddb336584403ac8e7c6a78b

Before and after source-carrier deletion, the payload archive was extracted into a temporary recovery directory and every file was verified against the manifest. SQLite pragma quick_check returned ok and the expected runs/events/host-journal/team-round/team-proposal tables remained readable.

Generated build outputs, Godot cache, node_modules, Ruff cache and similar rebuildable ignored state were not elevated into source authority.

## Final retirement gate

Immediately before physical removal:

- Runtime workspaces rooted at /root/projects/ordivon-game: 0
- external linked Git worktrees: 0
- process cwd/exe/fd references: 0
- systemd references: 0
- /etc and /root/.config references: 0
- live executable/test/config references: 0
- current external-authority old-root references: 0
- current Game capability metadata old-root references: 0
- current Workstation Nix old-root references: 0
- standalone tracked status: clean
- canonical Game source tree: exact
- canonical Game pnpm check: 584/584 tests PASS plus typecheck and web syntax check

The durable pre-delete retirement receipt is:

/root/ordivon-migration-backups/2026-09-21-game-retirement/game-physical-retirement.json

SHA-256:

6fb2ceab63102691fff78e20644f7ad01098ec60ad76abb5f9df2b614340e960

## Post-delete functional proof

With /root/projects/ordivon-game physically absent:

- canonical Game pnpm check: 584/584 PASS
- typecheck: PASS
- web syntax check: PASS
- Workstation live owner-path consequence test: PASS
- Artifact frozen Ogg Game consumer readback: PASS
- Artifact frozen Godot Linux ELF producer readback: PASS
- current authority/capability/Workstation old-root references: 0
- live /etc and /root/.config old-root references: 0
- Git restore proof: 413 refs, missing=0, mismatch=0
- local payload restore: all hashes PASS
- Station Zero SQLite quick_check: ok

## Historical path references

A final tracked census still contains historical literal /root/projects/ordivon-game references in 38 files. They are retained intentionally where the path is part of the evidence identity, exact historical revision, migration receipt, Creative Library/Preservation source record, artifact consumer acceptance, or dated research/knowledge snapshot.

Physical retirement does not rewrite provenance.

## Disposition

- active Game source owner: /root/projects/ordivon/domains/game
- legacy standalone Game path: physically absent
- standalone Git history: archived and restore-proven
- unique non-Git local Game state: archived and restore-proven
- two dirty orphan worktrees: recovery-proven, then drained
- compatibility alias at the old path: NONE
- production/store/provider mutation from this retirement: NONE

If legacy Game state must be recovered, materialize it into a bounded recovery path from the recorded bundle and payload archives. Do not recreate /root/projects/ordivon-game as a compatibility alias.
