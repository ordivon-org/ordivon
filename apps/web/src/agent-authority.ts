import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

import { WebProblem } from "./errors.ts";
import type {
  AdmissionChainDecision,
  AgentAdmissionInput,
  AgentEffectRequest,
  AgentGrantSnapshot,
  VerifiedAgent,
  VerifiedApproval,
} from "./model.ts";

export interface AgentVerificationRequest {
  readonly method: string;
  readonly url: string;
  readonly headers: Readonly<Record<string, string | string[] | undefined>>;
}

export interface AgentRequestVerifier {
  verify(request: AgentVerificationRequest): Promise<VerifiedAgent>;
}

export interface AgentAdmissionEvaluator {
  evaluate(input: AgentAdmissionInput): Promise<AdmissionChainDecision>;
}

export class SecurityContractAdmissionEvaluator implements AgentAdmissionEvaluator {
  private readonly evaluatorPath: string;

  constructor(
    evaluatorPath = fileURLToPath(
      new URL(
        "../../../platform/security/contracts/agent-admission-v1/evaluate.py",
        import.meta.url,
      ),
    ),
  ) {
    this.evaluatorPath = evaluatorPath;
  }

  async evaluate(input: AgentAdmissionInput): Promise<AdmissionChainDecision> {
    const result = spawnSync("/usr/bin/python3", [this.evaluatorPath], {
      input: JSON.stringify(input),
      encoding: "utf8",
      maxBuffer: 1024 * 1024,
    });
    if (result.status !== 0) {
      throw new WebProblem(
        503,
        "security-admission-unavailable",
        "Security admission unavailable",
        "The Security-owned Agent Admission contract did not return a decision.",
      );
    }
    const parsed: unknown = JSON.parse(result.stdout);
    if (
      parsed === null ||
      typeof parsed !== "object" ||
      !("kind" in parsed) ||
      (parsed as { kind?: unknown }).kind !==
        "ordivon.security.agent-admission-chain"
    ) {
      throw new WebProblem(
        503,
        "security-admission-invalid",
        "Security admission unavailable",
        "The Security-owned Agent Admission contract returned an invalid decision.",
      );
    }
    return parsed as AdmissionChainDecision;
  }
}

export function stableEffectDigest(value: unknown): string {
  return (
    "sha256:" +
    createHash("sha256").update(JSON.stringify(value)).digest("hex")
  );
}

export function admissionInput(
  nowEpochSeconds: number,
  grant: AgentGrantSnapshot,
  agent: VerifiedAgent,
  effect: AgentEffectRequest,
  approval: VerifiedApproval,
): AgentAdmissionInput {
  return {
    schemaVersion: 1,
    nowEpochSeconds,
    principal: {
      principalId: grant.principalId,
      authenticated: true,
      authnMethod: "webauthn",
    },
    agent: {
      agentId: agent.agentId,
      authenticated: true,
      credentialKind: "dpop-key",
    },
    grant: {
      grantId: grant.grantId,
      grantDigest: grant.grantDigest,
      active: grant.active,
      principalId: grant.principalId,
      agentId: grant.agentId,
      audience: grant.audience,
      allowedActions: grant.allowedActions,
      resourcePrefixes: grant.resourcePrefixes,
      expiresAtEpochSeconds: grant.expiresAtEpochSeconds,
      maxRiskClass: grant.maxRiskClass,
      stepUpAtOrAbove: grant.stepUpAtOrAbove,
      remainingEffects: grant.remainingEffects,
    },
    effect,
    approval,
  };
}
