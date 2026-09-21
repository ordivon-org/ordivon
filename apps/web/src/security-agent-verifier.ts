import {
  AgentRequestVerificationError,
  OAuthDpopAgentRequestVerifier,
} from "../../../platform/security/contracts/agent-request-verifier-v1/src/index.ts";

import type {
  AgentRequestVerifier,
  AgentVerificationRequest,
} from "./agent-authority.ts";
import type { WebConfig } from "./config.ts";
import { WebProblem } from "./errors.ts";
import type { VerifiedAgent } from "./model.ts";
import type { WebStore } from "./store.ts";

function toHeaders(
  input: Readonly<Record<string, string | string[] | undefined>>,
): Headers {
  const headers = new Headers();
  for (const [name, value] of Object.entries(input)) {
    if (value === undefined) continue;
    if (Array.isArray(value)) {
      for (const item of value) headers.append(name, item);
    } else {
      headers.set(name, value);
    }
  }
  return headers;
}

export class SecurityAgentRequestVerifier implements AgentRequestVerifier {
  private readonly verifier: OAuthDpopAgentRequestVerifier;
  private readonly origin: string;

  constructor(config: WebConfig, replayGuard: WebStore) {
    if (config.agentIssuer === undefined) {
      throw new Error("agentIssuer is required to configure Agent verification");
    }
    this.origin = config.origin;
    this.verifier = new OAuthDpopAgentRequestVerifier(
      {
        issuer: config.agentIssuer,
        audience: config.origin,
        allowInsecure: config.agentAllowInsecureIssuer === true,
      },
      replayGuard,
    );
  }

  async verify(request: AgentVerificationRequest): Promise<VerifiedAgent> {
    const webRequest = new Request(new URL(request.url, this.origin), {
      method: request.method,
      headers: toHeaders(request.headers),
    });
    try {
      return await this.verifier.verify(webRequest);
    } catch (error) {
      if (error instanceof AgentRequestVerificationError) {
        throw new WebProblem(
          401,
          "agent-request-verification-failed",
          "Agent verification failed",
          "OAuth/DPoP Agent request verification failed.",
        );
      }
      throw error;
    }
  }
}
