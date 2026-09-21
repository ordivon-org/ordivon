export class AdmissionLabError extends Error {
  readonly code: string;
  readonly httpStatus: number;

  constructor(code: string, message: string, httpStatus: number) {
    super(message);
    this.name = "AdmissionLabError";
    this.code = code;
    this.httpStatus = httpStatus;
  }
}

export function asAdmissionLabError(error: unknown): AdmissionLabError {
  if (error instanceof AdmissionLabError) return error;
  return new AdmissionLabError("internal_error", "Internal admission error.", 500);
}
