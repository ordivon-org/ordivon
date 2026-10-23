import { access, readFile } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { resolve } from "node:path";
import process from "node:process";

const motionManifest = JSON.parse(await readFile(new URL("../apps/motion-remotion/package.json", import.meta.url), "utf8"));
const runtimeVersion = motionManifest.dependencies?.remotion;
const cliVersion = motionManifest.devDependencies?.["@remotion/cli"];
if (!runtimeVersion || runtimeVersion !== cliVersion) {
  process.stderr.write(`Media Remotion dependency contract failed: remotion=${runtimeVersion ?? "missing"}, @remotion/cli=${cliVersion ?? "missing"}; pin both to the same exact version.\n`);
  process.exit(2);
}

const required = [
  ["TypeScript", "node_modules/.bin/tsc"],
  ["workspace dependency metadata", "node_modules/.modules.yaml"],
];
const missing = [];
for (const [label, relativePath] of required) {
  try { await access(resolve(process.cwd(), relativePath), fsConstants.R_OK); }
  catch { missing.push(`${label} (${relativePath})`); }
}

if (missing.length) {
  process.stderr.write([
    "Studio JavaScript dependencies are not materialized in this Workspace.",
    ...missing.map((item) => `- missing: ${item}`),
    "Acquire explicitly with `mise exec -- pnpm install --frozen-lockfile` (or `scripts/owner-environment bootstrap`), then replay the intended command.",
    "Do not use an ordinary `pnpm run` command as the recovery entry: Workstation intentionally fails closed before project dependencies are materialized.",
    "",
  ].join("\n"));
  process.exit(2);
}

process.stdout.write("studio_js_dependencies=ready\n");
