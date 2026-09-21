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
import type { Principal } from "./model.ts";
import { WebStore } from "./store.ts";

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
}
