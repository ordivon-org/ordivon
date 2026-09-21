import { randomUUID } from "node:crypto";

import {
  generateAuthenticationOptions,
  generateRegistrationOptions,
  verifyAuthenticationResponse,
  verifyRegistrationResponse,
  type AuthenticationResponseJSON,
  type RegistrationResponseJSON,
} from "@simplewebauthn/server";

import type { WebConfig } from "./config.ts";
import { WebProblem } from "./errors.ts";
import type { AgentGrantCreate, Principal } from "./model.ts";
import { WebStore } from "./store.ts";

interface GrantIssuePayload {
  readonly grant: AgentGrantCreate;
}

interface GrantRevokePayload {
  readonly grantId: string;
  readonly grantDigest: string;
}

interface EffectApprovalPayload {
  readonly effectId: string;
  readonly effectDigest: string;
}

function grantIssuePayload(value: unknown): GrantIssuePayload {
  if (value === null || typeof value !== "object" || !("grant" in value) || value.grant === null || typeof value.grant !== "object") {
    throw new WebProblem(500, "challenge-payload-invalid", "Challenge payload invalid", "The Grant issuance challenge payload is invalid.");
  }
  return value as GrantIssuePayload;
}

function grantRevokePayload(value: unknown): GrantRevokePayload {
  if (value === null || typeof value !== "object" || !("grantId" in value) || !("grantDigest" in value) || typeof value.grantId !== "string" || typeof value.grantDigest !== "string") {
    throw new WebProblem(500, "challenge-payload-invalid", "Challenge payload invalid", "The Grant revocation challenge payload is invalid.");
  }
  return value as GrantRevokePayload;
}

function effectApprovalPayload(value: unknown): EffectApprovalPayload {
  if (value === null || typeof value !== "object" || !("effectId" in value) || !("effectDigest" in value) || typeof value.effectId !== "string" || typeof value.effectDigest !== "string") {
    throw new WebProblem(500, "challenge-payload-invalid", "Challenge payload invalid", "The Effect approval challenge payload is invalid.");
  }
  return value as EffectApprovalPayload;
}

export class WebAuthnAccountService {
  private readonly store: WebStore;
  private readonly config: WebConfig;
  private readonly now: () => number;

  constructor(store: WebStore, config: WebConfig, now?: () => number) {
    this.store = store;
    this.config = config;
    this.now = now ?? (() => Math.floor(Date.now() / 1000));
  }

  async registrationOptions(
    principalId: string,
    userName: string,
    displayName: string,
  ) {
    const now = this.now();
    const principal = this.store.ensurePrincipal(
      principalId,
      userName,
      displayName,
      now,
    );
    const credentials = this.store
      .listCredentials(principalId)
      .filter((credential) => credential.revokedAt === null);
    const options = await generateRegistrationOptions({
      rpName: this.config.rpName,
      rpID: this.config.rpID,
      userName: principal.userName,
      userDisplayName: principal.displayName,
      userID: new TextEncoder().encode(principal.principalId),
      attestationType: "none",
      excludeCredentials: credentials.map((credential) => ({
        id: credential.credentialId,
        transports: [...credential.transports],
      })),
      authenticatorSelection: {
        residentKey: "preferred",
        userVerification: "required",
      },
    });
    const challenge = this.store.createChallenge(
      "register",
      principalId,
      options.challenge,
      now,
    );
    return { challengeId: challenge.challengeId, options };
  }

  async verifyRegistration(
    challengeId: string,
    response: RegistrationResponseJSON,
  ): Promise<Principal> {
    const now = this.now();
    const challenge = this.store.consumeChallenge(
      challengeId,
      "register",
      now,
    );
    const result = await verifyRegistrationResponse({
      response,
      expectedChallenge: challenge.challenge,
      expectedOrigin: this.config.origin,
      expectedRPID: this.config.rpID,
      requireUserPresence: true,
      requireUserVerification: true,
    });
    if (!result.verified) {
      throw new WebProblem(
        401,
        "webauthn-registration-failed",
        "Registration failed",
        "The WebAuthn registration response did not verify.",
      );
    }
    const info = result.registrationInfo;
    this.store.putCredential(
      challenge.principalId,
      {
        id: info.credential.id,
        publicKey: info.credential.publicKey,
        counter: info.credential.counter,
        transports: response.response.transports ?? [],
        deviceType: info.credentialDeviceType,
        backedUp: info.credentialBackedUp,
      },
      now,
    );
    return this.store.getPrincipal(challenge.principalId);
  }

