export type ProviderAdapterErrorCode =
  | "unavailable"
  | "timeout"
  | "process_failed"
  | "invalid_output"
  | "invalid_usage";

export class ProviderAdapterError extends Error {
  readonly code: ProviderAdapterErrorCode;

  constructor(code: ProviderAdapterErrorCode, message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "ProviderAdapterError";
    this.code = code;
  }
}
