import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const DIRECTION_SOURCE = "docs/GAME_CORE_RESEARCH_RESET.md";
const AUTHORITY_SOURCE = "docs/authority.md";
const CURRENT_FRONTIER_HEADING = "## Current frontier";
const AUTHORITY_GUARDS = [
  "`AGENTS.md` governs repository work rather than product truth.",
  "Its historical stage labels do not select the next Ordivon Game product or redefine current Game Core research.",
] as const;

function sha256(value: string): string {
  return `sha256:${createHash("sha256").update(value).digest("hex")}`;
}

function section(text: string, heading: string): string {
  const start = text.indexOf(heading);
  if (start < 0) throw new Error(`Missing required current-direction section: ${heading}`);
  const searchFrom = start + heading.length;
  const next = text.indexOf("\n## ", searchFrom);
  return text.slice(start, next < 0 ? text.length : next).trim();
}

export function gameCurrentDirectionContext(root = PROJECT_ROOT) {
  const directionPath = resolve(root, DIRECTION_SOURCE);
  const authorityPath = resolve(root, AUTHORITY_SOURCE);
  const directionSource = readFileSync(directionPath, "utf8");
  const authoritySource = readFileSync(authorityPath, "utf8");
  for (const guard of AUTHORITY_GUARDS) {
    if (!authoritySource.includes(guard)) throw new Error(`Missing current-direction authority guard: ${guard}`);
  }
  return {
    schemaVersion: 1,
    kind: "ordivon.game.current-direction-context",
    truthRole: "exact-source-current-direction-projection-not-product-authority",
    currentness: {
      state: "CURRENT_TO_WORKSPACE_SOURCE",
      canonicalRevisionClaimed: false,
    },
    direction: {
      sourcePath: DIRECTION_SOURCE,
      sourceDigest: sha256(directionSource),
      section: "Current frontier",
      exactSource: section(directionSource, CURRENT_FRONTIER_HEADING),
    },
    authority: {
      sourcePath: AUTHORITY_SOURCE,
      sourceDigest: sha256(authoritySource),
      exactGuards: [...AUTHORITY_GUARDS],
    },
    nonClaims: [
      "This projection does not select a product, assign a G0-G8 stage, or mint Game truth.",
      "This projection does not summarize historical programme evidence or replace owner source documents.",
      "Repository/Git currentness beyond the invoked workspace source is not claimed here.",
    ],
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  process.stdout.write(`${JSON.stringify(gameCurrentDirectionContext(), null, 2)}\n`);
}
