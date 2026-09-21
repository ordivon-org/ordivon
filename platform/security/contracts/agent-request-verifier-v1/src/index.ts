import * as oauth from "oauth4webapi";

export interface VerifiedAgent {
  readonly agentId: string;
  readonly clientId: string;
  readonly subject: string;
}

export interface AgentRequestVerifierOptions {
  readonly issuer: string;
  readonly audience: string;
  readonly allowInsecure?: boolean;
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

export class AgentRequestVerificationError extends Error {
  readonly code: "agent_request_verification_failed";

  constructor() {
    super("OAuth/DPoP Agent request verification failed.");
    this.name = "AgentRequestVerificationError";
    this.code = "agent_request_verification_failed";
  }
}

function verifiedProofId(request: Request): string {
  const proof = request.headers.get("dpop");
  if (proof === null || proof.includes(",")) {
    throw new AgentRequestVerificationError();
  }
  const parts = proof.split(".");
  if (parts.length !== 3) {
    throw new AgentRequestVerificationError();
  }
  try {
    const payload = JSON.parse(
      Buffer.from(parts[1]!, "base64url").toString("utf8"),
    ) as Record<string, unknown>;
    if (typeof payload.jti !== "string") {
      throw new Error("missing jti");
    }
    return payload.jti;
  } catch {
    throw new AgentRequestVerificationError();
  }
}

export class OAuthDpopAgentRequestVerifier {
  private authorizationServer: oauth.AuthorizationServer | undefined;
  private readonly issuer: URL;
  private readonly options: AgentRequestVerifierOptions;
  private readonly replayGuard: DpopReplayGuard;

  constructor(
    options: AgentRequestVerifierOptions,
    replayGuard: DpopReplayGuard,
  ) {
    this.options = options;
    this.replayGuard = replayGuard;
    this.issuer = new URL(options.issuer);
  }

  private protocolOptions(): { [oauth.allowInsecureRequests]?: boolean } {
    return this.options.allowInsecure
      ? { [oauth.allowInsecureRequests]: true }
      : {};
  }

  private async discover(): Promise<oauth.AuthorizationServer> {
    if (this.authorizationServer !== undefined) {
      return this.authorizationServer;
    }
    const response = await oauth.discoveryRequest(
      this.issuer,
      this.protocolOptions(),
    );
    this.authorizationServer = await oauth.processDiscoveryResponse(
      this.issuer,
      response,
    );
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
      if (
        typeof claims.client_id !== "string" ||
        claims.client_id.length === 0 ||
        typeof claims.sub !== "string" ||
        claims.sub.length === 0
      ) {
        throw new AgentRequestVerificationError();
      }
      return {
        agentId: "oauth-client:" + claims.client_id,
        clientId: claims.client_id,
        subject: claims.sub,
      };
    } catch (error) {
      if (error instanceof AgentRequestVerificationError) {
        throw error;
      }
      throw new AgentRequestVerificationError();
    }
  }
}
