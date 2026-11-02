/** Inspect source-backed Game composition examples without claiming installation.
 *
 * Explicitly does not install plugins, grant license, rank products or compile
 * game prototypes. Real game execution remains engine-native.
 */
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { readGameKnowledge } from "../src/knowledge-file.ts";
import { cliArgument } from "./cli-argument.ts";
import { normalizeQueryFilter } from "../src/query-input.ts";

type Source = { id: string; title: string; url: string; currentness: string };
type Slot = {
  role: string;
  sourceRef: string;
  integrationSeam: string;
  standing: "SOURCE_DOCUMENTED" | "EXECUTED_NATIVE";
  required: boolean;
};
type Recipe = {
  id: string;
  name: string;
  engine: "godot" | "bevy";
  intent: string;
  standing: "NATIVE_SUBSET_EXECUTED" | "NATIVE_SOURCE_COMPILED" | "DESIGN_CANDIDATE";
  currentConsumer?: string;
  components: Slot[];
  explicitGaps: string[];
  nextFalsifier: string;
};
type Plan = { recipes: Recipe[] };
type Index = { sources: Source[] };

export function queryPrototypeCompositions(options: { id?: string; engine?: string } = {}) {
  const plan = readGameKnowledge<Plan>("planning/prototype-composition-candidates-r1.json");
  const index = readGameKnowledge<Index>("knowledge/game_external_knowledge_base_r1.json");
  const byId = new Map(index.sources.map((source) => [source.id, source]));
  const requestedId = normalizeQueryFilter(options.id);
  const requestedEngine = normalizeQueryFilter(options.engine);
  const items = plan.recipes.filter((recipe) =>
    (!requestedId || recipe.id.toLowerCase() === requestedId) &&
    (!requestedEngine || recipe.engine.toLowerCase() === requestedEngine)
  ).map((recipe) => ({
    ...recipe,
    components: recipe.components.map((component) => {
      const source = byId.get(component.sourceRef);
      if (!source) throw new Error(`${recipe.id}: unknown source reference ${component.sourceRef}`);
      if (recipe.engine === "bevy" && /^(godot-|limboai-|dialogic2-)/.test(source.id))
        throw new Error(`${recipe.id}: Godot-only provider cannot be native Bevy plugin: ${source.id}`);
      if (recipe.engine === "godot" && /^bevy-/.test(source.id))
        throw new Error(`${recipe.id}: Bevy-only provider cannot be native Godot addon: ${source.id}`);
      return { ...component, provider: { title: source.title, url: source.url, currentness: source.currentness } };
    }),
  }));
  return {
    schemaVersion: 1 as const,
    kind: "ordivon.game.prototype-composition-query" as const,
    query: options,
    items,
    verifiedGameProducts: 0,
    notes: [
      "Documented upstream capability is not evidence of installation, compatibility or a successful game build.",
      "Only the existing native Godot composition fixture has EXECUTED_NATIVE standing.",
      "Provider source licensing does not automatically license user-made game assets or third-party samples.",
    ],
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  const id = cliArgument("--id");
  const engine = cliArgument("--engine");
  process.stdout.write(JSON.stringify(queryPrototypeCompositions({
    ...(id === undefined ? {} : { id }),
    ...(engine === undefined ? {} : { engine }),
  }), null, 2) + "\n");
}
