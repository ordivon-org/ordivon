import { randomUUID } from "node:crypto";

import {
  generateAuthenticationOptions,
  generateRegistrationOptions,
  verifyAuthenticationResponse,
  verifyRegistrationResponse,
  type AuthenticationResponseJSON,
  type RegistrationResponseJSON,
} from "@simplewebauthn/server";

import { AdmissionLabError } from "./errors.ts";
import type { GrantStore } from "./grant-store.ts";
import type { EffectRequest, GrantCreate, VerifiedApproval } from "./model.ts";
import type { ChallengeRecord, PrincipalStore, StoredCredential } from "./principal-store.ts";

export interface WebAuthnServiceOptions {
  readonly rpName: string;
  readonly rpID: string;
  readonly origin: string;
  readonly audience: string;
  readonly challengeTtlSeconds?: number;
  readonly approvalTtlSeconds?: number;
  readonly grantTtlSeconds?: number;
  readonly now?: () => number;
}

interface GrantIssuePayload {
  readonly grant: GrantCreate;
}

interface GrantRevokePayload {
  readonly grantId: string;
  readonly grantDigest: string;
}

interface EffectApprovalPayload {
  readonly effectId: string;
  readonly effectDigest: string;
}

function asGrantIssuePayload(value: unknown): GrantIssuePayload {
  if (
    value === null ||
    typeof value !== "object" ||
    !("grant" in value) ||
    value.grant === null ||
    typeof value.grant !== "object"
  ) {
    throw new AdmissionLabError("challenge_payload_invalid", "Grant challenge payload is invalid.", 500);
  }
  return value as GrantIssuePayload;
}

function asGrantRevokePayload(value: unknown): GrantRevokePayload {
  if (
    value === null ||
    typeof value !== "object" ||
    !("grantId" in value) ||
    !("grantDigest" in value) ||
    typeof value.grantId !== "string" ||
    typeof value.grantDigest !== "string"
  ) {
    throw new AdmissionLabError(
      "challenge_payload_invalid",
      "Grant revoke challenge payload is invalid.",
      500,
    );
  }
  return value as GrantRevokePayload;
}

function asEffectApprovalPayload(value: unknown): EffectApprovalPayload {
  if (
    value === null ||
    typeof value !== "object" ||
    !("effectId" in value) ||
    !("effectDigest" in value) ||
    typeof value.effectId !== "string" ||
    typeof value.effectDigest !== "string"
  ) {
    throw new AdmissionLabError(
      "challenge_payload_invalid",
      "Effect approval challenge payload is invalid.",
      500,
    );
  }
  return value as EffectApprovalPayload;
}

export class WebAuthnPrincipalService {
  private readonly principals: PrincipalStore;
  private readonly grants: GrantStore;
  private readonly options: WebAuthnServiceOptions;
  private readonly challengeTtlSeconds: number;
  private readonly approvalTtlSeconds: number;
  private readonly grantTtlSeconds: number;
  private readonly now: () => number;

  constructor(
    principals: PrincipalStore,
    grants: GrantStore,
    options: WebAuthnServiceOptions,
  ) {
    this.principals = principals;
    this.grants = grants;
    this.options = options;
    this.challengeTtlSeconds = options.challengeTtlSeconds ?? 120;
    this.approvalTtlSeconds = options.approvalTtlSeconds ?? 120;
    this.grantTtlSeconds = options.grantTtlSeconds ?? 3600;
    this.now = options.now ?? (() => Math.floor(Date.now() / 1000));
  }

  async registrationOptions(
    principalId: string,
    userName: string,
    displayName: string,
  ) {
    const now = this.now();
    this.principals.ensurePrincipal(principalId, userName, displayName, now);
    const existing = this.principals.listCredentials(principalId);
    const options = await generateRegistrationOptions({
      rpName: this.options.rpName,
      rpID: this.options.rpID,
      userName,
      userDisplayName: displayName,
      userID: new TextEncoder().encode(principalId),
      attestationType: "none",
      excludeCredentials: existing.map((credential) => ({
        id: credential.id,
        transports: [...credential.transports],
      })),
      authenticatorSelection: {
        residentKey: "preferred",
        userVerification: "required",
      },
    });
    const challenge = this.principals.createChallenge(
      "register",
      principalId,
      options.challenge,
      { principalId, userName, displayName },
      now + this.challengeTtlSeconds,
    );
    return { challengeId: challenge.challengeId, options };
  }

