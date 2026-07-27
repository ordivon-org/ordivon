import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { canonicalJson, sha256 } from "../digest.ts";
import { runProcess } from "../providers/process.ts";
import { ProviderAdapterError } from "../providers/types.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "./model.ts";
import { parseTeamProviderDecision, type TeamDecisionProvider } from "./providers.ts";

export interface TeamCodexCliProviderOptions {
  executable?: string;
  model?: string;
  timeoutMs?: number;
  environment?: NodeJS.ProcessEnv;
}

export class TeamCodexCliProvider implements TeamDecisionProvider {
  readonly providerId: string;
  readonly executable: string;
  readonly model: string | null;
  readonly timeoutMs: number;
  readonly environment: NodeJS.ProcessEnv;
  private lastEvidence: Record<string, unknown> | null = null;

  constructor(options: TeamCodexCliProviderOptions = {}) {
    this.executable = options.executable ?? "/usr/bin/codex";
    this.model = options.model ?? null;
    this.timeoutMs = options.timeoutMs ?? 120_000;
    this.environment = options.environment ?? process.env;
    this.providerId = `codex-team-cli-ephemeral-v1:${this.model ?? "configured"}`;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.lastEvidence ? { ...this.lastEvidence } : null;
  }

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    const root = mkdtempSync(join(tmpdir(), "ordivon-game-team-codex-"));
    const work = join(root, "work");
    mkdirSync(work);
    try {
      const schemaPath = join(root, "team-decision.schema.json");
      const outputPath = join(root, "team-decision.json");
      writeFileSync(schemaPath, JSON.stringify({
        type: "object",
        additionalProperties: false,
        required: ["contextId", "selectedActionCandidateId", "confidence", "rationale"],
        properties: {
          contextId: { type: "string" },
          selectedActionCandidateId: { type: ["string", "null"] },
          confidence: { type: "number", minimum: 0, maximum: 1 },
          rationale: { type: "string", minLength: 1 },
        },
      }, null, 2) + "\n");
      const prompt = [
        "You are one replaceable specialist cognition turn inside a persistent multi-Agent Station Zero Host.",
        `Your actor identity is ${context.actorId}. Use only the canonical Team Context below.`,
        "Choose at most one allowed Action by copying its actionCandidateId and the contextId exactly.",
        "Do not infer hidden rooms, undelivered messages, other actors' private observations, authority grants, or world outcomes.",
        "Do not invent commands, targets, facts, completion claims, or another action. Return JSON only.",
        "",
        canonicalJson(context),
      ].join("\n");
      const args = [
        "exec", "--ephemeral", "--sandbox", "read-only", "--skip-git-repo-check",
        "--ignore-user-config", "--ignore-rules", "--output-schema", schemaPath,
        "--output-last-message", outputPath, "--json", "--color", "never", "-C", work,
      ];
      if (this.model) args.push("--model", this.model);
      args.push("-");
      const result = await runProcess(this.executable, args, {
        cwd: work,
        env: { ...this.environment, NO_COLOR: "1" },
        input: prompt,
        timeoutMs: this.timeoutMs,
      });
      if (result.exitCode !== 0) {
        throw new ProviderAdapterError("process_failed", `Team Codex exited ${result.exitCode}: ${result.stderr.trim().slice(-2_000)}`);
      }
      let value: unknown;
      try { value = JSON.parse(readFileSync(outputPath, "utf8")); }
      catch (error) { throw new ProviderAdapterError("invalid_output", "Team Codex did not write valid structured output", { cause: error }); }
      const decision = parseTeamProviderDecision(context, value, this.providerId);
      const events = result.stdout.split(/\r?\n/).filter(Boolean).flatMap((line) => {
        try { return [JSON.parse(line) as Record<string, unknown>]; }
        catch { return []; }
      });
      const completed = [...events].reverse().find((event) => event.type === "turn.completed");
      const usage = completed?.usage && typeof completed.usage === "object"
        ? completed.usage as Record<string, unknown>
        : null;
      this.lastEvidence = {
        adapterId: this.providerId,
        actorId: context.actorId,
        model: this.model,
        elapsedMs: Number(result.elapsedMs.toFixed(3)),
        inputTokens: usage ? Number(usage.input_tokens ?? 0) : null,
        cachedInputTokens: usage ? Number(usage.cached_input_tokens ?? 0) : null,
        outputTokens: usage ? Number(usage.output_tokens ?? 0) : null,
        ephemeral: true,
        sandbox: "read-only",
        isolatedWorkingDirectory: true,
        persistentSessionRetained: false,
        stdoutDigest: sha256(result.stdout),
        stderrDigest: sha256(result.stderr),
      };
      return decision;
    } finally {
      rmSync(root, { recursive: true, force: true });
    }
  }
}
