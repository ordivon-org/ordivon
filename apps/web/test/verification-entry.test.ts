import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

test("verification provisions OPA and propagates a failing package ci script", { timeout: 45_000 }, () => {
  const owner = dirname(fileURLToPath(new URL("../mise.toml", import.meta.url)));
  const root = mkdtempSync(join(tmpdir(), "ordivon-web-verify-"));
  try {
    const unavailable = join(root, "unavailable-tools");
    mkdirSync(unavailable);
    writeFileSync(join(unavailable, "opa"), "#!/bin/sh\nexit 127\n", { mode: 0o755 });
    const binding = spawnSync("mise", ["which", "pnpm"], { cwd: owner, encoding: "utf8" });
    assert.equal(binding.status, 0, binding.stderr);
    const mise = process.env.PATH?.split(delimiter).map((dir) => join(dir, "mise")).find((path) => existsSync(path));
    assert.ok(mise);
    // Start a fresh tool context instead of inheriting the parent activation.
    const env: NodeJS.ProcessEnv = {
      HOME: process.env.HOME, USER: process.env.USER, CI: "true", BASH_ENV: "/dev/null",
      MISE_DATA_DIR: process.env.MISE_DATA_DIR, MISE_CACHE_DIR: process.env.MISE_CACHE_DIR,
      MISE_CONFIG_DIR: process.env.MISE_CONFIG_DIR, MISE_TRUSTED_CONFIG_PATHS: root,
      PATH: [unavailable, dirname(binding.stdout.trim()), dirname(process.execPath), dirname(mise), "/usr/bin", "/bin"].join(delimiter),
    };
    const consumer = join(root, "apps/web");
    const provider = join(root, "platform/security/contracts/agent-request-verifier-v1");
    for (const [directory, name] of [[consumer, "web-fixture"], [provider, "verifier-fixture"]]) {
      assert.ok(directory);
      mkdirSync(directory, { recursive: true });
      if (directory === consumer) {
        writeFileSync(join(directory, "mise.toml"), readFileSync(join(owner, "mise.toml")));
      }
      writeFileSync(join(directory, "package.json"), JSON.stringify({
        name, private: true, scripts: { ci: "node verify-fixture.cjs" },
      }));
      writeFileSync(join(directory, "verify-fixture.cjs"), [
        'const { spawnSync } = require("node:child_process");',
        'if (spawnSync("opa", ["version"]).status !== 0) process.exit(28);',
        'require("node:fs").writeFileSync("ci-ran", "yes");',
        "process.exit(29);",
      ].join("\n"));
      const lock = spawnSync("pnpm", ["install", "--lockfile-only", "--offline"], {
        cwd: directory, encoding: "utf8", timeout: 15_000, env,
      });
      assert.equal(lock.status, 0, lock.stdout + lock.stderr);
    }
    const result = spawnSync(mise, ["run", "verify"], {
      cwd: consumer, encoding: "utf8", timeout: 30_000, env,
    });
    assert.equal(result.status, 29, result.stdout + result.stderr);
    assert.equal(readFileSync(join(consumer, "ci-ran"), "utf8"), "yes");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
