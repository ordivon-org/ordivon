/** Pure filter and limit policy shared by Game's read-only queries.
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
