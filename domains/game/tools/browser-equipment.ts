import { execFileSync } from "node:child_process";
import { existsSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join, resolve } from "node:path";

function workstationBinding(): string | undefined {
  const tool = process.env.ORDIVON_EQUIPMENT_BINDING || "/root/tools/bin/equipment-binding";
  if (!existsSync(tool)) return undefined;
  try {
    const value = JSON.parse(execFileSync(tool, ["browser", "--family", "chromium"], { encoding: "utf8", timeout: 15000 }));
    if (value?.schemaVersion !== 1 || value?.kind !== "ordivon.workstation-equipment-binding") return undefined;
    if (value?.state !== "AVAILABLE" || value?.equipmentId !== "browser:playwright-chromium") return undefined;
    if (value?.executionTarget !== "local_linux" || typeof value?.executable !== "string") return undefined;
    return existsSync(value.executable) ? value.executable : undefined;
  } catch {
    return undefined;
  }
}

function findBrowser(root: string, depth = 0): string | undefined {
  if (depth > 4 || !existsSync(root)) return undefined;
  let entries;
  try { entries = readdirSync(root, { withFileTypes: true }); }
  catch { return undefined; }
  for (const entry of entries) {
    if (!entry.isFile() || !["chrome", "headless_shell"].includes(entry.name)) continue;
    const candidate = join(root, entry.name);
    if (existsSync(candidate)) return candidate;
  }
  for (const entry of entries) {
    if (!entry.isDirectory()) continue;
    const found = findBrowser(join(root, entry.name), depth + 1);
    if (found) return found;
  }
  return undefined;
}

export function resolveChromiumExecutable(playwrightExecutablePath: string | undefined): string | undefined {
  const explicit = process.env.ORDIVON_CHROMIUM_EXECUTABLE;
  if (explicit && existsSync(explicit)) return explicit;
  const bound = workstationBinding();
  if (bound) return bound;
  for (const candidate of [playwrightExecutablePath, "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"]) {
    if (candidate && existsSync(candidate)) return candidate;
  }
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, join(homedir(), ".cache", "ms-playwright")].filter((value): value is string => Boolean(value));
  for (const root of [...new Set(roots.map((value) => resolve(value)))]) {
    const found = findBrowser(root);
    if (found) return found;
  }
  return undefined;
}