  async loginOptions(userName: string) {
    const now = this.now();
    const principal = this.store.findPrincipalByUserName(userName);
    const credentials = this.store
      .listCredentials(principal.principalId)
      .filter((credential) => credential.revokedAt === null);
    if (credentials.length === 0) {
      throw new WebProblem(
        409,
        "no-active-passkey",
        "No active passkey",
        "The Principal has no active WebAuthn credential.",
      );
    }
    const options = await generateAuthenticationOptions({
      rpID: this.config.rpID,
      allowCredentials: credentials.map((credential) => ({
        id: credential.credentialId,
        transports: [...credential.transports],
      })),
      userVerification: "required",
    });
    const challenge = this.store.createChallenge(
      "login",
      principal.principalId,
      options.challenge,
      now,
    );
    return { challengeId: challenge.challengeId, options };
  }

  private async authorityAuthenticationOptions(
    principalId: string,
    purpose: "grant-issue" | "grant-revoke" | "effect-approve",
    payload: unknown,
  ) {
    const now = this.now();
    const credentials = this.store
      .listCredentials(principalId)
      .filter((credential) => credential.revokedAt === null);
    if (credentials.length === 0) {
      throw new WebProblem(
        409,
        "no-active-passkey",
        "No active passkey",
        "The Principal has no active WebAuthn credential.",
      );
    }
    const options = await generateAuthenticationOptions({
      rpID: this.config.rpID,
      allowCredentials: credentials.map((credential) => ({
        id: credential.credentialId,
        transports: [...credential.transports],
      })),
      userVerification: "required",
    });
    const challenge = this.store.createChallenge(
      purpose,
      principalId,
      options.challenge,
      now,
      120,
      payload,
    );
    return { challengeId: challenge.challengeId, options };
  }

  private async verifyAuthorityAuthentication(
    challengeId: string,
    purpose: "grant-issue" | "grant-revoke" | "effect-approve",
    response: AuthenticationResponseJSON,
  ) {
    const now = this.now();
    const challenge = this.store.consumeChallenge(challengeId, purpose, now);
    const credential = this.store.getActiveCredential(response.id);
    if (credential.principalId !== challenge.principalId) {
      throw new WebProblem(
        403,
        "credential-principal-mismatch",
        "Credential mismatch",
        "The credential does not belong to the Principal for this challenge.",
      );
    }
    const result = await verifyAuthenticationResponse({
      response,
      expectedChallenge: challenge.challenge,
      expectedOrigin: this.config.origin,
      expectedRPID: this.config.rpID,
      credential: {
        id: credential.credentialId,
        publicKey: Uint8Array.from(credential.publicKey),
        counter: credential.counter,
        transports: [...credential.transports],
      },
      requireUserVerification: true,
    });
    if (!result.verified || !result.authenticationInfo.userVerified) {
      throw new WebProblem(
        401,
        "webauthn-authority-failed",
        "Authority verification failed",
        "The WebAuthn authority response did not verify.",
      );
    }
    this.store.updateCredentialCounter(
      credential.credentialId,
      credential.counter,
      result.authenticationInfo.newCounter,
      now,
    );
    return { challenge, credential, now };
  }

  async verifyLogin(
    challengeId: string,
    response: AuthenticationResponseJSON,
    userAgent: string | null,
  ) {
    const now = this.now();
    const challenge = this.store.consumeChallenge(challengeId, "login", now);
    const credential = this.store.getActiveCredential(response.id);
    if (credential.principalId !== challenge.principalId) {
      throw new WebProblem(
        403,
        "credential-principal-mismatch",
        "Credential mismatch",
        "The credential does not belong to the Principal for this challenge.",
      );
    }
    const result = await verifyAuthenticationResponse({
      response,
      expectedChallenge: challenge.challenge,
      expectedOrigin: this.config.origin,
      expectedRPID: this.config.rpID,
      credential: {
        id: credential.credentialId,
        publicKey: Uint8Array.from(credential.publicKey),
        counter: credential.counter,
        transports: [...credential.transports],
      },
      requireUserVerification: true,
    });
    if (!result.verified || !result.authenticationInfo.userVerified) {
      throw new WebProblem(
        401,
        "webauthn-login-failed",
        "Authentication failed",
        "The WebAuthn authentication response did not verify.",
      );
    }
    this.store.updateCredentialCounter(
      credential.credentialId,
      credential.counter,
      result.authenticationInfo.newCounter,
      now,
    );
    const created = this.store.createSession(
      challenge.principalId,
      now,
      this.config.sessionIdleSeconds,
      this.config.sessionAbsoluteSeconds,
      userAgent,
    );
    return {
      principal: this.store.getPrincipal(challenge.principalId),
      ...created,
    };
  }

