import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { ProviderAdapterError } from "../src/providers/types.ts";
import { ENGINEER_ID } from "../src/scenario.ts";
import { GameStore } from "../src/storage.ts";
import { TeamCodexCliProvider } from "../src/team/codex-cli.ts";
import { compileTeamContext } from "../src/team/context.ts";
import { TeamHermesCliProvider } from "../src/team/hermes-cli.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "../src/team/model.ts";
import { TeamProviderChain } from "../src/team/provider-chain.ts";
import { FixtureTeamProvider, type TeamDecisionProvider } from "../src/team/providers.ts";
import { actorTaskId, TeamStore } from "../src/team/store.ts";

function fixtureContext(): { directory: string; game: GameStore; context: CompiledTeamContext } {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-team-provider-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  game.createRun({ runId: "run:team-provider-adapter", scenarioVersion: 2, rulesetVersion: 3 });
  game.setActiveRun("run:team-provider-adapter");
  const team = new TeamStore(game);
  team.initialize();
  const context = compileTeamContext({
    store: game,
    runId: game.activeRunId,
    task: team.getTask(actorTaskId(game.activeRunId, ENGINEER_ID)),
    profile: team.getProfile(ENGINEER_ID),
    goal: team.getGoal(),
    messages: [],
    policyMode: "autonomous",
  });
  return { directory, game, context };
}

function executable(directory: string, name: string, source: string): string {
  const path = join(directory, name);
  writeFileSync(path, `#!/usr/bin/env node\n${source}`);
  chmodSync(path, 0o755);
  return path;
}

const sharedFake = String.raw`
const fs = require('node:fs');
const args = process.argv.slice(2);
function value(flag) { return args[args.indexOf(flag) + 1]; }
function contextFrom(text) { return JSON.parse(text.slice(text.lastIndexOf('\n') + 1)); }
const mode = process.env.FAKE_MODE || 'ok';
if (mode === 'nonzero') { console.error('fake failure'); process.exit(9); }
if (args[0] === 'exec') {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    const context = contextFrom(input);
    const selected = context.allowedActions[0]?.actionCandidateId ?? null;
    const output = mode === 'invalid-json' ? '{' : JSON.stringify({
      contextId: mode === 'wrong-context' ? 'wrong' : context.contextId,
      selectedActionCandidateId: mode === 'invented' ? 'team-action:invented' : selected,
      confidence: 0.8, rationale: 'Choose one admitted specialist action.'
    });
    fs.writeFileSync(value('--output-last-message'), output);
    if (process.env.CAPTURE_PATH) fs.writeFileSync(process.env.CAPTURE_PATH, JSON.stringify({ args, cwd: process.cwd(), input }));
    console.log(JSON.stringify({ type: 'turn.completed', usage: { input_tokens: 11, cached_input_tokens: 2, output_tokens: 6 } }));
  });
} else {
  const prompt = value('--oneshot');
  const context = contextFrom(prompt);
  const selected = context.allowedActions[0]?.actionCandidateId ?? null;
  const usage = {
    model: process.env.FAKE_USAGE_MODEL || value('--model'),
    provider: process.env.FAKE_USAGE_PROVIDER || value('--provider'),
    completed: mode !== 'incomplete', failed: mode === 'incomplete', api_calls: mode === 'no-api' ? 0 : 1,
    input_tokens: 101, output_tokens: 21, reasoning_tokens: 7, total_tokens: 129, estimated_cost_usd: 0.002
  };
  fs.writeFileSync(value('--usage-file'), JSON.stringify(usage));
  if (process.env.CAPTURE_PATH) {
    const h = process.env.HERMES_HOME;
    fs.writeFileSync(process.env.CAPTURE_PATH, JSON.stringify({
      args, cwd: process.cwd(), home: process.env.HOME, hermesHome: h,
      config: fs.readFileSync(h + '/config.yaml', 'utf8'), credentials: fs.readFileSync(h + '/.env', 'utf8'), prompt
    }));
  }
  if (mode === 'invalid-json') process.stdout.write('{');
  else process.stdout.write(JSON.stringify({
    contextId: mode === 'wrong-context' ? 'wrong' : context.contextId,
    selectedActionCandidateId: mode === 'invented' ? 'team-action:invented' : selected,
    confidence: 0.9, rationale: 'Choose one admitted specialist action.'
  }));
}
`;

