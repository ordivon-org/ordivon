export type RiskClass = "R0" | "R1" | "R2" | "R3" | "R4" | "R5";

export interface GrantCreate {
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

export interface GrantSnapshot extends GrantCreate {
  readonly grantDigest: string;
  readonly active: boolean;
  readonly revision: number;
}

export interface EffectRequest {
  readonly effectId: string;
  readonly effectDigest: string;
  readonly action: string;
  readonly resource: string;
  readonly audience: string;
  readonly riskClass: RiskClass;
  readonly effectType: string;
}

export interface VerifiedAgent {
  readonly agentId: string;
  readonly clientId: string;
  readonly subject: string;
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
    readonly authnMethod: "webauthn" | "session" | "federated";
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
  readonly effect: EffectRequest;
  readonly approval: VerifiedApproval;
}

export interface AuthorityProjection {
  readonly requestId: string;
  readonly requestDigest: string;
  readonly actorId: string;
  readonly authorityId: string;
  readonly authorityDigest: string;
  readonly zoneRef: string;
  readonly capability: string;
  readonly effectType: string;
}

export interface AgentAdmissionDecision {
  readonly schemaVersion: 1;
  readonly kind: "ordivon.security.agent-admission";
  readonly principalId: string;
  readonly agentId: string;
  readonly grantId: string;
  readonly effectId: string;
  readonly outcome: "ALLOW" | "STEP_UP" | "DENY";
  readonly reason: string;
  readonly authorityProjection: AuthorityProjection | null;
}

export interface EffectAdmissionDecision {
  readonly schemaVersion: 1;
  readonly kind: "ordivon.security.range-effect-admission";
  readonly requestId: string;
  readonly requestDigest: string;
  readonly actorId: string;
  readonly authorityId: string;
  readonly authorityDigest: string | null;
  readonly zoneRef: string;
  readonly capability: string;
  readonly effectType: string;
  readonly admitted: boolean;
  readonly reason: string;
}

export interface AdmissionChainDecision {
  readonly agent: AgentAdmissionDecision;
  readonly effect: EffectAdmissionDecision | null;
}

export interface CommentReceipt {
  readonly commentId: string;
  readonly articleId: string;
  readonly content: string;
  readonly principalId: string;
  readonly agentId: string;
  readonly effectId: string;
}
