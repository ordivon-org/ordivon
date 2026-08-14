import assert from "node:assert/strict";
import { existsSync, readFileSync, statSync } from "node:fs";
import test from "node:test";

const brief = readFileSync(new URL("../docs/STATION_ZERO_V3_VERTICAL_SLICE.md", import.meta.url), "utf8");
const render = readFileSync(new URL("../web-v3/render.js", import.meta.url), "utf8");
const app = readFileSync(new URL("../web-v3/app.js", import.meta.url), "utf8");
const styles = readFileSync(new URL("../web-v3/styles.css", import.meta.url), "utf8");
const atlas = JSON.parse(readFileSync(new URL("../assets/station-zero-v3/rescue-specialists.json", import.meta.url), "utf8"));

test("G4 brief keeps the slice on measured production claims rather than expanding product scope", () => {
  assert.match(brief, /Production Claim A — Mobile command proximity/);
  assert.match(brief, /Production Claim B — Specialist visual identity/);
  assert.match(brief, /Production Claim C — Live deliberation experience/);
  assert.match(brief, /Production Claim D — Representative audio/);
  assert.match(brief, /Commander Order begins before y=900/);
  assert.match(brief, /Godot, Blender, 3D conversion, campaign\/meta progression/);
});

test("specialist Studio source and runtime derivative retain exact three-Actor mapping", () => {
  const source = new URL("../assets/station-zero-v3/rescue-specialists.aseprite", import.meta.url);
  const recipe = new URL("../assets/station-zero-v3/generate-rescue-specialists.lua", import.meta.url);
  const runtime = new URL("../web-v3/assets/rescue-specialists.png", import.meta.url);
  assert.ok(existsSync(source));
  assert.ok(existsSync(recipe));
  assert.ok(existsSync(runtime));
  assert.ok(statSync(source).size > 0);
  assert.ok(statSync(runtime).size > 0);
  assert.deepEqual(Object.keys(atlas.frames).sort(), ["engineer-imani", "medic-reyes", "security-chen"]);
  assert.deepEqual(Object.values(atlas.frames).map((frame: any) => frame.x), [0, 24, 48]);
  assert.equal(atlas.sheet.width, 72);
  assert.equal(atlas.sheet.height, 24);
  assert.match(styles, /rescue-specialists\.png/);
  assert.match(render, /SPECIALIST_VISUALS/);
});

test("G4 audio keeps deterministic local source, mute state, and post-boundary cues", () => {
  const recipe = new URL("../assets/station-zero-v3/generate-g4-audio.sh", import.meta.url);
  assert.ok(existsSync(recipe));
  for (const cue of ["plan-ready", "commit", "aftermath"]) {
    const path = new URL(`../web-v3/assets/audio/${cue}.ogg`, import.meta.url);
    assert.ok(existsSync(path));
    assert.ok(statSync(path).size > 1000);
    assert.match(app, new RegExp(`${cue}\\.ogg`));
  }
  assert.match(app, /station-zero-v3-audio-muted/);
  assert.match(render, /data-action="toggle-audio"/);
  assert.match(app, /playCue\("plan-ready"\)/);
  assert.match(app, /playCue\("commit"\)/);
  assert.match(app, /playCue\("aftermath"\)/);
});

test("deliberation is a truthful presentation state and mobile CSS routes Command before full Situation", () => {
  assert.match(render, /World paused at Turn/);
  assert.match(render, /Enemy plans sealed/);
  assert.match(render, /no fake progress/);
  assert.match(app, /data-busy-elapsed/);
  assert.match(styles, /\.mission > \.planning-grid \{ order: 6; \}/);
  assert.match(styles, /\.mission > \.situation-grid \{ order: 7; \}/);
  assert.match(styles, /prefers-reduced-motion/);
  assert.match(styles, /\.deliberating, \.spinner \{ animation: none; \}/);
});
