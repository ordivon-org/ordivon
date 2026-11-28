import type { AgentGrantSnapshot, Principal } from "./model.ts";

type GrantAvailability = "revoked" | "expired" | "exhausted" | "candidate";

function availability(grant: AgentGrantSnapshot, observedAt: number): GrantAvailability {
  if (!grant.active) return "revoked";
  if (grant.expiresAtEpochSeconds <= observedAt) return "expired";
  if (grant.remainingEffects <= 0) return "exhausted";
  return "candidate";
}

const labels: Record<GrantAvailability, string> = {
  revoked: "Revoked",
  expired: "Expired",
  exhausted: "Quota exhausted",
  candidate: "Candidate (not an admission decision)",
};

function html(value: string | number): string {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]!);
}

function time(value: number): string {
  const iso = new Date(value * 1000).toISOString();
  return '<time datetime="' + html(iso) + '">' + html(iso) + '</time>';
}

// Same-owner, synchronous read-only projection. Grant availability is not an
// authorization decision: actual admission still checks request, scope, risk,
// approval and current mutable authority at the point of execution.
export function renderOperatorGrants(
  principal: Principal,
  grants: readonly AgentGrantSnapshot[],
  observedAt: number,
): string {
  const rows = grants.map((grant) => {
    const status = availability(grant, observedAt);
    return '<tr><th scope="row">' + html(grant.grantId) +
      '</th><td>' + html(grant.agentId) +
      '</td><td data-availability="' + status + '">' + labels[status] +
      '</td><td>' + html(grant.remainingEffects) +
      '</td><td>' + html(grant.revision) +
      '</td><td>' + time(grant.expiresAtEpochSeconds) +
      '</td><td>' + html(grant.allowedActions.join(", ")) +
      '</td><td>' + html(grant.resourcePrefixes.join(", ")) + '</td></tr>';
  }).join("");
  return '<!doctype html><html lang="en"><head><meta charset="utf-8">' +
    '<meta name="viewport" content="width=device-width, initial-scale=1">' +
    '<title>Agent grants | Ordivon</title></head><body><main>' +
    '<h1>Agent grants</h1><p>Signed in as <strong>' + html(principal.displayName) +
    '</strong></p><p>Owner observation: ' + time(observedAt) + '</p>' +
    '<p>Read-only snapshot. A candidate grant is not permission to execute an action. ' +
    'The current request must still pass Security admission and the Owner commit fence.</p>' +
    '<p><a href="/operator/grants">Refresh owner observation</a></p>' +
    '<table><caption>Grants belonging to the current principal</caption>' +
    '<thead><tr><th scope="col">Grant</th><th scope="col">Agent</th>' +
    '<th scope="col">Availability</th><th scope="col">Remaining effects</th>' +
    '<th scope="col">Revision</th><th scope="col">Expires (UTC)</th>' +
    '<th scope="col">Actions</th><th scope="col">Resource scopes</th></tr></thead>' +
    '<tbody>' + rows + '</tbody></table>' +
    (grants.length === 0 ? '<p>No grants for this principal.</p>' : '') +
    '</main></body></html>';
}
