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

export type ChallengePurpose =
  | "register"
  | "login"
  | "grant-issue"
  | "grant-revoke"
  | "effect-approve";

export interface ChallengeRecord {
  readonly challengeId: string;
  readonly purpose: ChallengePurpose;
  readonly principalId: string;
  readonly challenge: string;
  readonly payloadDigest: string;
  readonly payload: unknown;
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

export type RiskClass = "R0" | "R1" | "R2" | "R3" | "R4" | "R5";

export interface VerifiedAgent {
  readonly agentId: string;
  readonly clientId: string;
  readonly subject: string;
}

export interface AgentGrantCreate {
  readonly grantId: string;
  readonly principalId: string;
  readonly agentId: string;
  readonly audience: string;
  readonly allowedActions: readonly string[];
  readonly resourcePrefixes: readonly string[];
  readonly expiresAtEpochSeconds: number;
  readonly maxRiskClass: RiskClass;
  readonly stepUpAtOrAbove: RiskClass;
  readonly remainingEffects: number;
}

export interface AgentGrantSnapshot extends AgentGrantCreate {
  readonly grantDigest: string;
  readonly active: boolean;
  readonly revision: number;
}

export interface AgentEffectRequest {
  readonly effectId: string;
  readonly effectDigest: string;
  readonly action: string;
  readonly resource: string;
  readonly audience: string;
  readonly riskClass: RiskClass;
  readonly effectType: string;
}

export interface VerifiedApproval {
  readonly verified: boolean;
  readonly principalId: string | null;
  readonly effectId: string | null;
  readonly method: "webauthn" | null;
}

export interface AgentAdmissionInput {
  readonly schemaVersion: 1;
  readonly nowEpochSeconds: number;
  readonly principal: {
    readonly principalId: string;
    readonly authenticated: true;
    readonly authnMethod: "webauthn";
  };
  readonly agent: {
    readonly agentId: string;
    readonly authenticated: true;
    readonly credentialKind: "dpop-key";
  };
  readonly grant: {
    readonly grantId: string;
    readonly grantDigest: string;
    readonly active: boolean;
    readonly principalId: string;
    readonly agentId: string;
    readonly audience: string;
    readonly allowedActions: readonly string[];
    readonly resourcePrefixes: readonly string[];
    readonly expiresAtEpochSeconds: number;
    readonly maxRiskClass: RiskClass;
    readonly stepUpAtOrAbove: RiskClass;
    readonly remainingEffects: number;
  };
  readonly effect: AgentEffectRequest;
  readonly approval: VerifiedApproval;
}

export interface AgentAdmissionDecision {
  readonly outcome: "ALLOW" | "STEP_UP" | "DENY";
  readonly reason: string;
  readonly authorityProjection: Record<string, unknown> | null;
}

export interface AdmissionChainDecision {
  readonly schemaVersion: 1;
  readonly kind: "ordivon.security.agent-admission-chain";
  readonly agent: AgentAdmissionDecision;
  readonly effect:
    | {
        readonly admitted: boolean;
        readonly reason: string;
      }
    | null;
}

export interface AgentEffectReceipt {
  readonly effectId: string;
  readonly effectDigest: string;
  readonly principalId: string;
  readonly agentId: string;
  readonly grantId: string;
  readonly action: string;
  readonly resource: string;
  readonly result: unknown;
  readonly committedAt: number;
}
