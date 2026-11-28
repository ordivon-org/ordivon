import type { FastifyInstance, FastifyReply, FastifyRequest } from "fastify";
import type { WebConfig } from "./config.ts";
import { WebProblem } from "./errors.ts";
import { stableDigest } from "./identity-digests.ts";
import { admissionInput, type AgentAdmissionEvaluator, type AgentRequestVerifier } from "./agent-authority.ts";
import type { AgentEffectRequest, AgentEffectReceipt, AgentGrantSnapshot, VerifiedAgent } from "./model.ts";
import { asBody, requireString, textHeader } from "./browser-request-boundary.ts";
import type { WebStore } from "./store.ts";

interface AgentCanaryRouteDependencies {
  readonly config: WebConfig;
  readonly store: WebStore;
  readonly now: () => number;
  readonly agentVerifier: AgentRequestVerifier | undefined;
  readonly agentAdmission: AgentAdmissionEvaluator;
}

type CommittedEffect = { receipt: AgentEffectReceipt; replayed: boolean };

// HTTP admission and receipt projection, not a new authority. Security evaluates
// the current request; WebStore retains the concrete transactional commit fence.
export function registerAgentCanaryRoutes(
  app: FastifyInstance,
  dependencies: AgentCanaryRouteDependencies,
): void {
  const { config, store, now, agentAdmission } = dependencies;

  async function verifiedAgent(request: FastifyRequest): Promise<VerifiedAgent> {
    if (dependencies.agentVerifier === undefined) {
      throw new WebProblem(
        503,
        "agent-verifier-unavailable",
        "Agent verification unavailable",
        "The Security-owned Agent request verifier is not configured.",
      );
    }
    return await dependencies.agentVerifier.verify({
      method: request.method,
      url: request.url,
      headers: request.headers,
    });
  }

  function effectId(request: FastifyRequest): string {
    const value = textHeader(request.headers["x-ordivon-effect-id"]);
    if (value === null || !/^sha256:[0-9a-f]{64}$/.test(value)) {
      throw new WebProblem(
        422,
        "effect-id-invalid",
        "Invalid Effect identity",
        "Agent mutations require X-Ordivon-Effect-Id as sha256:<64 lowercase hex>.",
      );
    }
    return value;
  }

  async function executeEffect(
    request: FastifyRequest,
    reply: FastifyReply,
    agent: VerifiedAgent,
    effect: AgentEffectRequest,
    approvalDetail: string,
    freshStatus: 200 | 201,
    commit: (grant: AgentGrantSnapshot) => CommittedEffect,
  ) {
    const timestamp = now();
    const replay = store.resolveAgentEffectReplay(agent.agentId, effect);
    if (replay !== null) {
      return reply.code(200).send({ receipt: replay, replayed: true });
    }
    const grant = store.resolveAgentGrant(
      agent.agentId, config.origin, effect.action, effect.resource, timestamp,
    );
    const approval = store.effectApproval(grant.principalId, effect, timestamp);
    const decision = await agentAdmission.evaluate(
      admissionInput(timestamp, grant, agent, effect, approval),
    );
    // Admission is asynchronous. A committed exact replay takes precedence
    // over an obsolete decision (including STEP_UP); never ask for approval
    // for an already committed effect.
    const lateReplay = store.resolveAgentEffectReplay(agent.agentId, effect);
    if (lateReplay !== null) {
      return reply.code(200).send({ receipt: lateReplay, replayed: true });
    }
    const requiresApproval = decision.agent.outcome === "STEP_UP";
    const allowed = decision.agent.outcome === "ALLOW" && decision.effect?.admitted === true;
    if (requiresApproval || allowed) {
      // Re-resolve the unique grant at the point of use; an intervening
      // revocation, expiry, ambiguity or revision invalidates admission.
      const current = store.resolveAgentGrant(
        agent.agentId, config.origin, effect.action, effect.resource, now(),
      );
      if (
        current.grantId !== grant.grantId ||
        current.grantDigest !== grant.grantDigest ||
        current.revision !== grant.revision
      ) {
        throw new WebProblem(
          409, "agent-grant-changed", "Agent Grant changed",
          "Mutable Agent authority changed after admission; retry with current authority.",
        );
      }
    }
    if (requiresApproval) {
      store.registerPendingEffectApproval(grant.principalId, effect, now());
      return reply.code(428).type("application/problem+json").send({
        type: config.origin + "/problems/principal-step-up-required",
        title: "Principal approval required",
        status: 428,
        detail: approvalDetail,
        effectId: effect.effectId,
        effectDigest: effect.effectDigest,
        requestId: request.id,
      });
    }
    if (!allowed) {
      throw new WebProblem(
        403, "agent-effect-denied", "Agent Effect denied", decision.agent.reason,
      );
    }
    const committed = commit(grant);
    return reply.code(committed.replayed ? 200 : freshStatus).send(committed);
  }

  app.post("/api/agent/canary/notes", async (request, reply) => {
    const agent = await verifiedAgent(request);
    const body = asBody(request);
    const content = requireString(body, "content", 2000);
    const resource = "/canary/notes";
    const effect: AgentEffectRequest = {
      effectId: effectId(request),
      effectDigest: stableDigest({
        action: "canary.note.create",
        resource,
        content,
      }),
      action: "canary.note.create",
      resource,
      audience: config.origin,
      riskClass: "R2",
      effectType: "website.canary.note.create",
    };
    return executeEffect(
      request, reply, agent, effect,
      "This Agent Effect requires effect-bound Principal approval.",
      201,
      (grant) => store.commitAgentCanaryCreate(grant, agent.agentId, effect, content, now()),
    );
  });

  app.post(
    "/api/agent/canary/notes/:noteId/publish",
    async (request, reply) => {
      const agent = await verifiedAgent(request);
      const params = request.params as { noteId?: unknown };
      if (typeof params.noteId !== "string" || params.noteId.length < 1) {
        throw new WebProblem(
          422,
          "invalid-note-id",
          "Invalid canary note",
          "noteId is required.",
        );
      }
      const noteId = params.noteId;
      const resource = "/canary/notes/" + noteId;
      const effect: AgentEffectRequest = {
        effectId: effectId(request),
        effectDigest: stableDigest({
          action: "canary.note.publish",
          resource,
          noteId,
        }),
        action: "canary.note.publish",
        resource,
        audience: config.origin,
        riskClass: "R4",
        effectType: "website.canary.note.publish",
      };
      return executeEffect(
        request, reply, agent, effect,
        "Publishing this canary note requires effect-bound Principal approval.",
        200,
        (grant) => store.commitAgentCanaryPublish(grant, agent.agentId, effect, noteId, now()),
      );
    },
  );

}
