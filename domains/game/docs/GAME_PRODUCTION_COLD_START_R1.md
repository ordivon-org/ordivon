# Game Production Cold Start R1

This is a bounded production-path acceptance slice, not a product, framework, or release workflow.

It exists to answer two mechanical questions:

1. can a new Game-owned Godot project start from repository source, resolve the current Workstation physical engine binding, execute from source, export a real Linux executable with the installed Godot export template, and execute that artifact successfully; and
2. for this exact minimal project, are two cold exports byte-identical when source bytes, Godot editor bytes, Linux x86_64 release-template bytes, target class, locale/timezone, and unsigned embedded-PCK export settings are held fixed?

Run:

```bash
pnpm e2e:production-smoke
```

The harness under `experiments/production-smoke-r1/`:

1. resolves `engine.project.execute` through the current `equipment-binding` contract;
2. requires an exact `workstation.professional-software` Godot binding;
3. binds and hashes the exact `linux_release.x86_64` export template;
4. copies only the repository-owned project source files into a fresh temporary project;
5. executes the source project successfully;
6. deletes `.godot`, performs a cold Linux x86_64 release export, records its SHA-256, deletes `.godot` again, and repeats the export at the same project/output paths;
7. requires both complete executable SHA-256 digests to match;
8. runs the exported executable again and requires `ORDIVON_GAME_COLD_START_OK`;
9. prints a digest-bound receipt for engine, template, source inputs, artifact, and the bounded reproducibility claim.

## Why the scene carries a persisted `unique_id`

Godot 4.6+ scene files can carry per-node `unique_id` values. During this acceptance work, the original minimal scene lacked one. With Godot `4.7.1.stable.arch_linux.a13da4feb`, two otherwise identical cold exports then produced different generated binary scenes and different embedded PCK/executable SHA-256 values. Persisting the node `unique_id` in `main.tscn` removed that observed source of nondeterminism: repeated clean exports became byte-identical.

This is intentionally treated as source identity, not as `.godot` cache state. `.godot/` remains disposable generated state.

## Reproducibility boundary

A PASS establishes **bit reproducibility only inside the declared acceptance boundary**:

- the four repository-owned source files in this minimal Godot project are identical;
- the Godot editor executable is byte-identical;
- the Linux x86_64 release export template is byte-identical;
- each export starts without `.godot` generated state;
- `LC_ALL=C` and `TZ=UTC` are fixed;
- the same Linux/x86_64 target class and unsigned embedded-PCK preset are used.

It does **not** generalize this result to arbitrary Godot projects, importers, plugins, GDExtensions, other Godot versions, other template bytes, other OS/architecture targets, code signing/notarization, or store-generated packages. Those require their own reproducibility acceptance because each can add inputs or nondeterminism.

For release patching, exact historical PCK/build artifacts remain release authority. Do not regenerate an old base pack and assume byte identity: Godot's own export documentation warns that re-exported packs can differ, and delta-encoded patching requires the exact base packs loaded by the shipped game.

The generated `build/` directory is intentionally ignored by Git. The build is a consequence, not source authority. Release systems must retain immutable release artifacts and digests separately when exact historical bytes matter.

A production PASS still does **not** establish Player Value, Human evidence, rights clearance, store release, commercial readiness, or the readiness of every Game genre/platform. Game retains domain semantics; Operations owns node package desired state; the compatibility Workstation contract projects exact physical equipment; Runtime owns physical command execution; mature engine/platform mechanisms retain their native authority.
