import { ProviderAdapterError } from "./provider-runtime.ts";
import type { CompiledTeamContext, TeamProviderDecision } from "./model.ts";
import type { TeamDecisionProvider } from "./providers.ts";

export class TeamProviderChain implements TeamDecisionProvider {
  readonly providerId: string;
  readonly providers: TeamDecisionProvider[];
  private lastEvidence: Record<string, unknown> | null = null;

  constructor(providers: TeamDecisionProvider[]) {
    if (providers.length === 0) throw new TypeError("Team Provider Chain requires at least one Provider");
    this.providers = [...providers];
    this.providerId = `team-provider-chain:${providers.map((provider) => provider.providerId).join("->")}`;
  }

  evidenceMetadata(): Record<string, unknown> | null {
    return this.lastEvidence ? structuredClone(this.lastEvidence) : null;
  }

  async decide(context: CompiledTeamContext): Promise<TeamProviderDecision> {
    const attempts: Array<Record<string, unknown>> = [];
    for (const provider of this.providers) {
      try {
        const decision = await provider.decide(context);
        attempts.push({ providerId: provider.providerId, status: "succeeded", evidence: provider.evidenceMetadata?.() ?? null });
        this.lastEvidence = { chainId: this.providerId, selectedProviderId: provider.providerId, attempts };
        return decision;
      } catch (error) {
        if (!(error instanceof ProviderAdapterError)) throw error;
        attempts.push({ providerId: provider.providerId, status: "failed", code: error.code, message: error.message, evidence: provider.evidenceMetadata?.() ?? null });
      }
    }
    this.lastEvidence = { chainId: this.providerId, selectedProviderId: null, attempts };
    throw new ProviderAdapterError("unavailable", "Every Team Provider failed technically");
  }
}
