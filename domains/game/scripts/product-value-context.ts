import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const PROJECT_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const CURRENT_RECEIPT = "evidence/station-zero-v3/product-value-current.json";

type SourceFence = { path: string; digest: string; role: string };
type CurrentReceipt = {
  schemaVersion: 1;
  kind: "ordivon.game.station-zero-v3-product-value-current";
  truthRole: string;
  subject: string;
  sourceFences: SourceFence[];
  lanes: unknown[];
  retainedConsequences: unknown[];
  boundaries: string[];
};

function sha256(path: string): string {
  return `sha256:${createHash("sha256").update(readFileSync(path)).digest("hex")}`;
}

function loadReceipt(root: string): CurrentReceipt {
  const path = resolve(root, CURRENT_RECEIPT);
  const value = JSON.parse(readFileSync(path, "utf8")) as CurrentReceipt;
  if (value?.schemaVersion !== 1 || value?.kind !== "ordivon.game.station-zero-v3-product-value-current") {
    throw new Error("Product Value current receipt has unsupported identity");
  }
  if (!Array.isArray(value.sourceFences) || value.sourceFences.length === 0) {
    throw new Error("Product Value current receipt has no source fences");
  }
  return value;
}

export function stationZeroV3ProductValueContext(root = PROJECT_ROOT) {
  const receipt = loadReceipt(root);
  const checks = receipt.sourceFences.map((fence) => {
    const observedDigest = sha256(resolve(root, fence.path));
    return {
      path: fence.path,
      role: fence.role,
      expectedDigest: fence.digest,
      observedDigest,
      current: observedDigest === fence.digest,
    };
  });
  const stale = checks.filter((check) => !check.current).map((check) => check.path);
  const current = stale.length === 0;
  return {
    schemaVersion: 1,
    kind: "ordivon.game.station-zero-v3-product-value-context",
    truthRole: "derived-read-only-evidence-projection",
    subject: receipt.subject,
    currentness: {
      state: current ? "CURRENT" : "STALE",
      usableForCurrentDecision: current,
      stalePaths: stale,
      checks,
    },
    // Currentness is enforced structurally, not left to prompt interpretation.
    // Historical lane/consequence payloads remain recoverable through sourceReceipt,
    // but ordinary decision cognition receives none of them after any semantic fence drifts.
    lanes: current ? receipt.lanes : [],
    retainedConsequences: current ? receipt.retainedConsequences : [],
    historicalEvidence: current ? null : {
      state: "WITHHELD_STALE",
      sourceReceipt: CURRENT_RECEIPT,
      laneCount: receipt.lanes.length,
      retainedConsequenceCount: receipt.retainedConsequences.length,
      reason: "One or more semantic source fences drifted; revalidate the exact standing/evaluator before consuming historical evidence for a current product decision.",
    },
    boundaries: receipt.boundaries,
    sourceReceipt: CURRENT_RECEIPT,
    escapeHatch: {
      standing: "docs/STATION_ZERO_V3_PRODUCT_VALUE.md",
      evaluator: "scripts/eval-station-zero-v3-product-value.ts",
      rawEvidenceRoot: "evidence/station-zero-v3",
    },
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  process.stdout.write(`${JSON.stringify(stationZeroV3ProductValueContext(), null, 2)}\n`);
}
