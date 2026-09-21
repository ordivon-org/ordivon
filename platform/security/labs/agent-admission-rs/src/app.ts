import { createHash } from "node:crypto";

import { asAdmissionLabError, AdmissionLabError } from "./errors.ts";
import type { GrantStore } from "./grant-store.ts";
import type {
  AgentAdmissionInput,
  EffectRequest,
  GrantSnapshot,
  RiskClass,
  VerifiedApproval,
} from "./model.ts";
import type { AgentVerifier } from "./oauth-verifier.ts";
import type { OpaAdmissionEngine } from "./opa.ts";

const EFFECT_ID = /^sha256:[0-9a-f]{64}$/;
const MAX_BODY_BYTES = 8192;

interface AppDependencies {
  readonly verifier: AgentVerifier;
  readonly store: GrantStore;
  readonly policy: OpaAdmissionEngine;
  readonly audience: string;
  readonly now?: () => number;
  readonly approval?: (
    effect: EffectRequest,
    principalId: string,
  ) => Promise<VerifiedApproval> | VerifiedApproval;
  readonly onStepUp?: (
    effect: EffectRequest,
    principalId: string,
  ) => Promise<void> | void;
  readonly consumeApproval?: (
    effect: EffectRequest,
    principalId: string,
  ) => Promise<void> | void;
}

