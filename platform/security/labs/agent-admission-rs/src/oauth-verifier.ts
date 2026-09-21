import * as oauth from "oauth4webapi";

import { AdmissionLabError } from "./errors.ts";
import type { VerifiedAgent } from "./model.ts";

export interface OAuthVerifierOptions {
  readonly issuer: string;
  readonly audience: string;
  readonly allowInsecureLab?: boolean;
  readonly now?: () => number;
  readonly proofReplayTtlSeconds?: number;
}

export interface DpopReplayGuard {
  consumeDpopProof(
    proofId: string,
    nowEpochSeconds: number,
    ttlSeconds?: number,
  ): void | Promise<void>;
}

export interface AgentVerifier {
  verify(request: Request): Promise<VerifiedAgent>;
}

function verifiedProofId(request: Request): string {
  const proof = request.headers.get("dpop");
  if (proof === null || proof.includes(",")) {
    throw new AdmissionLabError(
      "oauth_verification_failed",
      "OAuth/DPoP verification failed.",
      401,
    );
  }
  const parts = proof.split(".");
  if (parts.length !== 3) {
    throw new AdmissionLabError(
      "oauth_verification_failed",
      "OAuth/DPoP verification failed.",
      401,
    );
  }
  try {
    const payload = JSON.parse(
      Buffer.from(parts[1]!, "base64url").toString("utf8"),
    ) as Record<string, unknown>;
    if (typeof payload.jti !== "string") throw new Error("missing jti");
    return payload.jti;
  } catch {
    throw new AdmissionLabError(
      "oauth_verification_failed",
      "OAuth/DPoP verification failed.",
      401,
    );
  }
}

export class OAuthDpopAgentVerifier implements AgentVerifier {
  private authorizationServer: oauth.AuthorizationServer | undefined;
  private readonly issuer: URL;
  private readonly options: OAuthVerifierOptions;
  private readonly replayGuard: DpopReplayGuard;

  constructor(options: OAuthVerifierOptions, replayGuard: DpopReplayGuard) {
    this.options = options;
    this.replayGuard = replayGuard;
    this.issuer = new URL(options.issuer);
  }

  private protocolOptions(): { [oauth.allowInsecureRequests]?: boolean } {
    return this.options.allowInsecureLab
      ? { [oauth.allowInsecureRequests]: true }
      : {};
  }

  private async discover(): Promise<oauth.AuthorizationServer> {
    if (this.authorizationServer !== undefined) return this.authorizationServer;
    const response = await oauth.discoveryRequest(this.issuer, this.protocolOptions());
    this.authorizationServer = await oauth.processDiscoveryResponse(this.issuer, response);
    return this.authorizationServer;
  }

  async verify(request: Request): Promise<VerifiedAgent> {
    try {
      const authorizationServer = await this.discover();
      const claims = await oauth.validateJwtAccessToken(
        authorizationServer,
        request,
        this.options.audience,
        {
          ...this.protocolOptions(),
          requireDPoP: true,
          signingAlgorithms: ["RS256", "ES256"],
        },
      );
      await this.replayGuard.consumeDpopProof(
        verifiedProofId(request),
        this.options.now?.() ?? Math.floor(Date.now() / 1000),
        this.options.proofReplayTtlSeconds ?? 600,
      );
      return {
        agentId: `oauth-client:${claims.client_id}`,
        clientId: claims.client_id,
        subject: claims.sub,
      };
    } catch (error) {
      if (error instanceof AdmissionLabError) throw error;
      throw new AdmissionLabError(
        "oauth_verification_failed",
        "OAuth/DPoP verification failed.",
        401,
      );
    }
  }
}
