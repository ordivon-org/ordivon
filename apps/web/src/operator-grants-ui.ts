/** Load an explicit immutable build at startup; no request-dependent filesystem access. */
import { readFileSync } from "node:fs";
import { join } from "node:path";

type Asset = { readonly contentType: string; readonly bytes: Buffer };
const prefix = "/_web/grants/";
function assetPath(value: unknown, extension?: "js" | "css"): string {
  if (typeof value !== "string" || !/^assets\/[A-Za-z0-9_-]+\.(js|css)$/.test(value) ||
      (extension !== undefined && !value.endsWith("." + extension))) {
    throw new Error("Invalid operator UI asset path");
  }
  return value;
}
export function loadOperatorGrantsUi(dist: string): {html: string; assets: ReadonlyMap<string, Asset>} {
  const manifest: unknown = JSON.parse(readFileSync(join(dist, ".vite", "manifest.json"), "utf8"));
  if (manifest === null || typeof manifest !== "object" || Array.isArray(manifest)) throw Error("Invalid operator UI manifest");
  const entries = manifest as Record<string, {file?: unknown; css?: unknown; isEntry?: unknown; imports?: unknown; dynamicImports?: unknown; assets?: unknown}>;
  const entry = entries["operator.html"];
  if (entry?.isEntry !== true) throw Error("Missing operator UI entry");
  const script = assetPath(entry.file, "js");
  const assets = new Map<string, Asset>();
  const add = (path: string) => {
    if (!assets.has(prefix + path)) assets.set(prefix + path, {
      contentType: path.endsWith(".css") ? "text/css; charset=utf-8" : "text/javascript; charset=utf-8",
      bytes: readFileSync(join(dist, path)),
    });
  };
  const styles = (record: {css?: unknown}): string[] => {
    if (record.css === undefined) return [];
    if (!Array.isArray(record.css)) throw Error("Invalid operator UI styles");
    return record.css.map(value => assetPath(value, "css"));
  };
  for (const record of Object.values(entries)) {
    if (record === null || typeof record !== "object") throw Error("Invalid operator UI asset");
    for (const refs of [record.imports, record.dynamicImports]) {
      if (refs === undefined) continue;
      if (!Array.isArray(refs) || refs.some(ref => typeof ref !== "string" || !Object.hasOwn(entries, ref))) {
        throw Error("Invalid operator UI import graph");
      }
    }
    // This target supports script/style assets only, not an arbitrary file server.
    if (record.assets !== undefined && (!Array.isArray(record.assets) || record.assets.length !== 0)) {
      throw Error("Unsupported operator UI auxiliary assets");
    }
    add(assetPath(record.file));
    for (const css of styles(record)) add(css);
  }
  const html = '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1"><title>Agent grants | Ordivon</title>' +
    styles(entry).map(path => '<link rel="stylesheet" href="' + prefix + path + '">').join("") +
    '</head><body><div id="root"></div><noscript>JavaScript is required for this operator view.</noscript>' +
    '<script type="module" src="' + prefix + script + '"></script></body></html>';
  return {html, assets};
}
