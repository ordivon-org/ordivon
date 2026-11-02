/** Process argument parsing owned by Game CLI entrypoints, not pure query policy. */
export function cliArgument(name: string): string | undefined {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}
