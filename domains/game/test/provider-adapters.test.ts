import assert from "node:assert/strict";
import { chmodSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import { compileAgentContext, type CompiledAgentContext } from "../src/host/context.ts";
import { initialAgentProjection } from "../src/host/model.ts";
import { CodexCliProvider } from "../src/providers/codex-cli.ts";
import { ProviderChain } from "../src/providers/chain.ts";
import { RecoveryOperationProvider } from "../src/providers/fixture.ts";
import { HermesCliProvider } from "../src/providers/hermes-cli.ts";
import { runProcess } from "../src/providers/process.ts";
import {
  parseModelDecisionOutput,
  ProviderAdapterError,
  type OperationDecision,
  type OperationProvider,
} from "../src/providers/types.ts";
import { GameStore } from "../src/storage.ts";

function fixtureContext(): { directory: string; game: GameStore; context: CompiledAgentContext } {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-game-provider-test-"));
  const game = new GameStore(join(directory, "world.sqlite3"));
  const projection = initialAgentProjection(game.activeRunId, game.loadState().mission.status);
  return { directory, game, context: compileAgentContext(game.getRun(), game.loadState(), projection) };
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
if (mode === 'sleep') return setTimeout(() => {}, 10000);
if (mode === 'nonzero') { console.error('fake failure'); process.exit(9); }
if (mode === 'huge') { console.log('x'.repeat(10000)); process.exit(0); }
if (args[0] === 'exec') {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', chunk => input += chunk);
  process.stdin.on('end', () => {
    const context = contextFrom(input);
    const selected = context.allowedOperations[0]?.operationCandidateId ?? null;
    const output = mode === 'invalid-json' ? '{' : JSON.stringify({
      contextId: mode === 'wrong-context' ? 'wrong' : context.contextId,
      selectedOperationCandidateId: mode === 'invented' ? 'operation:invented' : selected,
      riskLevel: 'medium', confidence: 0.8, rationale: 'Choose one admitted operation.'
    });
    fs.writeFileSync(value('--output-last-message'), output);
    if (process.env.CAPTURE_PATH) fs.writeFileSync(process.env.CAPTURE_PATH, JSON.stringify({ args, cwd: process.cwd(), input }));
    console.log(JSON.stringify({ type: 'turn.completed', usage: { input_tokens: 10, output_tokens: 5 } }));
  });
} else {
  const prompt = value('--oneshot');
  const context = contextFrom(prompt);
  const selected = context.allowedOperations[0]?.operationCandidateId ?? null;
  const usage = {
    model: process.env.FAKE_USAGE_MODEL || value('--model'),
    provider: process.env.FAKE_USAGE_PROVIDER || value('--provider'),
    completed: mode !== 'incomplete', failed: mode === 'incomplete', api_calls: mode === 'no-api' ? 0 : 1,
    input_tokens: 100, output_tokens: 20, reasoning_tokens: 5, total_tokens: 120, estimated_cost_usd: 0.001
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
    selectedOperationCandidateId: mode === 'invented' ? 'operation:invented' : selected,
    riskLevel: 'medium', confidence: 0.9, rationale: 'Choose one admitted operation.'
  }));
}
`;

test("Codex adapter uses ephemeral read-only structured invocation and removes its workspace", async () => {
  const fixture = fixtureContext();
  try {
    const fake = executable(fixture.directory, "fake-codex", sharedFake);
    const capturePath = join(fixture.directory, "codex-capture.json");
    const provider = new CodexCliProvider({
      executable: fake,
      model: "gpt-test",
      environment: { ...process.env, CAPTURE_PATH: capturePath },
      timeoutMs: 2_000,
    });
    const decision = await provider.decide(fixture.context);
    assert.equal(decision.providerId, "codex-cli-ephemeral-v1:gpt-test");
    assert.equal(decision.contextId, fixture.context.contextId);
    assert.ok(fixture.context.payload.allowedOperations.some((item) => item.operationCandidateId === decision.selectedOperationCandidateId));
    const capture = JSON.parse(readFileSync(capturePath, "utf8")) as { args: string[]; cwd: string; input: string };
    assert.ok(capture.args.includes("--ephemeral"));
    assert.ok(capture.args.includes("read-only"));
    assert.ok(capture.args.includes("--ignore-user-config"));
    assert.ok(capture.args.includes("--ignore-rules"));
    assert.match(capture.input, /Never invent Commands/);
    assert.equal(existsSync(capture.cwd), false);
    assert.equal(provider.evidenceMetadata()?.persistentSessionRetained, false);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("Hermes adapter creates an isolated no-tool no-memory profile and records usage", async () => {
  const fixture = fixtureContext();
  try {
    const fake = executable(fixture.directory, "fake-hermes", sharedFake);
    const capturePath = join(fixture.directory, "hermes-capture.json");
    const credentials = join(fixture.directory, "credentials.env");
    writeFileSync(credentials, "DEEPSEEK_API_KEY=test-secret\nOTHER_SECRET=do-not-copy\n");
    const provider = new HermesCliProvider({
      executable: fake,
      model: "deepseek-v4-pro",
      provider: "deepseek",
      credentialEnvPath: credentials,
      environment: { ...process.env, CAPTURE_PATH: capturePath },
      timeoutMs: 2_000,
    });
    const decision = await provider.decide(fixture.context);
    assert.equal(decision.providerId, "hermes-cli-isolated-v1:deepseek/deepseek-v4-pro");
    const capture = JSON.parse(readFileSync(capturePath, "utf8")) as {
      args: string[]; home: string; hermesHome: string; config: string; credentials: string; prompt: string;
    };
    assert.match(capture.config, /cli: \[\]/);
    assert.match(capture.config, /mcp_servers: \{\}/);
    assert.match(capture.config, /memory_enabled: false/);
    assert.doesNotMatch(capture.credentials, /OTHER_SECRET/);
    assert.match(capture.credentials, /DEEPSEEK_API_KEY=test-secret/);
    assert.equal(existsSync(capture.home), false);
    assert.equal(existsSync(capture.hermesHome), false);
    const evidence = provider.evidenceMetadata();
    assert.equal(evidence?.apiCalls, 1);
    assert.equal(evidence?.totalTokens, 120);
    assert.deepEqual(evidence?.enabledToolsets, []);
    assert.equal(evidence?.memoryLoaded, false);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("CLI adapters fail closed on process, output, credentials, and usage errors", async () => {
  const fixture = fixtureContext();
  try {
    const fake = executable(fixture.directory, "fake-provider", sharedFake);
    for (const mode of ["nonzero", "invalid-json", "wrong-context", "invented"] as const) {
      const codex = new CodexCliProvider({ executable: fake, environment: { ...process.env, FAKE_MODE: mode }, timeoutMs: 2_000 });
      await assert.rejects(() => codex.decide(fixture.context), ProviderAdapterError);
    }
    const missing = new HermesCliProvider({ executable: fake, credentialEnvPath: join(fixture.directory, "missing") });
    await assert.rejects(
      () => missing.decide(fixture.context),
      (error) => error instanceof ProviderAdapterError && error.code === "unavailable",
    );
    const emptyCredentials = join(fixture.directory, "empty.env");
    writeFileSync(emptyCredentials, "DEEPSEEK_API_KEY=\n");
    await assert.rejects(
      () => new HermesCliProvider({ executable: fake, credentialEnvPath: emptyCredentials }).decide(fixture.context),
      ProviderAdapterError,
    );
    const credentials = join(fixture.directory, "ok.env");
    writeFileSync(credentials, "DEEPSEEK_API_KEY=test\n");
    for (const environment of [
      { FAKE_USAGE_MODEL: "wrong" },
      { FAKE_USAGE_PROVIDER: "wrong" },
      { FAKE_MODE: "incomplete" },
      { FAKE_MODE: "no-api" },
      { FAKE_MODE: "invalid-json" },
    ]) {
      const hermes = new HermesCliProvider({ executable: fake, credentialEnvPath: credentials, environment: { ...process.env, ...environment }, timeoutMs: 2_000 });
      await assert.rejects(() => hermes.decide(fixture.context), ProviderAdapterError);
    }
    assert.throws(() => new HermesCliProvider({ model: " " }), /non-empty/);
    assert.throws(() => new HermesCliProvider({ provider: "bad\nprovider" }), /single-line/);
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("process runner classifies timeout, output limit, unavailable executable, and exit code", async () => {
  const directory = mkdtempSync(join(tmpdir(), "ordivon-process-test-"));
  try {
    const fake = executable(directory, "fake-process", sharedFake);
    await assert.rejects(
      () => runProcess(fake, [], { cwd: directory, env: { ...process.env, FAKE_MODE: "sleep" }, timeoutMs: 20 }),
      (error) => error instanceof ProviderAdapterError && error.code === "timeout",
    );
    await assert.rejects(
      () => runProcess(fake, [], { cwd: directory, env: { ...process.env, FAKE_MODE: "huge" }, timeoutMs: 2_000, maximumOutputBytes: 10 }),
      (error) => error instanceof ProviderAdapterError && error.code === "process_failed",
    );
    await assert.rejects(
      () => runProcess(join(directory, "missing"), [], { cwd: directory, env: process.env, timeoutMs: 100 }),
      (error) => error instanceof ProviderAdapterError && error.code === "unavailable",
    );
    const failed = await runProcess(fake, [], { cwd: directory, env: { ...process.env, FAKE_MODE: "nonzero" }, timeoutMs: 2_000 });
    assert.equal(failed.exitCode, 9);
    assert.match(failed.stderr, /fake failure/);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

test("strict model output parser rejects shape, type, identity, and value drift", () => {
  const fixture = fixtureContext();
  try {
    const operation = fixture.context.payload.allowedOperations[0];
    assert.ok(operation);
    const valid = {
      contextId: fixture.context.contextId,
      selectedOperationCandidateId: operation.operationCandidateId,
      riskLevel: "low",
      confidence: 0.5,
      rationale: "Valid.",
    };
    assert.equal(parseModelDecisionOutput(fixture.context, valid, "test").providerId, "test");
    for (const invalid of [
      null,
      [],
      { ...valid, extra: true },
      { ...valid, confidence: "high" },
      { ...valid, riskLevel: "unknown" },
      { ...valid, contextId: "wrong" },
      { ...valid, selectedOperationCandidateId: "invented" },
      { ...valid, rationale: "" },
    ]) {
      assert.throws(
        () => parseModelDecisionOutput(fixture.context, invalid, "test"),
        (error) => error instanceof ProviderAdapterError && error.code === "invalid_output",
      );
    }
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});

test("Provider Chain falls back only after technical failure and retains attempt evidence", async () => {
  const fixture = fixtureContext();
  try {
    let secondCalls = 0;
    const failed: OperationProvider = {
      providerId: "failed-provider",
      async decide() { throw new ProviderAdapterError("process_failed", "failed"); },
    };
    const second = new RecoveryOperationProvider();
    const wrapped: OperationProvider = {
      providerId: second.providerId,
      async decide(context) { secondCalls += 1; return await second.decide(context); },
    };
    const chain = new ProviderChain([failed, wrapped]);
    const decision = await chain.decide(fixture.context);
    assert.equal(decision.providerId, wrapped.providerId);
    assert.equal(secondCalls, 1);
    assert.equal((chain.evidenceMetadata()?.attempts as unknown[]).length, 2);

    const firstSuccess: OperationProvider = {
      providerId: "first-success",
      async decide(context): Promise<OperationDecision> {
        return { providerId: "first-success", contextId: context.contextId,
          selectedOperationCandidateId: context.payload.allowedOperations[0]?.operationCandidateId ?? null,
          riskLevel: "low", confidence: 1, rationale: "first" };
      },
    };
    const noFallback = new ProviderChain([firstSuccess, wrapped]);
    await noFallback.decide(fixture.context);
    assert.equal(secondCalls, 1);
    assert.throws(() => new ProviderChain([]), /at least one/);
    await assert.rejects(
      () => new ProviderChain([failed]).decide(fixture.context),
      (error) => error instanceof ProviderAdapterError && error.code === "unavailable",
    );
  } finally {
    fixture.game.close();
    rmSync(fixture.directory, { recursive: true, force: true });
  }
});