function json(value: unknown, status = 200): Response {
  return new Response(JSON.stringify(value), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

async function readJsonObject(request: Request): Promise<Record<string, unknown>> {
  const bytes = new Uint8Array(await request.arrayBuffer());
  if (bytes.byteLength === 0 || bytes.byteLength > MAX_BODY_BYTES) {
    throw new AdmissionLabError("invalid_body", "Request body size is invalid.", 422);
  }
  let value: unknown;
  try {
    value = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch {
    throw new AdmissionLabError("invalid_json", "Request body must be UTF-8 JSON.", 400);
  }
  if (value === null || Array.isArray(value) || typeof value !== "object") {
    throw new AdmissionLabError(
      "invalid_body",
      "Request body must be a JSON object.",
      422,
    );
  }
  return value as Record<string, unknown>;
}

function requireEffectId(request: Request): string {
  const value = request.headers.get("x-ordivon-effect-id") ?? "";
  if (!EFFECT_ID.test(value)) {
    throw new AdmissionLabError(
      "invalid_effect_id",
      "X-Ordivon-Effect-Id must be a sha256-prefixed 64-hex identity.",
      400,
    );
  }
  return value;
}

function effectDigest(
  id: string,
  action: string,
  resource: string,
  body: Record<string, unknown>,
): string {
  const digest = createHash("sha256")
    .update(JSON.stringify({ id, action, resource, body }))
    .digest("hex");
  return `sha256:${digest}`;
}

async function noApproval(): Promise<VerifiedApproval> {
  return { verified: false, principalId: null, effectId: null, method: null };
}

function admissionInput(
  grant: GrantSnapshot,
  agentId: string,
  effect: EffectRequest,
  approval: VerifiedApproval,
  nowEpochSeconds: number,
): AgentAdmissionInput {
  return {
    schemaVersion: 1,
    nowEpochSeconds,
    principal: {
      principalId: grant.principalId,
      authenticated: true,
      authnMethod: "federated",
    },
    agent: {
      agentId,
      authenticated: true,
      credentialKind: "dpop-key",
    },
    grant: {
      grantId: grant.grantId,
      grantDigest: grant.grantDigest,
      active: grant.active,
      principalId: grant.principalId,
      agentId: grant.agentId,
      audience: grant.audience,
      allowedActions: grant.allowedActions,
      resourcePrefixes: grant.resourcePrefixes,
      expiresAtEpochSeconds: grant.expiresAtEpochSeconds,
      maxRiskClass: grant.maxRiskClass,
      stepUpAtOrAbove: grant.stepUpAtOrAbove,
      remainingEffects: grant.remainingEffects,
    },
    effect,
    approval,
  };
}

function commentRoute(url: URL): { articleId: string; resource: string } | null {
  const match = /^\/api\/articles\/([A-Za-z0-9._-]{1,128})\/comments$/.exec(
    url.pathname,
  );
  if (match === null) return null;
  const articleId = match[1]!;
  return { articleId, resource: `/comments/${articleId}` };
}

function createEffect(
  id: string,
  action: string,
  resource: string,
  riskClass: RiskClass,
  effectType: string,
  audience: string,
  body: Record<string, unknown>,
): EffectRequest {
  return {
    effectId: id,
    effectDigest: effectDigest(id, action, resource, body),
    action,
    resource,
    audience,
    riskClass,
    effectType,
  };
}

async function evaluateWithFreshGrant(
  dependencies: AppDependencies,
  agentId: string,
  effect: EffectRequest,
  nowEpochSeconds: number,
) {
  const grant = dependencies.store.resolveUniqueGrant(
    agentId,
    dependencies.audience,
    effect.action,
    effect.resource,
    nowEpochSeconds,
  );
  const approval =
    dependencies.approval === undefined
      ? await noApproval()
      : await dependencies.approval(effect, grant.principalId);
  const decision = await dependencies.policy.evaluate(
    admissionInput(grant, agentId, effect, approval, nowEpochSeconds),
  );
  return { grant, decision };
}

export function createAgentAdmissionApp(dependencies: AppDependencies) {
  return async function handle(request: Request): Promise<Response> {
    try {
      const url = new URL(request.url);
      if (request.method === "GET" && url.pathname === "/health") {
        return json({ status: "ok", kind: "agent-admission-rs-lab" });
      }

      const comment = commentRoute(url);
      if (request.method === "POST" && comment !== null) {
        const agent = await dependencies.verifier.verify(request);
        const body = await readJsonObject(request);
        const content = body.content;
        if (typeof content !== "string" || content.length < 1 || content.length > 2000) {
          throw new AdmissionLabError("invalid_comment", "content is invalid.", 422);
        }

        const id = requireEffectId(request);
        const nowEpochSeconds = dependencies.now?.() ?? Math.floor(Date.now() / 1000);
        const effect = createEffect(
          id,
          "comment.create",
          comment.resource,
          "R2",
          "website.comment.create",
          dependencies.audience,
          body,
        );

        const historical = dependencies.store.lookupCommittedEffect(
          effect.effectId,
          effect.effectDigest,
          agent.agentId,
        );
        if (historical !== null) {
          return json({ outcome: "ALLOW", replayed: true, receipt: historical }, 200);
        }

        for (let attempt = 0; attempt < 2; attempt += 1) {
          const { grant, decision } = await evaluateWithFreshGrant(
            dependencies,
            agent.agentId,
            effect,
            nowEpochSeconds,
          );

          if (decision.agent.outcome === "DENY") {
            return json(
              {
                outcome: "DENY",
                reason: decision.agent.reason,
                effectId: effect.effectId,
              },
              403,
            );
          }
          if (decision.agent.outcome === "STEP_UP") {
            await dependencies.onStepUp?.(effect, grant.principalId);
            return json(
              {
                outcome: "STEP_UP",
                reason: decision.agent.reason,
                effectId: effect.effectId,
                effectDigest: effect.effectDigest,
              },
              428,
            );
          }

          try {
            const committed = dependencies.store.commitComment(
              grant,
              effect,
              comment.articleId,
              content,
              nowEpochSeconds,
            );
            return json(
              {
                outcome: "ALLOW",
                replayed: committed.replayed,
                receipt: committed.receipt,
              },
              committed.replayed ? 200 : 201,
            );
          } catch (error) {
            if (
              error instanceof AdmissionLabError &&
              error.code === "grant_changed" &&
              attempt === 0
            ) {
              continue;
            }
            throw error;
          }
        }
      }

      if (request.method === "POST" && url.pathname === "/api/publish-probe") {
        const agent = await dependencies.verifier.verify(request);
        const body = await readJsonObject(request);
        const id = requireEffectId(request);
        const nowEpochSeconds = dependencies.now?.() ?? Math.floor(Date.now() / 1000);
        const effect = createEffect(
          id,
          "site.publish",
          "/site/publish",
          "R4",
          "website.site.publish",
          dependencies.audience,
          body,
        );
        const { grant, decision } = await evaluateWithFreshGrant(
          dependencies,
          agent.agentId,
          effect,
          nowEpochSeconds,
        );
        if (decision.agent.outcome === "STEP_UP") {
          await dependencies.onStepUp?.(effect, grant.principalId);
          return json(
            {
              outcome: "STEP_UP",
              reason: decision.agent.reason,
              effectId: effect.effectId,
              effectDigest: effect.effectDigest,
            },
            428,
          );
        }
        if (decision.agent.outcome === "DENY") {
          return json(
            {
              outcome: "DENY",
              reason: decision.agent.reason,
              effectId: effect.effectId,
            },
            403,
          );
        }
        await dependencies.consumeApproval?.(effect, grant.principalId);
        return json(
          {
            outcome: "ALLOW",
            reason: decision.agent.reason,
            effectId: effect.effectId,
          },
          200,
        );
      }

      return json({ error: "not_found" }, 404);
    } catch (error) {
      const normalized = asAdmissionLabError(error);
      return json(
        { error: normalized.code, message: normalized.message },
        normalized.httpStatus,
      );
    }
  };
}
