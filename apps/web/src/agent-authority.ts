import { spawn } from "node:child_process";
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
    // Node's event loop must not block while Python validates the schema and
    // OPA evaluates the Security-owned policies.
    const output = await new Promise<string>((resolve, reject) => {
      const child = spawn("/usr/bin/python3", [this.evaluatorPath], {
        stdio: ["pipe", "pipe", "pipe"],
        timeout: 10_000,
        killSignal: "SIGKILL",
      });
      const limit = 1024 * 1024;
      let stdout = "";
      let stdoutBytes = 0;
      let settled = false;
      const fail = () => {
        if (settled) return;
        settled = true;
        child.kill("SIGKILL");
        reject(new WebProblem(
          503, "security-admission-unavailable", "Security admission unavailable",
          "The Security-owned Agent Admission contract did not return a decision.",
        ));
      };
      child.stdout.setEncoding("utf8");
      child.stdout.on("data", (chunk: string) => {
        stdoutBytes += Buffer.byteLength(chunk);
        if (stdoutBytes > limit) {
          fail();
        } else {
          stdout += chunk;
        }
      });
      // Do not expose OPA/Python diagnostic output or token-bearing arguments.
      child.stderr.resume();
      child.on("error", fail);
      child.on("close", (code, signal) => {
        if (settled) return;
        if (code !== 0 || signal !== null) {
          fail();
          return;
        }
        settled = true;
        resolve(stdout);
      });
      child.stdin.on("error", fail);
      child.stdin.end(JSON.stringify(input));
    });
    let parsed: unknown;
    try {
      parsed = JSON.parse(output);
    } catch {
      throw new WebProblem(
        503, "security-admission-invalid", "Security admission unavailable",
        "The Security-owned Agent Admission contract returned invalid JSON.",
      );
    }
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
