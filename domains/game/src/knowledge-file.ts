/** Source-bound Game knowledge files, shared by existing read-only queries.
 *
 * This is a filesystem read operation, not a Game standard, registry, ranking
 * authority, or new store. The JSON fixtures remain owned by the Game domain.
 */
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const GAME_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");

export function readGameKnowledge<T = any>(path: string, root = GAME_ROOT): T {
  return JSON.parse(readFileSync(resolve(root, path), "utf8")) as T;
}