  async verifyRegistration(
    challengeId: string,
    response: RegistrationResponseJSON,
  ): Promise<{ principalId: string; credentialId: string }> {
    const now = this.now();
    const challenge = this.principals.consumeChallenge(challengeId, "register", now);
    const result = await verifyRegistrationResponse({
      response,
      expectedChallenge: challenge.challenge,
      expectedOrigin: this.options.origin,
      expectedRPID: this.options.rpID,
      requireUserPresence: true,
      requireUserVerification: true,
    });
    if (!result.verified) {
      throw new AdmissionLabError(
        "webauthn_registration_failed",
        "WebAuthn registration did not verify.",
        401,
      );
    }
    const info = result.registrationInfo;
    this.principals.putCredential(
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
    return { principalId: challenge.principalId, credentialId: info.credential.id };
  }

  private async authenticationOptions(
    principalId: string,
    purpose: "grant-issue" | "grant-revoke" | "effect-approve",
    payload: unknown,
  ) {
    const now = this.now();
    this.principals.requirePrincipal(principalId);
    const credentials = this.principals.listCredentials(principalId);
    if (credentials.length === 0) {
      throw new AdmissionLabError(
        "principal_has_no_webauthn_credential",
        "Principal has no registered WebAuthn credential.",
        409,
      );
    }
    const options = await generateAuthenticationOptions({
      rpID: this.options.rpID,
      allowCredentials: credentials.map((credential) => ({
        id: credential.id,
        transports: [...credential.transports],
      })),
      userVerification: "required",
    });
    const challenge = this.principals.createChallenge(
      purpose,
      principalId,
      options.challenge,
      payload,
      now + this.challengeTtlSeconds,
    );
    return { challengeId: challenge.challengeId, options };
  }

  async grantIssueOptions(principalId: string, agentId: string) {
    if (!/^oauth-client:[A-Za-z0-9._:-]{1,128}$/.test(agentId)) {
      throw new AdmissionLabError("invalid_agent_id", "Agent identity is invalid.", 422);
    }
    const now = this.now();
    const grant: GrantCreate = {
      grantId: `grant:webauthn:${randomUUID()}`,
      principalId,
      agentId,
      audience: this.options.audience,
      allowedActions: ["comment.create", "site.publish"],
      resourcePrefixes: ["/comments/", "/site/"],
      expiresAtEpochSeconds: now + this.grantTtlSeconds,
      maxRiskClass: "R4",
      stepUpAtOrAbove: "R4",
      remainingEffects: 6,
    };
    const auth = await this.authenticationOptions(
      principalId,
      "grant-issue",
      { grant } satisfies GrantIssuePayload,
    );
    return { ...auth, grant };
  }

  private async verifyAuthenticationChallenge(
    challenge: ChallengeRecord,
    response: AuthenticationResponseJSON,
  ): Promise<StoredCredential> {
    const credential = this.principals.getCredential(response.id);
    if (credential.principalId !== challenge.principalId) {
      throw new AdmissionLabError(
        "credential_principal_mismatch",
        "WebAuthn credential does not belong to the expected Principal.",
        403,
      );
    }
    const result = await verifyAuthenticationResponse({
      response,
      expectedChallenge: challenge.challenge,
      expectedOrigin: this.options.origin,
      expectedRPID: this.options.rpID,
      credential: {
        id: credential.id,
        publicKey: Uint8Array.from(credential.publicKey),
        counter: credential.counter,
        transports: [...credential.transports],
      },
      requireUserVerification: true,
    });
    if (!result.verified || !result.authenticationInfo.userVerified) {
      throw new AdmissionLabError(
        "webauthn_authentication_failed",
        "WebAuthn authentication did not verify with user verification.",
        401,
      );
    }
    this.principals.updateCredentialCounter(
      credential.id,
      credential.counter,
      result.authenticationInfo.newCounter,
      this.now(),
    );
    return credential;
  }

  async verifyGrantIssue(
    challengeId: string,
    response: AuthenticationResponseJSON,
  ) {
    const now = this.now();
    const challenge = this.principals.consumeChallenge(challengeId, "grant-issue", now);
    await this.verifyAuthenticationChallenge(challenge, response);
    const payload = asGrantIssuePayload(challenge.payload);
    if (
      payload.grant.principalId !== challenge.principalId ||
      payload.grant.audience !== this.options.audience
    ) {
      throw new AdmissionLabError(
        "grant_binding_invalid",
        "WebAuthn grant payload is not bound to this Principal and audience.",
        500,
      );
    }
    return this.grants.createGrant(payload.grant);
  }

  async grantRevokeOptions(principalId: string, grantId: string) {
    const grant = this.grants.getGrant(grantId);
    if (grant.principalId !== principalId) {
      throw new AdmissionLabError(
        "grant_principal_mismatch",
        "Delegation grant does not belong to this Principal.",
        403,
      );
    }
    const auth = await this.authenticationOptions(
      principalId,
      "grant-revoke",
      {
        grantId: grant.grantId,
        grantDigest: grant.grantDigest,
      } satisfies GrantRevokePayload,
    );
    return { ...auth, grantId: grant.grantId, grantDigest: grant.grantDigest };
  }

  async verifyGrantRevoke(
    challengeId: string,
    response: AuthenticationResponseJSON,
  ) {
    const now = this.now();
    const challenge = this.principals.consumeChallenge(challengeId, "grant-revoke", now);
    await this.verifyAuthenticationChallenge(challenge, response);
    const payload = asGrantRevokePayload(challenge.payload);
    const current = this.grants.getGrant(payload.grantId);
    if (
      current.principalId !== challenge.principalId ||
      current.grantDigest !== payload.grantDigest
    ) {
      throw new AdmissionLabError(
        "grant_revoke_binding_invalid",
        "Delegation grant changed before WebAuthn revocation.",
        409,
      );
    }
    this.grants.revokeGrant(current.grantId);
    return this.grants.getGrant(current.grantId);
  }

  registerStepUp(principalId: string, effect: EffectRequest): void {
    this.principals.registerPendingEffect(principalId, effect, this.now());
  }

  async effectApprovalOptions(principalId: string, effectId: string) {
    const pending = this.principals.requirePendingEffect(principalId, effectId, this.now());
    return await this.authenticationOptions(
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
  ): Promise<{ principalId: string; effectId: string }> {
    const now = this.now();
    const challenge = this.principals.consumeChallenge(challengeId, "effect-approve", now);
    const credential = await this.verifyAuthenticationChallenge(challenge, response);
    const payload = asEffectApprovalPayload(challenge.payload);
    const pending = this.principals.requirePendingEffect(
      challenge.principalId,
      payload.effectId,
      now,
    );
    if (pending.effectDigest !== payload.effectDigest) {
      throw new AdmissionLabError(
        "effect_approval_binding_invalid",
        "Pending effect digest changed before WebAuthn approval.",
        409,
      );
    }
    this.principals.putEffectApproval(
      challenge.principalId,
      credential.id,
      payload.effectId,
      payload.effectDigest,
      now,
      this.approvalTtlSeconds,
    );
    return { principalId: challenge.principalId, effectId: payload.effectId };
  }

  lookupEffectApproval(principalId: string, effect: EffectRequest): VerifiedApproval {
    return this.principals.lookupEffectApproval(principalId, effect, this.now());
  }

  consumeEffectApproval(principalId: string, effect: EffectRequest): void {
    this.principals.consumeEffectApproval(principalId, effect, this.now());
  }
}
