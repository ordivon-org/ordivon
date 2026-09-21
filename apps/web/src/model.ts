export interface Principal {
  readonly principalId: string;
  readonly userName: string;
  readonly displayName: string;
}

export interface SessionView {
  readonly sessionId: string;
  readonly principalId: string;
  readonly createdAt: number;
  readonly authenticatedAt: number;
  readonly lastSeenAt: number;
  readonly idleExpiresAt: number;
  readonly absoluteExpiresAt: number;
  readonly revokedAt: number | null;
  readonly authnMethod: "webauthn";
  readonly userAgent: string | null;
}

export interface AuthenticatedSession {
  readonly tokenHash: string;
  readonly session: SessionView;
  readonly principal: Principal;
}

export interface StoredCredential {
  readonly credentialId: string;
  readonly principalId: string;
  readonly publicKey: Uint8Array;
  readonly counter: number;
  readonly transports: readonly string[];
  readonly deviceType: string;
  readonly backedUp: boolean;
  readonly createdAt: number;
  readonly lastUsedAt: number;
  readonly revokedAt: number | null;
}

export type ChallengePurpose = "register" | "login";

export interface ChallengeRecord {
  readonly challengeId: string;
  readonly purpose: ChallengePurpose;
  readonly principalId: string;
  readonly challenge: string;
  readonly expiresAt: number;
}

export interface CanaryNote {
  readonly noteId: string;
  readonly principalId: string;
  readonly content: string;
  readonly state: "DRAFT" | "PUBLISHED";
  readonly createdAt: number;
  readonly publishedAt: number | null;
}
