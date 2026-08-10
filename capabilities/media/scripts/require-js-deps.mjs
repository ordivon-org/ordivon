import { access } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { resolve } from "node:path";
import process from "node:process";

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
    "Run `pnpm bootstrap` (equivalent to `pnpm install --frozen-lockfile`) once, then replay the intended command.",
    "Python-only checks remain available through `pnpm models:check` and `pnpm python:test` without JavaScript bootstrap.",
    "",
  ].join("\n"));
  process.exit(2);
}

process.stdout.write("studio_js_dependencies=ready\n");
