import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawnSync } from "node:child_process";
import { copyFileSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { resolveGameEquipment } from "../../scripts/equipment-surface.ts";

const root = dirname(fileURLToPath(import.meta.url));
const project = join(root, "godot");
const buildDir = join(root, "build");
const build = join(buildDir, "ordivon-game-cold-start-r1.x86_64");
const projectSourceFiles = ["project.godot", "export_presets.cfg", "main.tscn", "main.gd"] as const;
const childEnv = { ...process.env, LC_ALL: "C", TZ: "UTC" };

function sha256(path: string): string {
  const h = createHash("sha256");
  h.update(readFileSync(path));
  return `sha256:${h.digest("hex")}`;
}

function execute(executable: string, args: string[], cwd = project) {
  const cp = spawnSync(executable, args, { cwd, encoding: "utf8", timeout: 120_000, env: childEnv });
  if (cp.error) throw cp.error;
  assert.equal(cp.status, 0, `${executable} ${args.join(" ")} failed\nSTDOUT:\n${cp.stdout}\nSTDERR:\n${cp.stderr}`);
  return { stdout: cp.stdout, stderr: cp.stderr };
}

const engine = resolveGameEquipment("engine.project.execute");
assert.equal(engine.state, "AVAILABLE", JSON.stringify(engine));
assert.equal(engine.binding.provider, "workstation.professional-software");
const godot = engine.binding.executable as string;
assert.ok(existsSync(godot), godot);

const godotVersion = execute(godot, ["--version"], root).stdout.trim();
const templateVersion = godotVersion.match(/^(\d+\.\d+\.\d+\.stable)/)?.[1];
assert.ok(templateVersion, `cannot derive stable export-template version from ${godotVersion}`);
const dataHome = process.env.XDG_DATA_HOME ?? (process.env.HOME ? join(process.env.HOME, ".local", "share") : undefined);
assert.ok(dataHome, "XDG_DATA_HOME or HOME is required to bind the Godot export template");
const releaseTemplate = join(dataHome, "godot", "export_templates", templateVersion, "linux_release.x86_64");
assert.ok(existsSync(releaseTemplate), `missing exact Godot release template: ${releaseTemplate}`);
const releaseTemplateDigest = sha256(releaseTemplate);

rmSync(buildDir, { recursive: true, force: true });
mkdirSync(buildDir, { recursive: true });

const scratch = mkdtempSync(join(tmpdir(), "ordivon-game-godot-repro-"));
const cleanProject = join(scratch, "project");
const scratchBuild = join(scratch, "ordivon-game-cold-start-r1.x86_64");
mkdirSync(cleanProject, { recursive: true });
for (const name of projectSourceFiles) copyFileSync(join(project, name), join(cleanProject, name));

let firstBuildDigest = "";
let secondBuildDigest = "";
let byteLength = 0;
try {
  const sourceRun = execute(godot, ["--headless", "--path", cleanProject], cleanProject);
  assert.match(sourceRun.stdout + sourceRun.stderr, /ORDIVON_GAME_COLD_START_OK/);

  rmSync(join(cleanProject, ".godot"), { recursive: true, force: true });
  execute(godot, ["--headless", "--path", cleanProject, "--export-release", "Linux/X11", scratchBuild], cleanProject);
  assert.ok(existsSync(scratchBuild), `${scratchBuild} was not exported`);
  byteLength = statSync(scratchBuild).size;
  assert.ok(byteLength > 1_000_000, `unexpectedly small build: ${byteLength}`);
  firstBuildDigest = sha256(scratchBuild);

  rmSync(join(cleanProject, ".godot"), { recursive: true, force: true });
  rmSync(scratchBuild, { force: true });
  execute(godot, ["--headless", "--path", cleanProject, "--export-release", "Linux/X11", scratchBuild], cleanProject);
  secondBuildDigest = sha256(scratchBuild);
  assert.equal(
    secondBuildDigest,
    firstBuildDigest,
    `Godot export is not byte reproducible inside the declared boundary: ${firstBuildDigest} != ${secondBuildDigest}`,
  );

  copyFileSync(scratchBuild, build);
} finally {
  rmSync(scratch, { recursive: true, force: true });
}

const buildRun = execute(build, ["--headless"], buildDir);
assert.match(buildRun.stdout + buildRun.stderr, /ORDIVON_GAME_COLD_START_OK/);

const receipt = {
  schemaVersion: 2,
  kind: "ordivon.game.production-cold-start-r1",
  standing: "MECHANICAL_PRODUCTION_SLICE_AND_BOUNDED_BIT_REPRODUCIBILITY_PASS",
  engine: {
    equipmentId: engine.binding.equipmentId,
    provider: engine.binding.provider,
    executable: engine.binding.executable,
    executableDigest: engine.binding.executableDigest,
    bindingDigest: engine.binding.bindingDigest,
    version: godotVersion,
  },
  exportTemplate: {
    path: releaseTemplate,
    sha256: releaseTemplateDigest,
  },
  source: {
    project: "experiments/production-smoke-r1/godot",
    files: projectSourceFiles,
    projectGodotDigest: sha256(join(project, "project.godot")),
    sceneDigest: sha256(join(project, "main.tscn")),
    scriptDigest: sha256(join(project, "main.gd")),
    exportPresetDigest: sha256(join(project, "export_presets.cfg")),
  },
  build: {
    relativePath: "experiments/production-smoke-r1/build/ordivon-game-cold-start-r1.x86_64",
    byteLength,
    sha256: sha256(build),
    sourceExecutionMarker: "ORDIVON_GAME_COLD_START_OK",
    exportedExecutionMarker: "ORDIVON_GAME_COLD_START_OK",
  },
  reproducibility: {
    standing: "BIT_REPRODUCIBLE_WITHIN_DECLARED_BOUNDARY",
    firstBuildDigest,
    secondBuildDigest,
    cleanGodotStateBeforeEachExport: true,
    fixedEnvironment: { LC_ALL: "C", TZ: "UTC" },
    boundary: "same repository source files + same Godot editor bytes + same Linux x86_64 release-template bytes + same host/target class + unsigned embedded-PCK export",
    notEstablished: [
      "arbitrary Godot projects or importers",
      "cross-Godot-version reproducibility",
      "cross-export-template reproducibility",
      "cross-OS or cross-architecture reproducibility",
      "code-signed or notarized artifact byte identity",
      "store-generated package byte identity",
    ],
  },
  claimsNotMinted: ["PLAYER_VALUE", "HUMAN_EVIDENCE", "RIGHTS", "STORE_RELEASE", "COMMERCIAL_READINESS"],
};

process.stdout.write(`${JSON.stringify(receipt, null, 2)}\n`);
