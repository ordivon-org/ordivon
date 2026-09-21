# Capital legacy replay tools

This directory contains historical qualification/replay tooling, not current Capital runtime entrypoints.

The current operational surface is under src/, config/, contracts/, and scripts/ as exercised by the canonical Capital gates. Historical LEAN Wave-B class names, environment names, fixtures, and evidence coordinates are intentionally preserved here so old experiments remain understandable and reproducible without masquerading as current architecture.

Old scripts paths have no compatibility shims. The path mapping authority is config/legacy_replay_surface_registry.json.
