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

test("invalid Workstation browser bindings fall back to the supplied executable", () => {
  const root = mkdtempSync(join(tmpdir(), "game-browser-negative-"));
  const fallback = join(root, "fallback-chrome");
  const tool = join(root, "tool-binding");
  const before = {
    tool: process.env.ORDIVON_TOOL_BINDING,
    explicit: process.env.ORDIVON_CHROMIUM_EXECUTABLE,
    browsers: process.env.PLAYWRIGHT_BROWSERS_PATH,
  };
  try {
    writeFileSync(fallback, "browser");
    chmodSync(fallback, 0o755);
    process.env.ORDIVON_TOOL_BINDING = tool;
    delete process.env.ORDIVON_CHROMIUM_EXECUTABLE;
    delete process.env.PLAYWRIGHT_BROWSERS_PATH;
    const valid = {
      schemaVersion: 1,
      kind: "ordivon.workstation.v2.tool-binding",
      state: "AVAILABLE",
      equipmentId: "browser:playwright-chromium",
      executionTarget: "local_linux",
      observedExecutable: fallback,
    };
    for (const invalid of [
      { ...valid, kind: "ordivon.workstation-equipment-binding" },
      { ...valid, equipmentId: "browser:unexpected" },
      { ...valid, executionTarget: "windows_native" },
      { ...valid, state: "UNAVAILABLE" },
      { ...valid, observedExecutable: join(root, "does-not-exist") },
    ]) {
      writeFileSync(tool, "#!/bin/sh\\nprintf '%s\\n' '" + JSON.stringify(invalid) + "'\\n");
      chmodSync(tool, 0o755);
      assert.equal(resolveChromiumExecutable(fallback), fallback);
    }
  } finally {
    if (before.tool === undefined) delete process.env.ORDIVON_TOOL_BINDING; else process.env.ORDIVON_TOOL_BINDING = before.tool;
    if (before.explicit === undefined) delete process.env.ORDIVON_CHROMIUM_EXECUTABLE; else process.env.ORDIVON_CHROMIUM_EXECUTABLE = before.explicit;
    if (before.browsers === undefined) delete process.env.PLAYWRIGHT_BROWSERS_PATH; else process.env.PLAYWRIGHT_BROWSERS_PATH = before.browsers;
    rmSync(root, { recursive: true, force: true });
  }
});
