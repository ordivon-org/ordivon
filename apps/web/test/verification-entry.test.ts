import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { delimiter, dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

test("owner verification propagates a failing package ci script", { timeout: 45_000 }, () => {
  const owner = dirname(fileURLToPath(new URL("../mise.toml", import.meta.url)));
  const metadata = spawnSync("mise", ["tasks", "info", "verify", "--json"], {
    cwd: owner, encoding: "utf8", timeout: 15_000,
  });
  assert.equal(metadata.status, 0, metadata.stderr);
  const task = JSON.parse(metadata.stdout) as { run: string[] };
  const root = mkdtempSync(join(tmpdir(), "ordivon-web-verify-"));
  const binding = spawnSync("mise", ["which", "pnpm"], { cwd: owner, encoding: "utf8" });
  assert.equal(binding.status, 0, binding.stderr);
  const env: NodeJS.ProcessEnv = {
    ...process.env, CI: "true", BASH_ENV: "/dev/null", MISE_TRUSTED_CONFIG_PATHS: root,
    PATH: [dirname(binding.stdout.trim()), dirname(process.execPath), process.env.PATH].join(delimiter),
  };
  const consumer = join(root, "apps/web");
  const provider = join(root, "platform/security/contracts/agent-request-verifier-v1");
  try {
    for (const [directory, name] of [[consumer, "web-fixture"], [provider, "verifier-fixture"]]) {
      assert.ok(directory);
      mkdirSync(directory, { recursive: true });
      if (directory === consumer) {
        // Internal pnpm commands may re-enter through mise shims in this fixture.
        writeFileSync(join(directory, "mise.toml"), readFileSync(join(owner, "mise.toml")));
      }
      writeFileSync(join(directory, "package.json"), JSON.stringify({
        name, private: true, scripts: { ci: "node -e \"require('node:fs').writeFileSync('ci-ran','yes');process.exit(29)\"" },
      }));
      const lock = spawnSync("pnpm", ["install", "--lockfile-only", "--offline"], {
        cwd: directory, encoding: "utf8", timeout: 15_000,
        env,
      });
      assert.equal(lock.status, 0, lock.stdout + lock.stderr);
    }
    const result = spawnSync("/bin/bash", ["-c", task.run.join("\n")], {
      cwd: consumer, encoding: "utf8", timeout: 30_000,
      env,
    });
    assert.equal(result.status, 29, result.stdout + result.stderr);
    assert.equal(readFileSync(join(consumer, "ci-ran"), "utf8"), "yes");
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
