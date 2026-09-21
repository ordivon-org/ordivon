import { AdmissionLabError } from "./errors.ts";
import { GrantStore } from "./grant-store.ts";

const databasePath =
  process.env.AGENT_ADMISSION_DB ??
  new URL("../.agent-admission-lab.sqlite3", import.meta.url).pathname;
const audience =
  process.env.AGENT_ADMISSION_AUDIENCE ?? "http://127.0.0.1:8788";
const store = new GrantStore(databasePath);
const now = Math.floor(Date.now() / 1000);

function ensureGrant(
  grantId: string,
  create: () => Parameters<GrantStore["createGrant"]>[0],
): void {
  try {
    store.getGrant(grantId);
  } catch (error) {
    if (!(error instanceof AdmissionLabError) || error.code !== "grant_not_found") {
      throw error;
    }
    store.createGrant(create());
  }
}

ensureGrant("grant:research-comment-v1", () => ({
  grantId: "grant:research-comment-v1",
  principalId: "principal:lab-owner",
  agentId: "oauth-client:agent-research-17",
  audience,
  allowedActions: ["comment.create"],
  resourcePrefixes: ["/comments/"],
  expiresAtEpochSeconds: now + 86400,
  maxRiskClass: "R3",
  stepUpAtOrAbove: "R4",
  remainingEffects: 5,
}));

ensureGrant("grant:research-publish-probe-v1", () => ({
  grantId: "grant:research-publish-probe-v1",
  principalId: "principal:lab-owner",
  agentId: "oauth-client:agent-research-17",
  audience,
  allowedActions: ["site.publish"],
  resourcePrefixes: ["/site/"],
  expiresAtEpochSeconds: now + 86400,
  maxRiskClass: "R4",
  stepUpAtOrAbove: "R4",
  remainingEffects: 1,
}));

console.log(
  JSON.stringify({
    comment: store.getGrant("grant:research-comment-v1"),
    publishProbe: store.getGrant("grant:research-publish-probe-v1"),
  }),
);
store.close();
