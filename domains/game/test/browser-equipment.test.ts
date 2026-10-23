import test from "node:test";
import assert from "node:assert/strict";
import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { resolveChromiumExecutable } from "../tools/browser-equipment.ts";

test("Game browser discovery consumes canonical Workstation tool binding", () => {
  const root = mkdtempSync(join(tmpdir(), "game-browser-binding-"));
  const browser = join(root, "chrome");
  const tool = join(root, "tool-binding");
  try {
    writeFileSync(browser, "browser");
    chmodSync(browser, 0o755);
    writeFileSync(tool, `#!/usr/bin/env python3
import json
print(json.dumps({
  "schemaVersion": 1,
  "kind": "ordivon.workstation.v2.tool-binding",
  "truthRole": "node-local-materialization-binding",
  "state": "AVAILABLE",
  "equipmentId": "browser:playwright-chromium",
  "executionTarget": "local_linux",
  "observedExecutable": ${JSON.stringify(browser)}
}))
`);
    chmodSync(tool, 0o755);
    const previous = {
      tool: process.env.ORDIVON_TOOL_BINDING,
      oldTool: process.env.ORDIVON_EQUIPMENT_BINDING,
      explicit: process.env.ORDIVON_CHROMIUM_EXECUTABLE,
      browsers: process.env.PLAYWRIGHT_BROWSERS_PATH,
    };
    delete process.env.ORDIVON_EQUIPMENT_BINDING;
    delete process.env.ORDIVON_CHROMIUM_EXECUTABLE;
    delete process.env.PLAYWRIGHT_BROWSERS_PATH;
    process.env.ORDIVON_TOOL_BINDING = tool;
    try {
      assert.equal(resolveChromiumExecutable(undefined), browser);
    } finally {
      if (previous.tool === undefined) delete process.env.ORDIVON_TOOL_BINDING; else process.env.ORDIVON_TOOL_BINDING = previous.tool;
      if (previous.oldTool === undefined) delete process.env.ORDIVON_EQUIPMENT_BINDING; else process.env.ORDIVON_EQUIPMENT_BINDING = previous.oldTool;
      if (previous.explicit === undefined) delete process.env.ORDIVON_CHROMIUM_EXECUTABLE; else process.env.ORDIVON_CHROMIUM_EXECUTABLE = previous.explicit;
      if (previous.browsers === undefined) delete process.env.PLAYWRIGHT_BROWSERS_PATH; else process.env.PLAYWRIGHT_BROWSERS_PATH = previous.browsers;
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
