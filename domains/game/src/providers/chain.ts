import type { CompiledAgentContext } from "../host/context.ts";
import { ProviderAdapterError, type OperationDecision, type OperationProvider } from "./types.ts";

export class ProviderChain implements OperationProvider {
  readonly providerId: string;
  readonly providers: OperationProvider[];
  private lastEvidence: Record<string, unknown> | null = null;

  constructor(providers: OperationProvider[]) {
    if (providers.length === 0) throw new TypeError("Provider Chain requires at least one Provider");
    this.providers = [...providers];
    this.providerId = `provider-chain:${providers.map((provider) => provider.providerId).join("->")}`;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.lastEvidence ? structuredClone(this.lastEvidence) : null;
  }

  async decide(context: CompiledAgentContext): Promise<OperationDecision> {
    const attempts: Array<Record<string, unknown>> = [];
    for (const provider of this.providers) {
      try {
        const decision = await provider.decide(context);
        attempts.push({ providerId: provider.providerId, status: "succeeded", evidence: provider.evidenceMetadata?.() ?? null });
        this.lastEvidence = { selectedProviderId: provider.providerId, attempts };
        return decision;
      } catch (error) {
        attempts.push({
          providerId: provider.providerId,
          status: "failed",
          error: error instanceof Error ? error.message : String(error),
          code: error instanceof ProviderAdapterError ? error.code : "unexpected_error",
          evidence: provider.evidenceMetadata?.() ?? null,
        });
      }
    }
    this.lastEvidence = { selectedProviderId: null, attempts };
    throw new ProviderAdapterError("unavailable", "Every Provider in the chain failed");
  }
}
