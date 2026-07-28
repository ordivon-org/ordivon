import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { relative, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { sha256 } from "../digest.ts";

export interface EvaluatedContractVersion {
  id: string;
  version: number;
}

export interface EvaluatedInputFile {
  path: string;
  sha256: string;
  bytes: number;
}

export interface EvaluatedInputManifest {
  schemaVersion: 1;
  product: string;
  packageVersion: string;
  scenarioContracts: EvaluatedContractVersion[];
  rulesetContracts: EvaluatedContractVersion[];
  files: EvaluatedInputFile[];
  evaluatedInputsDigest: string;
  sourceCommit: string | null;
  sourceTree: string | null;
}

export const PROJECT_ROOT = fileURLToPath(new URL("../../", import.meta.url));

const EVALUATED_INPUT_ROOTS = [
  ".github/workflows",
  "scripts",
  "src",
  "test",
  "web",
  "package.json",
  "pnpm-lock.yaml",
  "tsconfig.json",
] as const;

interface PackageIdentity {
  name: string;
  version: string;
}

function packageIdentity(root: string): PackageIdentity {
  const value = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8")) as Partial<PackageIdentity>;
  if (!value.name?.trim() || !value.version?.trim()) throw new TypeError("package.json requires name and version");
  return { name: value.name, version: value.version };
}

function posixPath(root: string, path: string): string {
  return relative(root, path).split(sep).join("/");
}

function collectFiles(root: string, path: string, output: string[]): void {
  const info = statSync(path);
  if (info.isFile()) {
    output.push(path);
    return;
  }
  if (!info.isDirectory()) return;
  for (const entry of readdirSync(path).sort()) collectFiles(root, resolve(path, entry), output);
}

export function listEvaluatedInputFiles(root = PROJECT_ROOT): string[] {
  const files: string[] = [];
  for (const input of EVALUATED_INPUT_ROOTS) collectFiles(root, resolve(root, input), files);
  return files.map((path) => posixPath(root, path)).sort();
}

export interface CreateEvaluatedInputManifestOptions {
  root?: string;
  scenarioContracts?: EvaluatedContractVersion[];
  rulesetContracts?: EvaluatedContractVersion[];
  sourceCommit?: string | null;
  sourceTree?: string | null;
}

export function createEvaluatedInputManifest(
  options: CreateEvaluatedInputManifestOptions = {},
): EvaluatedInputManifest {
  const root = options.root ?? PROJECT_ROOT;
  const pkg = packageIdentity(root);
  const scenarioContracts = [...(options.scenarioContracts ?? [])]
    .sort((left, right) => left.id.localeCompare(right.id) || left.version - right.version);
  const rulesetContracts = [...(options.rulesetContracts ?? [])]
    .sort((left, right) => left.id.localeCompare(right.id) || left.version - right.version);
  const files = listEvaluatedInputFiles(root).map((path) => {
    const content = readFileSync(resolve(root, path));
    return { path, sha256: createHash("sha256").update(content).digest("hex"), bytes: content.byteLength };
  });
  const evaluatedInputs = {
    schemaVersion: 1 as const,
    product: pkg.name,
    packageVersion: pkg.version,
    scenarioContracts,
    rulesetContracts,
    files,
  };
  return {
    ...evaluatedInputs,
    evaluatedInputsDigest: sha256({ kind: "ordivon.game.evaluated-inputs", ...evaluatedInputs }),
    sourceCommit: options.sourceCommit ?? process.env.GITHUB_SHA ?? null,
    sourceTree: options.sourceTree ?? null,
  };
}

export function currentPackageIdentity(root = PROJECT_ROOT): string {
  const pkg = packageIdentity(root);
  return `${pkg.name}@${pkg.version}`;
}
