import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";

import { AdmissionLabError } from "./errors.ts";
import type {
  AdmissionChainDecision,
  AgentAdmissionDecision,
  AgentAdmissionInput,
  AuthorityProjection,
  EffectAdmissionDecision,
} from "./model.ts";

interface OpaEvalResult<T> {
  result?: Array<{
    expressions?: Array<{
      value?: T;
    }>;
  }>;
}

const defaultAgentPolicy = fileURLToPath(
  new URL("../../../policies/agent_admission.rego", import.meta.url),
);
const defaultEffectPolicy = fileURLToPath(
  new URL("../../../policies/effect_admission.rego", import.meta.url),
);

async function opaEval<T>(
  policyPath: string,
  query: string,
  input: unknown,
  opaPath: string,
): Promise<T> {
  return await new Promise<T>((resolve, reject) => {
    const child = spawn(
      opaPath,
      ["eval", "--format=json", "--data", policyPath, "--stdin-input", query],
      { stdio: ["pipe", "pipe", "pipe"] },
    );
    const stdout: Buffer[] = [];
    const stderr: Buffer[] = [];
    child.stdout.on("data", (chunk: Buffer) => stdout.push(chunk));
    child.stderr.on("data", (chunk: Buffer) => stderr.push(chunk));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code !== 0) {
        reject(
          new AdmissionLabError(
            "policy_unavailable",
            `OPA failed: ${Buffer.concat(stderr).toString("utf8").trim()}`,
            503,
          ),
        );
        return;
      }
      try {
        const parsed = JSON.parse(
          Buffer.concat(stdout).toString("utf8"),
        ) as OpaEvalResult<T>;
        const value = parsed.result?.[0]?.expressions?.[0]?.value;
        if (value === undefined) throw new Error("OPA decision is undefined");
        resolve(value);
      } catch (error) {
        reject(
          new AdmissionLabError(
            "policy_invalid_output",
            error instanceof Error ? error.message : "OPA output is invalid.",
            503,
          ),
        );
      }
    });
    child.stdin.end(JSON.stringify(input));
  });
}

function effectInput(projection: AuthorityProjection): unknown {
  return {
    actorIds: [projection.actorId],
    authorities: [
      {
        authorityId: projection.authorityId,
        actorId: projection.actorId,
        zoneRefs: [projection.zoneRef],
        capabilities: [projection.capability],
        authorityDigest: projection.authorityDigest,
      },
    ],
    request: projection,
  };
}

export class OpaAdmissionEngine {
  private readonly agentPolicyPath: string;
  private readonly effectPolicyPath: string;
  private readonly opaPath: string;

  constructor(
    agentPolicyPath = defaultAgentPolicy,
    effectPolicyPath = defaultEffectPolicy,
    opaPath = "/usr/bin/opa",
  ) {
    this.agentPolicyPath = agentPolicyPath;
    this.effectPolicyPath = effectPolicyPath;
    this.opaPath = opaPath;
  }

  async evaluate(input: AgentAdmissionInput): Promise<AdmissionChainDecision> {
    const agent = await opaEval<AgentAdmissionDecision>(
      this.agentPolicyPath,
      "data.ordivon.security.v2.agent_admission.decision",
      input,
      this.opaPath,
    );

    if (agent.outcome !== "ALLOW" || agent.authorityProjection === null) {
      return { agent, effect: null };
    }

    const effect = await opaEval<EffectAdmissionDecision>(
      this.effectPolicyPath,
      "data.ordivon.security.v2.effect_admission.decision",
      effectInput(agent.authorityProjection),
      this.opaPath,
    );

    if (!effect.admitted) {
      throw new AdmissionLabError(
        "effect_admission_rejected",
        `Existing effect admission rejected projection: ${effect.reason}`,
        403,
      );
    }
    return { agent, effect };
  }
}
