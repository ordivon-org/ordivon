import { writeFileSync } from "node:fs";

import { listRulesetContracts, listScenarioContracts } from "../src/registry.ts";
import { createEvaluatedInputManifest } from "../src/release/inputs.ts";

const manifest = createEvaluatedInputManifest({
  scenarioContracts: listScenarioContracts(),
  rulesetContracts: listRulesetContracts(),
});
const outputIndex = process.argv.indexOf("--out");
if (outputIndex >= 0) {
  const path = process.argv[outputIndex + 1];
  if (!path?.trim()) throw new TypeError("--out requires a file path");
  writeFileSync(path, JSON.stringify(manifest, null, 2) + "\n");
}
console.log(JSON.stringify(manifest, null, 2));
