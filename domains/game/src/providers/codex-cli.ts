import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { canonicalJson, sha256 } from "../digest.ts";
import type { CompiledAgentContext } from "../host/context.ts";
import { parseModelDecisionOutput, ProviderAdapterError, type OperationDecision, type OperationProvider } from "./types.ts";
import { runProcess } from "./process.ts";

export interface CodexCliProviderOptions {
  executable?: string;
  model?: string;
  timeoutMs?: number;
  environment?: NodeJS.ProcessEnv;
}

export class CodexCliProvider implements OperationProvider {
  readonly providerId: string;
  readonly executable: string;
  readonly model: string | null;
  readonly timeoutMs: number;
  readonly environment: NodeJS.ProcessEnv;
  private lastEvidence: Record<string, unknown> | null = null;

  constructor(options: CodexCliProviderOptions = {}) {
    this.executable = options.executable ?? "/usr/bin/codex";
    this.model = options.model ?? null;
    this.timeoutMs = options.timeoutMs ?? 120_000;
    this.environment = options.environment ?? process.env;
    this.providerId = `codex-cli-ephemeral-v1:${this.model ?? "configured"}`;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.lastEvidence ? { ...this.lastEvidence } : null;
  }

  async decide(context: CompiledAgentContext): Promise<OperationDecision> {
    const root = mkdtempSync(join(tmpdir(), "ordivon-game-codex-"));
    const work = join(root, "work");
    mkdirSync(work);
    try {
      const schemaPath = join(root, "decision.schema.json");
      const outputPath = join(root, "decision.json");
      writeFileSync(schemaPath, JSON.stringify({
        type: "object",
        additionalProperties: false,
        required: ["contextId", "selectedOperationCandidateId", "riskLevel", "confidence", "rationale"],
        properties: {
          contextId: { type: "string" },
          selectedOperationCandidateId: { type: ["string", "null"] },
          riskLevel: { enum: ["low", "medium", "high", "critical"] },
          confidence: { type: "number", minimum: 0, maximum: 1 },
          rationale: { type: "string", minLength: 1 },
        },
      }, null, 2) + "\n");
      const prompt = [
        "You are one replaceable cognitive step inside a persistent game Agent Host.",
        "Use only the canonical Context below. Apply strategy.decisionPolicy in order. Start from the sole strategy.selectionClass=preferred Operation; never choose blocked or defer while preferred exists. Choose exactly one allowed Operation by copying its operationCandidateId and contextId exactly.",
        "Never invent Commands, objects, paths, Effects, completion claims, or another Operation. Return JSON only.",
        "",
        canonicalJson(context.payload),
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
        throw new ProviderAdapterError("process_failed", `Codex exited ${result.exitCode}: ${result.stderr.trim().slice(-2_000)}`);
      }
      let value: unknown;
      try { value = JSON.parse(readFileSync(outputPath, "utf8")); }
      catch (error) { throw new ProviderAdapterError("invalid_output", "Codex did not write valid structured output", { cause: error }); }
      const decision = parseModelDecisionOutput(context, value, this.providerId);
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
