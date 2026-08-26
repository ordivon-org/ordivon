import test from "node:test";
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
  assert.deepEqual(catalog.operations.map((x) => x.operation).sort(), ["gpu.frame.inspect", "level.topology.author", "sprite.source.author", "vector.asset.author"]);
});

test("exact Workstation binding is consumed but never becomes gameplay authority", () => {
  const root = mkdtempSync(join(tmpdir(), "game-equipment-"));
  try {
    const tool = join(root, "equipment-binding");
    writeFileSync(tool, `#!/usr/bin/env python3
import json
print(json.dumps({"schemaVersion":1,"kind":"ordivon.workstation-equipment-binding","state":"AVAILABLE","equipmentId":"game-tiled-e1","executable":"/exact/tiled","bindingDigest":"sha256:${"a".repeat(64)}"}))
`);
    chmodSync(tool, 0o755);
    const value = resolveGameEquipment("level.topology.author", { ORDIVON_EQUIPMENT_BINDING: tool });
    assert.equal(value.state, "AVAILABLE");
    assert.equal(value.binding.executable, "/exact/tiled");
    assert.equal(value.gameplayAuthorityGranted, false);
    assert.match(value.admission, /Game spatial-layout validation/);
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

test("missing Workstation projection is unresolved rather than replaced by ambient PATH folklore", () => {
  const value = resolveGameEquipment("gpu.frame.inspect", { ORDIVON_EQUIPMENT_BINDING: join(tmpdir(), "definitely-missing-equipment-binding") });
  assert.equal(value.state, "UNRESOLVED");
});
