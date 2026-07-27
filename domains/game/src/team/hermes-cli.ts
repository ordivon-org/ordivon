import { chmodSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

import { canonicalJson, sha256 } from "../digest.ts";
import { runProcess } from "../providers/process.ts";
import { ProviderAdapterError } from "../providers/types.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "./model.ts";
import { parseTeamProviderDecision, type TeamDecisionProvider } from "./providers.ts";

export interface TeamHermesCliProviderOptions {
  executable?: string;
  model?: string;
  provider?: string;
  baseUrl?: string;
  credentialEnvPath?: string;
  timeoutMs?: number;
  environment?: NodeJS.ProcessEnv;
}

export class TeamHermesCliProvider implements TeamDecisionProvider {
  readonly providerId: string;
  readonly executable: string;
  readonly model: string;
  readonly provider: string;
  readonly baseUrl: string;
  readonly credentialEnvPath: string;
  readonly timeoutMs: number;
  readonly environment: NodeJS.ProcessEnv;
  private lastEvidence: Record<string, unknown> | null = null;

  constructor(options: TeamHermesCliProviderOptions = {}) {
    this.executable = options.executable ?? "/root/.local/bin/hermes";
    this.model = options.model ?? "deepseek-v4-pro";
    this.provider = options.provider ?? "deepseek";
    this.baseUrl = (options.baseUrl ?? "https://api.deepseek.com").replace(/\/$/, "");
    this.credentialEnvPath = options.credentialEnvPath ?? join(homedir(), ".hermes", ".env");
    this.timeoutMs = options.timeoutMs ?? 180_000;
    this.environment = options.environment ?? process.env;
    for (const [label, value] of [["model", this.model], ["provider", this.provider], ["base URL", this.baseUrl]]) {
      if (!value || value !== value.trim() || value.includes("\n")) throw new TypeError(`Team Hermes ${label} must be non-empty and single-line`);
    }
    this.providerId = `hermes-team-cli-isolated-v1:${this.provider}/${this.model}`;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.lastEvidence ? { ...this.lastEvidence } : null;
  }

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    const root = mkdtempSync(join(tmpdir(), "ordivon-game-team-hermes-"));
    const home = join(root, "home");
    const hermesHome = join(root, "hermes");
    const work = join(root, "work");
    mkdirSync(home);
    mkdirSync(hermesHome);
    mkdirSync(work);
    try {
      this.writeCredentials(join(hermesHome, ".env"));
      this.writeConfig(join(hermesHome, "config.yaml"));
      writeFileSync(join(hermesHome, ".no-bundled-skills"), "");
      const usagePath = join(root, "usage.json");
      const prompt = [
        "You are one replaceable specialist cognition turn inside a persistent multi-Agent Station Zero Host.",
        `Your actor identity is ${context.actorId}. Use only the canonical Team Context below.`,
        "Choose at most one allowed Action by copying its actionCandidateId and the contextId exactly.",
        "Return exactly one JSON object with contextId as a string, selectedActionCandidateId as a string or null, confidence as a JSON number from 0 to 1, and rationale as a non-empty string.",
        "Do not infer hidden rooms, undelivered messages, other actors' private observations, authority grants, or world outcomes.",
        "Do not call tools or use memory, rules, skills, MCP, prior sessions, or markdown.",
        "",
        canonicalJson(context),
      ].join("\n");
      const env: NodeJS.ProcessEnv = { ...this.environment, HOME: home, HERMES_HOME: hermesHome, NO_COLOR: "1" };
      for (const name of ["HERMES_INFERENCE_MODEL", "HERMES_INFERENCE_PROVIDER", "HERMES_IGNORE_USER_CONFIG", "HERMES_SAFE_MODE"]) delete env[name];
      const result = await runProcess(this.executable, [
        "--oneshot", prompt, "--model", this.model, "--provider", this.provider,
        "--ignore-rules", "--usage-file", usagePath,
      ], { cwd: work, env, timeoutMs: this.timeoutMs });
      if (result.exitCode !== 0) {
        throw new ProviderAdapterError("process_failed", `Team Hermes exited ${result.exitCode}: ${result.stderr.trim().slice(-2_000)}`);
      }
      let value: unknown;
      let usage: Record<string, unknown>;
      try {
        value = JSON.parse(result.stdout);
        usage = JSON.parse(readFileSync(usagePath, "utf8")) as Record<string, unknown>;
      } catch (error) {
        throw new ProviderAdapterError("invalid_output", "Team Hermes returned invalid Decision or usage JSON", { cause: error });
      }
      this.validateUsage(usage);
      const decision = parseTeamProviderDecision(context, value, this.providerId);
      this.lastEvidence = {
        adapterId: this.providerId,
        actorId: context.actorId,
        model: this.model,
        provider: this.provider,
        baseUrl: this.baseUrl,
        elapsedMs: Number(result.elapsedMs.toFixed(3)),
        apiCalls: Number(usage.api_calls ?? 0),
        inputTokens: Number(usage.input_tokens ?? 0),
        outputTokens: Number(usage.output_tokens ?? 0),
        reasoningTokens: Number(usage.reasoning_tokens ?? 0),
        totalTokens: Number(usage.total_tokens ?? 0),
        estimatedCostUsd: usage.estimated_cost_usd ?? null,
        isolatedHome: true,
        enabledToolsets: [],
        memoryLoaded: false,
        persistentSessionRetained: false,
        stdoutDigest: sha256(result.stdout),
      };
      return decision;
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  }

  private writeCredentials(destination: string): void {
    let lines: string[];
    try { lines = readFileSync(this.credentialEnvPath, "utf8").split(/\r?\n/); }
    catch (error) { throw new ProviderAdapterError("unavailable", "Team Hermes credential environment file is unavailable", { cause: error }); }
    const prefix = this.provider.toUpperCase().replaceAll("-", "_");
    const keyName = `${prefix}_API_KEY`;
    const keyLines = lines.filter((line) => line.startsWith(`${keyName}=`) && line.slice(keyName.length + 1));
    if (keyLines.length === 0) throw new ProviderAdapterError("unavailable", `Team Hermes credential file has no ${keyName}`);
    writeFileSync(destination, `${keyLines.at(-1)}\n${prefix}_BASE_URL=${this.baseUrl}\n`);
    chmodSync(destination, 0o600);
  }

  private writeConfig(destination: string): void {
    writeFileSync(destination, [
      "model:", `  default: ${JSON.stringify(this.model)}`, `  provider: ${JSON.stringify(this.provider)}`,
      `  base_url: ${JSON.stringify(this.baseUrl)}`, "platform_toolsets:", "  cli: []", "mcp_servers: {}",
      "memory:", "  memory_enabled: false", "  user_profile_enabled: false", "  nudge_interval: 0",
      "  flush_min_turns: 999999", "skills:", "  creation_nudge_interval: 999999",
      "sessions:", "  write_json_snapshots: false", "",
    ].join("\n"));
    chmodSync(destination, 0o600);
  }

  private validateUsage(usage: Record<string, unknown>): void {
    if (usage.model !== this.model || usage.provider !== this.provider) {
      throw new ProviderAdapterError("invalid_usage", "Team Hermes used another model or provider");
    }
    if (usage.completed !== true || usage.failed !== false || Number(usage.api_calls ?? 0) < 1) {
      throw new ProviderAdapterError("invalid_usage", "Team Hermes usage reports an incomplete or non-model invocation");
    }
  }
}
