/** Process argument parsing owned by Game CLI entrypoints, not pure query policy. */
export function cliArgument(name: string, argv: readonly string[] = process.argv): string | undefined {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : undefined;
}

/** Assemble only supplied CLI fields; each query still owns its domain semantics.
 *
 * Preserve legacy first-occurrence, missing-value, Number() and --limit rules.
 * This is a narrow CLI adapter, not a new query language or registry.
 */
export function cliQueryArguments<const K extends string>(
  stringFields: readonly K[],
  argv: readonly string[] = process.argv,
): Partial<Record<K, string>> & { limit?: number } {
  const query: Partial<Record<K, string>> = {};
  for (const field of stringFields) {
    const value = cliArgument(`--${field}`, argv);
    if (value !== undefined) query[field] = value;
  }
  const result: Partial<Record<K, string>> & { limit?: number } = query;
  const rawLimit = cliArgument("--limit", argv);
  if (rawLimit !== undefined) result.limit = Number(rawLimit);
  return result;
}
