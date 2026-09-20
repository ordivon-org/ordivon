import policy from "../config/edge-policy.json";

export const EDGE_POLICY = policy;
export const EDGE_POLICY_FAMILY = policy.family;
export const RETENTION_POLICY = policy.retention_days;
export const REQUEST_POLICY = policy.request;
export const FETCH_POLICY = policy.fetch;
export const BROWSER_POLICY = policy.browser;
export const LEASE_POLICY = policy.leases_ms;
export const RATE_LIMIT_POLICY = policy.rate_limits;

export interface PolicyEnvironment {
  readonly FETCH_ALLOWED_HOSTS: string;
}

function normalizeAllowedHosts(value: string): string[] {
  return value
    .split(",")
    .map((host) => host.trim().toLowerCase().replace(/\.$/, ""))
    .filter((host) => host.length > 0)
    .sort();
}

let cachedPolicyInput: string | undefined;
let cachedPolicyVersion: Promise<string> | undefined;

export function effectivePolicyVersion(
  environment: PolicyEnvironment
): Promise<string> {
  const input = JSON.stringify({
    policy: EDGE_POLICY,
    effective_fetch_allowed_hosts: normalizeAllowedHosts(
      environment.FETCH_ALLOWED_HOSTS
    )
  });
  if (input !== cachedPolicyInput || cachedPolicyVersion === undefined) {
    cachedPolicyInput = input;
    cachedPolicyVersion = crypto.subtle
      .digest("SHA-256", new TextEncoder().encode(input))
      .then((digest) => {
        const hex = [...new Uint8Array(digest)]
          .map((byte) => byte.toString(16).padStart(2, "0"))
          .join("");
        return `${EDGE_POLICY_FAMILY}.${hex.slice(0, 16)}`;
      });
  }
  return cachedPolicyVersion;
}
