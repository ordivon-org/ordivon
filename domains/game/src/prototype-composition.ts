/** Pure, source-grounded Game prototype composition projection.
 *
 * Provider documentation never proves installation or a playable game.
 * The result reflects explicitly supplied evidence states; native consumers
 * independently execute their own acceptance, and no global registry exists.
 */
import { normalizeQueryFilter } from "./query-input.ts";

export type CompositionSource = {
  id: string;
  title: string;
  url: string;
  currentness: string;
};

export type CompositionSlot = {
  role: string;
  sourceRef: string;
  integrationSeam: string;
  standing: "SOURCE_DOCUMENTED" | "EXECUTED_NATIVE";
  required: boolean;
};

export type CompositionRecipe = {
  id: string;
  name: string;
  engine: "godot" | "bevy";
  intent: string;
  standing:
    | "NATIVE_SUBSET_EXECUTED"
    | "NATIVE_COMPONENT_EXECUTED"
    | "NATIVE_SOURCE_COMPILED"
    | "DESIGN_CANDIDATE";
  currentConsumer?: string;
  components: CompositionSlot[];
  explicitGaps: string[];
  nextFalsifier: string;
};

export type CompositionPlan = { recipes: CompositionRecipe[] };
export type CompositionSourceIndex = { sources: CompositionSource[] };
export type CompositionQuery = { id?: string; engine?: string };

export function projectPrototypeCompositions(
  plan: CompositionPlan,
  index: CompositionSourceIndex,
  options: CompositionQuery = {},
) {
  const sources = new Map<string, CompositionSource>();
  for (const source of index.sources) {
    if (sources.has(source.id)) throw new Error(`duplicate Game source ${source.id}`);
    sources.set(source.id, source);
  }

  const requestedId = normalizeQueryFilter(options.id);
  const requestedEngine = normalizeQueryFilter(options.engine);
  const items = plan.recipes.filter((recipe) =>
    (!requestedId || recipe.id.toLowerCase() === requestedId) &&
    (!requestedEngine || recipe.engine.toLowerCase() === requestedEngine)
  ).map((recipe) => ({
    ...recipe,
    components: recipe.components.map((component) => {
      const source = sources.get(component.sourceRef);
      if (!source) throw new Error(`${recipe.id}: unknown source reference ${component.sourceRef}`);
      if (recipe.engine === "bevy" && /^(godot-|limboai-|dialogic2-)/.test(source.id))
        throw new Error(`${recipe.id}: Godot-only provider cannot be native Bevy plugin: ${source.id}`);
      if (recipe.engine === "godot" && /^bevy-/.test(source.id))
        throw new Error(`${recipe.id}: Bevy-only provider cannot be native Godot addon: ${source.id}`);
      return {
        ...component,
        provider: { title: source.title, url: source.url, currentness: source.currentness },
      };
    }),
  }));

  return {
    schemaVersion: 1 as const,
    kind: "ordivon.game.prototype-composition-query" as const,
    query: options,
    items,
    verifiedGameProducts: 0,
    notes: [
      "Upstream documentation does not establish plugin installation, release compatibility or shipped game behavior.",
      "NATIVE_SUBSET_EXECUTED is limited to the named Godot fixture; NATIVE_COMPONENT_EXECUTED proves only a component; NATIVE_SOURCE_COMPILED is not a human-played game.",
      "Provider source licenses do not automatically license third-party derivative works or all related media.",
    ],
  };
}
