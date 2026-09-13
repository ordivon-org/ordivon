# Game Production Cold Start R1

This is a bounded production-path acceptance slice, not a product, framework, or release workflow.

It exists to answer one mechanical question: can a new Game-owned Godot project start from repository source, resolve the current Workstation physical engine binding, execute from source, export a real Linux executable with the installed Godot export templates, and execute that exported artifact successfully?

Run:

```bash
pnpm e2e:production-smoke
```

The harness under `experiments/production-smoke-r1/`:

1. resolves `engine.project.execute` through the current `equipment-binding` contract;
2. requires an exact `workstation.professional-software` Godot binding;
3. imports and runs a new standalone Godot project;
4. exports a Linux x86_64 executable using the repository-owned export preset;
5. runs the exported executable again and requires `ORDIVON_GAME_COLD_START_OK`;
6. prints a digest-bound receipt for the engine binding, source inputs, and exported artifact.

The generated `build/` directory is intentionally ignored by Git. The build is a consequence, not source authority.

A PASS establishes only a mechanical production slice. It does **not** establish Player Value, Human evidence, rights clearance, store release, commercial readiness, or the readiness of every Game genre/platform. Game retains domain semantics; Operations owns node package desired state; the compatibility Workstation contract projects exact physical equipment; Runtime owns physical command execution; mature engine/platform mechanisms retain their native authority.