test("Team Codex adapter is ephemeral, read-only, structured, and actor-scoped", async () => {
  const fixture = fixtureContext();
  try {
    const fake = executable(fixture.directory, "fake-team-codex", sharedFake);
    const capturePath = join(fixture.directory, "team-codex-capture.json");
    const provider = new TeamCodexCliProvider({
      executable: fake,
      model: "gpt-team-test",
      environment: { ...process.env, CAPTURE_PATH: capturePath },
      timeoutMs: 2_000,
    });
    const decision = await provider.decide(fixture.context);
    assert.equal(decision.providerId, "codex-team-cli-ephemeral-v1:gpt-team-test");
    assert.equal(decision.contextId, fixture.context.contextId);
    assert.ok(fixture.context.allowedActions.some((candidate) => candidate.actionCandidateId === decision.selectedActionCandidateId));
    const capture = JSON.parse(readFileSync(capturePath, "utf8")) as { args: string[]; cwd: string; input: string };
    assert.ok(capture.args.includes("--ephemeral"));
    assert.ok(capture.args.includes("read-only"));
    assert.ok(capture.args.includes("--ignore-user-config"));
    assert.ok(capture.args.includes("--ignore-rules"));
    assert.match(capture.input, /Do not infer hidden rooms/);
    assert.match(capture.input, new RegExp(fixture.context.actorId));
    assert.equal(existsSync(capture.cwd), false);
    const evidence = provider.evidenceMetadata();
    assert.equal(evidence?.actorId, ENGINEER_ID);
    assert.equal(evidence?.inputTokens, 11);
    assert.equal(evidence?.cachedInputTokens, 2);
    assert.equal(evidence?.outputTokens, 6);
    assert.equal(evidence?.persistentSessionRetained, false);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("Team Hermes adapter isolates credentials, tools, memory, and sessions", async () => {
  const fixture = fixtureContext();
  try {
    const fake = executable(fixture.directory, "fake-team-hermes", sharedFake);
    const capturePath = join(fixture.directory, "team-hermes-capture.json");
    const credentials = join(fixture.directory, "credentials.env");
    writeFileSync(credentials, "DEEPSEEK_API_KEY=test-secret\nOTHER_SECRET=do-not-copy\n");
    const provider = new TeamHermesCliProvider({
      executable: fake,
      model: "deepseek-v4-pro",
      provider: "deepseek",
      credentialEnvPath: credentials,
      environment: { ...process.env, CAPTURE_PATH: capturePath },
      timeoutMs: 2_000,
    });
    const decision = await provider.decide(fixture.context);
    assert.equal(decision.providerId, "hermes-team-cli-isolated-v1:deepseek/deepseek-v4-pro");
    const capture = JSON.parse(readFileSync(capturePath, "utf8")) as {
      args: string[]; home: string; hermesHome: string; config: string; credentials: string; prompt: string;
    };
    assert.match(capture.config, /cli: \[\]/);
    assert.match(capture.config, /mcp_servers: \{\}/);
    assert.match(capture.config, /memory_enabled: false/);
    assert.doesNotMatch(capture.credentials, /OTHER_SECRET/);
    assert.match(capture.credentials, /DEEPSEEK_API_KEY=test-secret/);
    assert.match(capture.prompt, /Do not infer hidden rooms/);
    assert.equal(existsSync(capture.home), false);
    assert.equal(existsSync(capture.hermesHome), false);
    const evidence = provider.evidenceMetadata();
    assert.equal(evidence?.actorId, ENGINEER_ID);
    assert.equal(evidence?.apiCalls, 1);
    assert.equal(evidence?.totalTokens, 129);
    assert.deepEqual(evidence?.enabledToolsets, []);
    assert.equal(evidence?.memoryLoaded, false);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("Team CLI adapters fail closed on process, output, credentials, and usage errors", async () => {
  const fixture = fixtureContext();
  try {
    const fake = executable(fixture.directory, "fake-team-provider", sharedFake);
    for (const mode of ["nonzero", "invalid-json", "wrong-context", "invented"] as const) {
      const codex = new TeamCodexCliProvider({ executable: fake, environment: { ...process.env, FAKE_MODE: mode }, timeoutMs: 2_000 });
      await assert.rejects(() => codex.decide(fixture.context), ProviderAdapterError);
    }
    const missing = new TeamHermesCliProvider({ executable: fake, credentialEnvPath: join(fixture.directory, "missing") });
    await assert.rejects(() => missing.decide(fixture.context), (error: unknown) => error instanceof ProviderAdapterError && error.code === "unavailable");
    const emptyCredentials = join(fixture.directory, "empty.env");
    writeFileSync(emptyCredentials, "DEEPSEEK_API_KEY=\n");
    await assert.rejects(() => new TeamHermesCliProvider({ executable: fake, credentialEnvPath: emptyCredentials }).decide(fixture.context), ProviderAdapterError);
    const credentials = join(fixture.directory, "ok.env");
    writeFileSync(credentials, "DEEPSEEK_API_KEY=test\n");
    for (const environment of [
      { FAKE_USAGE_MODEL: "wrong" },
      { FAKE_USAGE_PROVIDER: "wrong" },
      { FAKE_MODE: "incomplete" },
      { FAKE_MODE: "no-api" },
      { FAKE_MODE: "invalid-json" },
    ]) {
      const hermes = new TeamHermesCliProvider({ executable: fake, credentialEnvPath: credentials, environment: { ...process.env, ...environment }, timeoutMs: 2_000 });
      await assert.rejects(() => hermes.decide(fixture.context), ProviderAdapterError);
    }
    assert.throws(() => new TeamHermesCliProvider({ model: " " }), /non-empty/);
    assert.throws(() => new TeamHermesCliProvider({ provider: "bad\nprovider" }), /single-line/);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("Team Provider Chain falls back only after technical failure", async () => {
  const fixture = fixtureContext();
  try {
    let secondCalls = 0;
    const failed: TeamDecisionProvider = {
      providerId: "failed-team-provider",
      async decide() { throw new ProviderAdapterError("process_failed", "failed"); },
    };
    const fixtureProvider = new FixtureTeamProvider();
    const second: TeamDecisionProvider = {
      providerId: "second-team-provider",
      async decide(context): Promise<TeamProviderDecision> {
        secondCalls += 1;
        const decision = await fixtureProvider.decide(context);
        return { ...decision, providerId: "second-team-provider" };
      },
      evidenceMetadata() { return { secondCalls }; },
    };
    const chain = new TeamProviderChain([failed, second]);
    const decision = await chain.decide(fixture.context);
    assert.equal(decision.providerId, "second-team-provider");
    assert.equal(secondCalls, 1);
    assert.equal((chain.evidenceMetadata()?.attempts as unknown[]).length, 2);

    const firstSuccess = new TeamProviderChain([second, failed]);
    await firstSuccess.decide(fixture.context);
    assert.equal(secondCalls, 2);
    assert.throws(() => new TeamProviderChain([]), /at least one/);
    await assert.rejects(() => new TeamProviderChain([failed]).decide(fixture.context), (error: unknown) => error instanceof ProviderAdapterError && error.code === "unavailable");

    const unexpected: TeamDecisionProvider = {
      providerId: "unexpected",
      async decide() { throw new Error("programming error"); },
    };
    await assert.rejects(() => new TeamProviderChain([unexpected, second]).decide(fixture.context), /programming error/);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});
