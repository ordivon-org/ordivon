import { EdgeError } from "./errors.js";
import { BROWSER_POLICY } from "./policy.js";
import {
  validateExternalUrl,
  type FetchPolicyEnvironment
} from "./fetch-policy.js";

const ALLOWED_FIELDS = new Set([
  "url",
  "viewport_width",
  "viewport_height",
  "full_page",
  "wait_until",
  "timeout_ms",
  "wait_after_ms"
]);
const WAIT_UNTIL_VALUES = new Set<BrowserRunLifecycleEvent>(
  BROWSER_POLICY.wait_until as BrowserRunLifecycleEvent[]
);

export interface ValidatedBrowserRunRequest {
  readonly url: URL;
  readonly viewport: {
    readonly width: number;
    readonly height: number;
  };
  readonly fullPage: boolean;
  readonly waitUntil: BrowserRunLifecycleEvent;
  readonly timeoutMs: number;
  readonly waitAfterMs: number;
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

export function validateBrowserRunRequest(
  value: Record<string, unknown>,
  environment: FetchPolicyEnvironment
): ValidatedBrowserRunRequest {
  for (const field of Object.keys(value)) {
    if (!ALLOWED_FIELDS.has(field)) {
      throw new EdgeError("unsupported_browser_option", 422, `Browser option ${field} is not supported.`);
    }
  }
  if (typeof value.url !== "string") {
    throw new EdgeError("invalid_request", 422, "url must be a string.");
  }
  if (value.full_page !== undefined && typeof value.full_page !== "boolean") {
    throw new EdgeError("invalid_request", 422, "full_page must be a boolean.");
  }
  const waitUntil = value.wait_until ?? "domcontentloaded";
  if (typeof waitUntil !== "string" || !WAIT_UNTIL_VALUES.has(waitUntil as BrowserRunLifecycleEvent)) {
    throw new EdgeError("invalid_request", 422, "wait_until is not supported.");
  }

  return {
    url: validateExternalUrl(value.url, environment),
    viewport: {
      width: boundedInteger(
        value.viewport_width,
        BROWSER_POLICY.viewport.default_width,
        BROWSER_POLICY.viewport.min_width,
        BROWSER_POLICY.viewport.max_width,
        "viewport_width"
      ),
      height: boundedInteger(
        value.viewport_height,
        BROWSER_POLICY.viewport.default_height,
        BROWSER_POLICY.viewport.min_height,
        BROWSER_POLICY.viewport.max_height,
        "viewport_height"
      )
    },
    fullPage: value.full_page ?? false,
    waitUntil: waitUntil as BrowserRunLifecycleEvent,
    timeoutMs: boundedInteger(
      value.timeout_ms,
      BROWSER_POLICY.timeout.default_ms,
      BROWSER_POLICY.timeout.min_ms,
      BROWSER_POLICY.timeout.max_ms,
      "timeout_ms"
    ),
    waitAfterMs: boundedInteger(
      value.wait_after_ms,
      BROWSER_POLICY.wait_after.default_ms,
      BROWSER_POLICY.wait_after.min_ms,
      BROWSER_POLICY.wait_after.max_ms,
      "wait_after_ms"
    )
  };
}

function escapeRegularExpression(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function browserRunOptions(
  request: ValidatedBrowserRunRequest
): BrowserRunSnapshotOptions {
  const originPattern = `^https://${escapeRegularExpression(request.url.hostname)}(?::443)?(?:/|$)`;
  return {
    url: request.url.toString(),
    viewport: request.viewport,
    gotoOptions: {
      timeout: request.timeoutMs,
      waitUntil: request.waitUntil
    },
    waitForTimeout: request.waitAfterMs,
    actionTimeout: Math.min(
      BROWSER_POLICY.action_timeout_max_ms,
      request.timeoutMs +
        request.waitAfterMs +
        BROWSER_POLICY.action_timeout_overhead_ms
    ),
    cacheTTL: 0,
    setJavaScriptEnabled: true,
    allowRequestPattern: [originPattern],
    rejectResourceTypes: [...BROWSER_POLICY.rejected_resource_types] as BrowserRunResourceType[],
    screenshotOptions: {
      type: "png",
      fullPage: request.fullPage,
      optimizeForSpeed: true
    }
  };
}
