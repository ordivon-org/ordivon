export interface WebConfig {
  readonly host: string;
  readonly port: number;
  readonly origin: string;
  readonly rpID: string;
  readonly rpName: string;
  readonly databasePath: string;
  readonly bootstrapEnrollmentToken?: string;
  readonly sessionIdleSeconds: number;
  readonly sessionAbsoluteSeconds: number;
}

function integerEnv(name: string, fallback: number): number {
  const raw = process.env[name];
  if (raw === undefined) return fallback;
  const value = Number.parseInt(raw, 10);
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error(name + " must be a positive integer");
  }
  return value;
}

export function loadConfig(): WebConfig {
  const port = integerEnv("ORDIVON_WEB_PORT", 8789);
  const host = process.env.ORDIVON_WEB_HOST ?? "127.0.0.1";
  const origin = process.env.ORDIVON_WEB_ORIGIN ?? "https://localhost:" + port;
  const rpID = process.env.ORDIVON_WEB_RPID ?? new URL(origin).hostname;
  return {
    host,
    port,
    origin,
    rpID,
    rpName: process.env.ORDIVON_WEB_RP_NAME ?? "Ordivon",
    databasePath:
      process.env.ORDIVON_WEB_DB ??
      new URL("../.web.sqlite3", import.meta.url).pathname,
    ...(process.env.ORDIVON_WEB_BOOTSTRAP_ENROLLMENT_TOKEN === undefined
      ? {}
      : {
          bootstrapEnrollmentToken:
            process.env.ORDIVON_WEB_BOOTSTRAP_ENROLLMENT_TOKEN,
        }),
    sessionIdleSeconds: integerEnv("ORDIVON_WEB_SESSION_IDLE_SECONDS", 1800),
    sessionAbsoluteSeconds: integerEnv(
      "ORDIVON_WEB_SESSION_ABSOLUTE_SECONDS",
      43200,
    ),
  };
}
