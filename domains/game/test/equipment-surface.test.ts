import test from "node:test";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, chmodSync, rmSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { gameEquipmentCatalog, resolveGameEquipment } from "../scripts/equipment-surface.ts";

test("Game equipment catalog preserves domain authority and has no MCP/tool registry authority", () => {
  const catalog = gameEquipmentCatalog();
  assert.equal(catalog.mcpRequired, false);
  assert.equal(catalog.gameplayAuthorityGranted, false);
  assert.equal(catalog.gameOwnsDomainMeaning, true);
  assert.deepEqual(catalog.operations.map((x) => x.operation).sort(), ["engine.project.execute", "gpu.frame.inspect", "level.topology.author", "model3d.source.author", "sprite.source.author", "vector.asset.author"]);
});

test("Tiled is requested as professional software without a caller-supplied executable path", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const log = join(root, "args.json");
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json,sys
open(${JSON.stringify(log)},"w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"professional:tiled:tiled","executable":"/exact/tiled","bindingDigest":"sha256:${"a".repeat(64)}"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("level.topology.author", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    assert.equal(value.binding.executable, "/exact/tiled");
    assert.equal(value.gameplayAuthorityGranted, false);
    assert.match(value.admission, /Game spatial-layout validation/);
    const args = JSON.parse(readFileSync(log, "utf8"));
    assert.deepEqual(args, ["professional", "--software-id", "tiled", "--launcher", "tiled"]);
    assert.ok(!args.some((item: string) => item.includes("/usr/bin/tiled")));
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("Aseprite is requested as managed equipment without caller-supplied executable path", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const log = join(root, "args.json");
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json,sys
open(${JSON.stringify(log)},"w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"game-aseprite-e1","executable":"/managed/aseprite"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("sprite.source.author", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    const args = JSON.parse(readFileSync(log, "utf8"));
    assert.deepEqual(args, ["managed", "--equipment-id", "game-aseprite-e1"]);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("Inkscape is requested as managed equipment without an overlay executable contract", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const log = join(root, "args.json");
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json,sys
open(${JSON.stringify(log)},"w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"game-inkscape-e1","executable":"/managed/inkscape"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("vector.asset.author", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    const args = JSON.parse(readFileSync(log, "utf8"));
    assert.deepEqual(args, ["managed", "--equipment-id", "game-inkscape-e1"]);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("Blender 3D authoring requests Workstation Windows professional software without a caller path", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const log = join(root, "args.json");
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json,sys
open(${JSON.stringify(log)},"w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"professional:blender:blender","provider":"workstation.professional-software","executionTarget":"windows_native","executable":"/mnt/c/Users/example/AppData/Local/Programs/Blender-5.2-Portable/blender.exe","executableDigest":"sha256:${"d".repeat(64)}"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("model3d.source.author", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    assert.equal(value.binding.executionTarget, "windows_native");
    assert.equal(value.binding.equipmentId, "professional:blender:blender");
    assert.ok(value.admission);
    assert.match(value.admission, /engine import\/runtime checks/);
    const args = JSON.parse(readFileSync(log, "utf8"));
    assert.deepEqual(args, ["professional", "--software-id", "blender", "--launcher", "blender"]);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("RenderDoc is requested as professional software without a caller-supplied executable path", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const log = join(root, "args.json");
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json,sys
open(${JSON.stringify(log)},"w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"professional:renderdoc:renderdoccmd","executable":"/exact/renderdoccmd","bindingDigest":"sha256:${"c".repeat(64)}"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("gpu.frame.inspect", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    assert.equal(value.binding.executable, "/exact/renderdoccmd");
    const args = JSON.parse(readFileSync(log, "utf8"));
    assert.deepEqual(args, ["professional", "--software-id", "renderdoc", "--launcher", "renderdoccmd"]);
    assert.ok(!args.some((item: string) => item.includes("/usr/bin/renderdoccmd")));
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("Godot engine execution requests Workstation professional software without a caller path", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const log = join(root, "args.json");
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json,sys
open(${JSON.stringify(log)},"w").write(json.dumps(sys.argv[1:]))
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"professional:godot:godot","provider":"workstation.professional-software","executable":"/exact/godot","executableDigest":"sha256:${"b".repeat(64)}"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("engine.project.execute", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    assert.equal(value.binding.executable, "/exact/godot");
    assert.equal(value.gameplayAuthorityGranted, false);
    const args = JSON.parse(readFileSync(log, "utf8"));
    assert.deepEqual(args, ["professional", "--software-id", "godot", "--launcher", "godot"]);
    assert.ok(!args.some((item: string) => item.includes("/usr/bin/godot")));
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("missing Workstation projection is unresolved rather than replaced by ambient PATH folklore", () => {
  const value = resolveGameEquipment("gpu.frame.inspect", { ORDIVON_EQUIPMENT_BINDING: join(tmpdir(), "definitely-missing-equipment-binding") });
  assert.equal(value.state, "UNRESOLVED");
});

test("production smoke accepts only the actual Workstation v2 professional provider", () => {
  const root = mkdtempSync(join(tmpdir(), "game-workstation-v2-cdc-"));
  const tool = join(root, "equipment-binding");
  const godot = join(root, "godot");
  const entry = fileURLToPath(new URL("../experiments/production-smoke-r1/run.ts", import.meta.url));
  try {
    writeFileSync(godot, "#!/bin/sh\nprintf '%s\\n' '4.7.2.stable.official'\n");
    chmodSync(godot, 0o755);
    for (const provider of [
      "workstation.v2.professional-software",
      "workstation.professional-software",
    ]) {
      const binding = {
        schemaVersion: 1,
        kind: "ordivon.workstation-equipment-binding",
        state: "AVAILABLE",
        equipmentId: "professional:godot:godot",
        provider,
        executable: godot,
        executableDigest: "sha256:" + "a".repeat(64),
      };
      writeFileSync(tool, "#!/usr/bin/env python3\nprint(" + JSON.stringify(JSON.stringify(binding)) + ")\n");
      chmodSync(tool, 0o755);
      const result = spawnSync(process.execPath, [entry], {
        encoding: "utf8",
        timeout: 12000,
        env: { ...process.env, ORDIVON_EQUIPMENT_BINDING: tool, XDG_DATA_HOME: root },
      });
      assert.equal(result.status, 1, result.stderr);
      if (provider === "workstation.v2.professional-software") {
        // The exact consumer contract must pass; no actual Godot template is
        // supplied, so execution stops before exporting a build.
        assert.match(result.stderr, /missing exact Godot release template/);
      } else {
        assert.match(result.stderr, /workstation\.v2\.professional-software/);
        assert.doesNotMatch(result.stderr, /missing exact Godot release template/);
      }
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
