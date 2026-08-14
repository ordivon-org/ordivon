import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const study = readFileSync(new URL("../docs/CROSS_PROJECT_SELF_LOOP_STUDY.md", import.meta.url), "utf8");
const readme = readFileSync(new URL("../README.md", import.meta.url), "utf8");
const authority = readFileSync(new URL("../docs/authority.md", import.meta.url), "utf8");
const agents = readFileSync(new URL("../AGENTS.md", import.meta.url), "utf8");
const project = readFileSync(new URL("../.ordivon/project.yaml", import.meta.url), "utf8");

test("cross-project study is revision-bound research rather than a new authority plane", () => {
  assert.match(study, /^id: game\.research\.cross-project-self-loop-study$/m);
  assert.match(study, /not a new Ordivon architecture, service, protocol, controller, or source of truth/);
  assert.match(study, /revision-bound observation/);
  for (const revision of [
    "761bfe8dd7ca7c5e3e514891657c986eecb204e5",
    "507589eb1ae602f788913c7a8fdfd7bad355fe6c",
    "bb9f636cc4b533895254c0caf3e90eb083ca9e50",
    "d36fa9e8764c89dd9c51dbef2727ebb13e7a9e27",
    "c96ba2cc73b651097443a38ff7a2431801efd217",
    "c640e5af80727c7f7f35919257642776a8cdce10",
    "ad313efe289d36660e6643934ed5e3a586e5fab3",
    "2aba805e6ffe6c64ce0e0ebafce4240b61ef26a3",
    "f3a3ff13077961620c8fb965506557e8947a6ecb",
    "8dde4a411c71b062a0b5765dc6534d445a9ed6db",
    "f7725dfc9b391c3e9a0c509d49795994931c9d63",
    "430ed2f77a18d925963de8a8cb1e6f32142655d7",
  ]) assert.match(study, new RegExp(revision));
});

test("Game contraction claims remain hypotheses with explicit keep/delete-pressure classes", () => {
  for (const label of ["KEEP", "PROVEN RESIDUE", "DELETION EXPERIMENT REQUIRED", "OWNERSHIP PRESSURE"]) {
    assert.match(study, new RegExp(label));
  }
  assert.match(study, /research hypotheses\*\*, not deletion authorization/);
  assert.match(study, /Optional Agent Action Admission — PROVEN RESIDUE/);
  assert.match(study, /Embedded Host for every v3 Turn — DELETION EXPERIMENT REQUIRED/);
  assert.match(study, /DeepSeek credential\/pool plumbing — OWNERSHIP PRESSURE/);
  assert.match(study, /Selected Plan Preview/);
});

test("repository navigation routes the study without promoting it to product authority", () => {
  for (const source of [readme, authority, agents, project]) assert.match(source, /CROSS_PROJECT_SELF_LOOP_STUDY\.md/);
  assert.match(authority, /owns only Game's revision-bound research synthesis/);
  assert.match(authority, /every proposed Game contraction still requires owner-local falsification/);
  assert.match(agents, /does not authorize deletion without Game-local experiments/);
});