  async agentGrantIssueOptions(principalId: string, agentId: string) {
    if (!/^oauth-client:[A-Za-z0-9._:-]{1,128}$/.test(agentId)) {
      throw new WebProblem(
        422,
        "invalid-agent-id",
        "Invalid Agent",
        "The Agent identity is invalid.",
      );
    }
    const now = this.now();
    const grant: AgentGrantCreate = {
      grantId: "grant:web:" + randomUUID(),
      principalId,
      agentId,
      audience: this.config.origin,
      allowedActions: ["canary.note.create", "canary.note.publish"],
      resourcePrefixes: ["/canary/notes"],
      expiresAtEpochSeconds: now + 3600,
      maxRiskClass: "R4",
      stepUpAtOrAbove: "R4",
      remainingEffects: 6,
    };
    const auth = await this.authorityAuthenticationOptions(
      principalId,
      "grant-issue",
      { grant } satisfies GrantIssuePayload,
    );
    return { ...auth, grant };
  }

  async verifyAgentGrantIssue(
    challengeId: string,
    response: AuthenticationResponseJSON,
  ) {
    const verified = await this.verifyAuthorityAuthentication(
      challengeId,
      "grant-issue",
      response,
    );
    const payload = grantIssuePayload(verified.challenge.payload);
    if (
      payload.grant.principalId !== verified.challenge.principalId ||
      payload.grant.audience !== this.config.origin
    ) {
      throw new WebProblem(
        409,
        "grant-binding-invalid",
        "Agent Grant binding invalid",
        "The signed Agent Grant is not bound to this Principal and audience.",
      );
    }
    return this.store.createAgentGrant(payload.grant, verified.now);
  }

  async agentGrantRevokeOptions(principalId: string, grantId: string) {
    const grant = this.store.getAgentGrant(grantId);
    if (grant.principalId !== principalId) {
      throw new WebProblem(
        403,
        "agent-grant-principal-mismatch",
        "Agent Grant mismatch",
        "The Agent Grant does not belong to this Principal.",
      );
    }
    const auth = await this.authorityAuthenticationOptions(
      principalId,
      "grant-revoke",
      {
        grantId: grant.grantId,
        grantDigest: grant.grantDigest,
      } satisfies GrantRevokePayload,
    );
    return {
      ...auth,
      grantId: grant.grantId,
      grantDigest: grant.grantDigest,
    };
  }

  async verifyAgentGrantRevoke(
    challengeId: string,
    response: AuthenticationResponseJSON,
  ) {
    const verified = await this.verifyAuthorityAuthentication(
      challengeId,
      "grant-revoke",
      response,
    );
    const payload = grantRevokePayload(verified.challenge.payload);
    return this.store.revokeAgentGrant(
      verified.challenge.principalId,
      payload.grantId,
      payload.grantDigest,
      verified.now,
    );
  }

  async effectApprovalOptions(principalId: string, effectId: string) {
    const pending = this.store.requirePendingEffectApproval(
      principalId,
      effectId,
      this.now(),
    );
    return await this.authorityAuthenticationOptions(
      principalId,
      "effect-approve",
      {
        effectId: pending.effectId,
        effectDigest: pending.effectDigest,
      } satisfies EffectApprovalPayload,
    );
  }

  async verifyEffectApproval(
    challengeId: string,
    response: AuthenticationResponseJSON,
  ) {
    const verified = await this.verifyAuthorityAuthentication(
      challengeId,
      "effect-approve",
      response,
    );
    const payload = effectApprovalPayload(verified.challenge.payload);
    const pending = this.store.requirePendingEffectApproval(
      verified.challenge.principalId,
      payload.effectId,
      verified.now,
    );
    if (pending.effectDigest !== payload.effectDigest) {
      throw new WebProblem(
        409,
        "effect-approval-binding-invalid",
        "Effect approval changed",
        "The pending Effect digest changed before approval.",
      );
    }
    this.store.putEffectApproval(
      verified.challenge.principalId,
      verified.credential.credentialId,
      payload.effectId,
      payload.effectDigest,
      verified.now,
    );
    return {
      principalId: verified.challenge.principalId,
      effectId: payload.effectId,
    };
  }

}
