import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveGameEquipment } from "../../scripts/equipment-surface.ts";

const root = dirname(fileURLToPath(import.meta.url));
const project = join(root, "godot");
const buildDir = join(root, "build");
const build = join(buildDir, "ordivon-game-cold-start-r1.x86_64");

function sha256(path: string): string {
  const h = createHash("sha256");
  h.update(readFileSync(path));
  return `sha256:${h.digest("hex")}`;
}

function execute(executable: string, args: string[], cwd = project) {
  const cp = spawnSync(executable, args, { cwd, encoding: "utf8", timeout: 120_000, env: process.env });
  if (cp.error) throw cp.error;
  assert.equal(cp.status, 0, `${executable} ${args.join(" ")} failed\nSTDOUT:\n${cp.stdout}\nSTDERR:\n${cp.stderr}`);
  return { stdout: cp.stdout, stderr: cp.stderr };
}

const engine = resolveGameEquipment("engine.project.execute");
assert.equal(engine.state, "AVAILABLE", JSON.stringify(engine));
assert.equal(engine.binding.provider, "workstation.professional-software");
const godot = engine.binding.executable as string;
assert.ok(existsSync(godot), godot);

rmSync(buildDir, { recursive: true, force: true });
mkdirSync(buildDir, { recursive: true });

execute(godot, ["--headless", "--editor", "--path", project, "--quit"]);
const sourceRun = execute(godot, ["--headless", "--path", project]);
assert.match(sourceRun.stdout + sourceRun.stderr, /ORDIVON_GAME_COLD_START_OK/);

const exported = execute(godot, ["--headless", "--path", project, "--export-release", "Linux/X11", build]);
assert.ok(existsSync(build), `${build} was not exported`);
assert.ok(statSync(build).size > 1_000_000, `unexpectedly small build: ${statSync(build).size}`);

const buildRun = execute(build, ["--headless"], buildDir);
assert.match(buildRun.stdout + buildRun.stderr, /ORDIVON_GAME_COLD_START_OK/);

const receipt = {
  schemaVersion: 1,
  kind: "ordivon.game.production-cold-start-r1",
  standing: "MECHANICAL_PRODUCTION_SLICE_PASS_NOT_PRODUCT_RELEASE_OR_HUMAN_VALUE",
  engine: {
    equipmentId: engine.binding.equipmentId,
    provider: engine.binding.provider,
    executable: engine.binding.executable,
    executableDigest: engine.binding.executableDigest,
    bindingDigest: engine.binding.bindingDigest,
  },
  source: {
    project: "experiments/production-smoke-r1/godot",
    projectGodotDigest: sha256(join(project, "project.godot")),
    sceneDigest: sha256(join(project, "main.tscn")),
    scriptDigest: sha256(join(project, "main.gd")),
    exportPresetDigest: sha256(join(project, "export_presets.cfg")),
  },
  build: {
    relativePath: "experiments/production-smoke-r1/build/ordivon-game-cold-start-r1.x86_64",
    byteLength: statSync(build).size,
    sha256: sha256(build),
    sourceExecutionMarker: "ORDIVON_GAME_COLD_START_OK",
    exportedExecutionMarker: "ORDIVON_GAME_COLD_START_OK",
  },
  claimsNotMinted: ["PLAYER_VALUE", "HUMAN_EVIDENCE", "RIGHTS", "STORE_RELEASE", "COMMERCIAL_READINESS"],
};

process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
