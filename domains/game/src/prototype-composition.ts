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
  /** Explicit native compatibility for engine-bound sources; omitted means unclassified. */
  nativeEngines?: readonly ("godot" | "bevy")[];
};

export type CompositionSlot = {
  role: string;
  sourceRef: string;
  integrationSeam: string;
  standing: "SOURCE_DOCUMENTED" | "EXECUTED_NATIVE";
  required: boolean;
  /** Direct native reader for an executed slot within an advisory recipe. */
  currentConsumer?: string;
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

  // This is a structural consistency check, NOT execution proof.
  // Real effects remain owned by the named native consumer and its tests.
  const ids = new Set<string>();
  for (const recipe of plan.recipes) {
    if (ids.has(recipe.id)) throw new Error(`duplicate Game composition ${recipe.id}`);
    ids.add(recipe.id);
    if (recipe.standing !== "DESIGN_CANDIDATE" && !recipe.currentConsumer)
      throw new Error(`${recipe.id}: non-candidate composition missing named consumer`);
    if ((recipe.standing === "NATIVE_SUBSET_EXECUTED" || recipe.standing === "NATIVE_COMPONENT_EXECUTED")
        && !recipe.components.some((item) => item.standing === "EXECUTED_NATIVE"))
      throw new Error(`${recipe.id}: native execution standing without an executed component`);
    for (const component of recipe.components) {
      if (component.standing === "EXECUTED_NATIVE" &&
          recipe.standing === "DESIGN_CANDIDATE" && !component.currentConsumer?.trim())
        throw new Error(`${recipe.id}: executed candidate slot missing scoped consumer`);
    }
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
      // An identifier is not an interface contract: renaming a provider
      // must never change its native compatibility.
      if (source.nativeEngines && !source.nativeEngines.includes(recipe.engine))
        throw new Error(recipe.id + ": provider " + source.id + " supports " + source.nativeEngines.join(", ") + ", not " + recipe.engine);
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
