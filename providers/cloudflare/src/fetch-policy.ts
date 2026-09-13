import { EdgeError } from "./errors.js";
import { FETCH_POLICY } from "./policy.js";

const ALLOWED_FIELDS = new Set(["url", "maximum_bytes", "timeout_ms", "accept"]);

const {
  max_url_bytes: MAX_URL_BYTES,
  max_response_bytes: MAX_RESPONSE_BYTES,
  default_response_bytes: DEFAULT_RESPONSE_BYTES,
  min_timeout_ms: MIN_TIMEOUT_MS,
  max_timeout_ms: MAX_TIMEOUT_MS,
  default_timeout_ms: DEFAULT_TIMEOUT_MS,
  max_accept_bytes: MAX_ACCEPT_BYTES,
  forbidden_host_suffixes: FORBIDDEN_HOST_SUFFIXES
} = FETCH_POLICY;

export interface FetchPolicyEnvironment {
  readonly FETCH_ALLOWED_HOSTS: string;
}

export interface ValidatedFetchRequest {
  readonly url: URL;
  readonly maximumBytes: number;
  readonly timeoutMs: number;
  readonly accept: string;
}

function boundedInteger(
  value: unknown,
  defaultValue: number,
  minimum: number,
  maximum: number,
  field: string
): number {
  if (value === undefined) {
    return defaultValue;
  }
  if (!Number.isSafeInteger(value) || (value as number) < minimum || (value as number) > maximum) {
    throw new EdgeError("invalid_request", 422, `${field} is outside the allowed range.`);
  }
  return value as number;
}

function normalizeHostname(hostname: string): string {
  return hostname.toLowerCase().replace(/\.$/, "");
}

function isIpLiteral(hostname: string): boolean {
  const candidate = hostname.replace(/^\[/, "").replace(/\]$/, "");
  return candidate.includes(":") || /^[0-9.]+$/.test(candidate);
}

function parseAllowedHosts(value: string): string[] {
  const hosts = value
    .split(",")
    .map((host) => normalizeHostname(host.trim()))
    .filter((host) => host.length > 0);
  if (hosts.length === 0) {
    throw new EdgeError("fetch_unavailable", 503, "No external fetch hosts are configured.", "failed");
  }
  for (const host of hosts) {
    if (host.startsWith("*.")) {
      throw new EdgeError(
        "fetch_unavailable",
        503,
        "Wildcard external fetch hosts are not supported.",
        "failed"
      );
    }
  }
  return hosts;
}

function hostnameAllowed(hostname: string, patterns: readonly string[]): boolean {
  return patterns.includes(hostname);
}

export function validateExternalUrl(
  input: string,
  environment: FetchPolicyEnvironment
): URL {
  if (new TextEncoder().encode(input).byteLength > MAX_URL_BYTES) {
    throw new EdgeError("invalid_url", 422, "The external URL is too long.");
  }
  let url: URL;
  try {
    url = new URL(input);
  } catch {
    throw new EdgeError("invalid_url", 422, "The external URL is invalid.");
  }
  if (url.protocol !== FETCH_POLICY.allowed_scheme) {
    throw new EdgeError("unsupported_scheme", 422, "Only HTTPS external URLs are allowed.");
  }
  if (url.username !== "" || url.password !== "") {
    throw new EdgeError("url_credentials_forbidden", 422, "Credentials in external URLs are forbidden.");
  }
  if (url.port !== "" && url.port !== FETCH_POLICY.allowed_port) {
    throw new EdgeError("unsafe_port", 422, "Only the standard HTTPS port is allowed.");
  }
  const hostname = normalizeHostname(url.hostname);
  if (
    hostname.length === 0 ||
    isIpLiteral(hostname) ||
    !/^[a-z0-9.-]+$/.test(hostname) ||
    hostname.includes("..") ||
    FORBIDDEN_HOST_SUFFIXES.some((suffix) => hostname === suffix.slice(1) || hostname.endsWith(suffix))
  ) {
    throw new EdgeError("unsafe_host", 422, "The external hostname is not allowed.");
  }
  if (!hostnameAllowed(hostname, parseAllowedHosts(environment.FETCH_ALLOWED_HOSTS))) {
    throw new EdgeError("host_not_allowed", 403, "The external hostname is outside the configured allowlist.");
  }
  url.hostname = hostname;
  url.hash = "";
  return url;
}

export function validateFetchRequest(
  value: Record<string, unknown>,
  environment: FetchPolicyEnvironment
): ValidatedFetchRequest {
  for (const field of Object.keys(value)) {
    if (!ALLOWED_FIELDS.has(field)) {
      throw new EdgeError(
        "unsupported_fetch_option",
        422,
        `Fetch option ${field} is not supported.`
      );
    }
  }
  if (typeof value.url !== "string") {
    throw new EdgeError("invalid_request", 422, "url must be a string.");
  }
  const accept = value.accept === undefined ? "*/*" : value.accept;
  if (
    typeof accept !== "string" ||
    new TextEncoder().encode(accept).byteLength > MAX_ACCEPT_BYTES ||
    /[\r\n\0]/.test(accept)
  ) {
    throw new EdgeError("invalid_request", 422, "accept is invalid.");
  }
  return {
    url: validateExternalUrl(value.url, environment),
    maximumBytes: boundedInteger(
      value.maximum_bytes,
      DEFAULT_RESPONSE_BYTES,
      1,
      MAX_RESPONSE_BYTES,
      "maximum_bytes"
    ),
    timeoutMs: boundedInteger(
      value.timeout_ms,
      DEFAULT_TIMEOUT_MS,
      MIN_TIMEOUT_MS,
      MAX_TIMEOUT_MS,
      "timeout_ms"
    ),
    accept
  };
}
