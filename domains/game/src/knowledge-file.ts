/** Source-bound Game knowledge files, shared by existing read-only queries.
 *
 * This is a filesystem read operation, not a Game standard, registry, ranking
 * authority, or new store. The JSON fixtures remain owned by the Game domain.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const GAME_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

/** Return the exact source text and its parsed value from a single read.
 * Consumers that attest source digests must not reconstruct text from JSON.
 */
export function readGameKnowledgeSource<T = any>(path: string, root = GAME_ROOT): { raw: string; value: T } {
  const raw = readFileSync(resolve(root, path), "utf8");
  return { raw, value: JSON.parse(raw) as T };
}

export function readGameKnowledge<T = any>(path: string, root = GAME_ROOT): T {
  return readGameKnowledgeSource<T>(path, root).value;
}
