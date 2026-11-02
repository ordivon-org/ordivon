import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import {
  buildMechanismRelationshipGraphFromSources,
  LIBRARY_PATH,
  SPEC_PATH,
} from "../src/mechanism-relationship-graph.ts";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const OUTPUT_PATH = "knowledge/game_mechanism_relationship_graph_r1.json";

function read(path: string): { raw: string; value: any } {
  const raw = readFileSync(resolve(ROOT, path), "utf8");
  return { raw, value: JSON.parse(raw) };
}

export function buildMechanismRelationshipGraph(): any {
  return buildMechanismRelationshipGraphFromSources(read(LIBRARY_PATH), read(SPEC_PATH));
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const graph = buildMechanismRelationshipGraph();
  writeFileSync(resolve(ROOT, OUTPUT_PATH), `${JSON.stringify(graph, null, 2)}\n`);
  process.stdout.write(`${JSON.stringify({ mechanisms: graph.mechanismNodes.length, edges: graph.withinExperienceEdges.length, facets: graph.retrievalFacets.length, conditionalities: graph.conditionalities.length }, null, 2)}\n`);
}
