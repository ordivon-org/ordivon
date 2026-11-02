/** File/CLI adapter for the pure source-bound composition projection.
 * No engine installation, new registry or external side effect.
 */
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { readGameKnowledge } from "../src/knowledge-file.ts";
import {
  projectPrototypeCompositions,
  type CompositionQuery,
  type CompositionPlan,
  type CompositionSourceIndex,
} from "../src/prototype-composition.ts";
import { cliArgument } from "./cli-argument.ts";

export function queryPrototypeCompositions(options: CompositionQuery = {}) {
  return projectPrototypeCompositions(
    readGameKnowledge<CompositionPlan>("planning/prototype-composition-candidates-r1.json"),
    readGameKnowledge<CompositionSourceIndex>("knowledge/game_external_knowledge_base_r1.json"),
    options,
  );
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const id = cliArgument("--id");
  const engine = cliArgument("--engine");
  process.stdout.write(JSON.stringify(queryPrototypeCompositions({
    ...(id === undefined ? {} : { id }),
    ...(engine === undefined ? {} : { engine }),
  }), null, 2) + "\n");
}
