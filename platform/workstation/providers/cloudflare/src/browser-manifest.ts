import type {
  ArtifactReference,
  BrowserReceiptDetails,
  EdgeExecutionMetadata
} from "./contracts.js";

export const BROWSER_MANIFEST_SCHEMA_VERSION = 2 as const;

export interface BrowserManifestDocument {
  readonly schema_version: typeof BROWSER_MANIFEST_SCHEMA_VERSION;
  readonly receipt_id: string;
  readonly execution: EdgeExecutionMetadata;
  readonly browser: BrowserReceiptDetails;
  readonly artifacts: readonly [ArtifactReference, ArtifactReference];
}

export interface BrowserManifestOptions {
  readonly receiptId: string;
  readonly execution: EdgeExecutionMetadata;
  readonly browser: BrowserReceiptDetails;
  readonly screenshot: ArtifactReference;
  readonly content: ArtifactReference;
}

export function createBrowserManifest(
  options: BrowserManifestOptions
): BrowserManifestDocument {
  return {
    schema_version: BROWSER_MANIFEST_SCHEMA_VERSION,
    receipt_id: options.receiptId,
    execution: {
      policy_version: options.execution.policy_version,
      capability_version: options.execution.capability_version,
      worker_version_id: options.execution.worker_version_id,
      worker_version_tag: options.execution.worker_version_tag,
      worker_version_timestamp: options.execution.worker_version_timestamp,
      lease_generation: options.execution.lease_generation
    },
    browser: {
      requested_url: options.browser.requested_url,
      final_url_observed: options.browser.final_url_observed,
      ...(options.browser.final_url === undefined
        ? {}
        : { final_url: options.browser.final_url }),
      page_title: options.browser.page_title,
      page_status: options.browser.page_status,
      browser_ms: options.browser.browser_ms,
      viewport: {
        width: options.browser.viewport.width,
        height: options.browser.viewport.height
      },
      full_page: options.browser.full_page
    },
    artifacts: [options.screenshot, options.content]
  };
}
