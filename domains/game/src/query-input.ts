/** Pure input policy shared by Game's five read-only knowledge query entrypoints.
 *
 * Keep each query's own dataset, matching semantics, and maximum-result cap local.
 * This is not a new query engine, a ranking authority, or a public API.
 */
export function normalizeQueryFilter(value?: string): string | undefined {
  const result = value?.trim().toLowerCase();
  return result || undefined;
}

export function boundedQueryLimit(limit: number | undefined, maximum: number): number {
  return Number.isInteger(limit) && (limit ?? 0) > 0 ? Math.min(limit!, maximum) : 50;
}

export function cliArgument(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}
