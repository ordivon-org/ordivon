import { access, readFile } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import process from "node:process";

const root = new URL("../", import.meta.url);
const motionRoot = new URL("apps/motion-remotion/", root);

function finish(status, code, detail = "") {
  process.stdout.write(`studio_js_dependencies=${status}\n`);
  if (detail) process.stderr.write(detail + "\n");
  process.exitCode = code;
}

async function observe() {
  let motionManifest;
  try {
    motionManifest = JSON.parse(await readFile(new URL("package.json", motionRoot), "utf8"));
  } catch (error) {
    return finish("unobserved", 4, `Cannot observe Media dependency declaration: ${error.message}`);
  }
  const runtimeVersion = motionManifest?.dependencies?.remotion;
  const cliVersion = motionManifest?.devDependencies?.["@remotion/cli"];
  // These two packages share one release contract. Other packages retain
  // their compatible ranges and pnpm's own resolution semantics.
  if (typeof runtimeVersion !== "string" || !/^\d+\.\d+\.\d+(?:-[\w.-]+)?(?:\+[\w.-]+)?$/.test(runtimeVersion)
      || runtimeVersion !== cliVersion) {
    return finish("contract-invalid", 3,
      `Media Remotion dependency contract failed: remotion=${runtimeVersion ?? "missing"}, @remotion/cli=${cliVersion ?? "missing"}; use the same exact release.`);
  }

  const missing = [];
  for (const relativePath of ["node_modules/.bin/tsc", "node_modules/.modules.yaml"]) {
    try {
      await access(new URL(relativePath, root), fsConstants.R_OK);
    } catch (error) {
      if (error.code !== "ENOENT" && error.code !== "ENOTDIR")
        return finish("unobserved", 4, `Cannot observe ${relativePath}: ${error.message}`);
      missing.push(relativePath);
    }
  }
  for (const name of ["remotion", "@remotion/cli"]) {
    let installed;
    try {
      installed = JSON.parse(await readFile(new URL(`node_modules/${name}/package.json`, motionRoot), "utf8"));
    } catch (error) {
      if (error.code !== "ENOENT" && error.code !== "ENOTDIR" && !(error instanceof SyntaxError))
        return finish("unobserved", 4, `Cannot observe ${name}: ${error.message}`);
      missing.push(`${name}: missing or invalid local package metadata`);
      continue;
    }
    if (installed?.name !== name || installed?.version !== runtimeVersion)
      missing.push(`${name}: installed identity does not match ${runtimeVersion}`);
  }
  if (missing.length)
    return finish("not-ready", 2, [
      "Studio JavaScript dependencies are not materialized or current in this Workspace.",
      ...missing.map((item) => `- ${item}`),
      "Acquire explicitly with `mise exec -- pnpm install --frozen-lockfile`, then replay the intended command.",
    ].join("\n"));

  // This observes selected installed identities, not a proof of package bytes
  // or every transitive dependency. The project-pinned pnpm resolver owns those
  // installation/currentness rules.
  return finish("ready", 0);
}

await observe();
