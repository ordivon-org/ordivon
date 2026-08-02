import { sha256 } from "./digest.ts";

export const CURRENT_BUILD = "ordivon-game@0.1.0-alpha.1";
export const CURRENT_INPUTS_DIGEST = sha256({
  kind: "ordivon.game.executable-inputs",
  build: CURRENT_BUILD,
  scenario: "station-zero@2",
  ruleset: "station-zero-core@3",
});
