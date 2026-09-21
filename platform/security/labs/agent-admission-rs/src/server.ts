import { createServer, type IncomingHttpHeaders, type IncomingMessage } from "node:http";

import { createAgentAdmissionApp } from "./app.ts";
import { GrantStore } from "./grant-store.ts";
import { OAuthDpopAgentVerifier } from "./oauth-verifier.ts";
import { OpaAdmissionEngine } from "./opa.ts";
import { PrincipalStore } from "./principal-store.ts";
import { createWebAuthnRouter } from "./webauthn-router.ts";
import { WebAuthnPrincipalService } from "./webauthn-service.ts";

function requireEnv(name: string, fallback?: string): string {
  const value = process.env[name] ?? fallback;
  if (value === undefined || value === "") throw new Error(`${name} is required`);
  return value;
}

function webHeaders(input: IncomingHttpHeaders): Headers {
  const headers = new Headers();
  for (const [name, value] of Object.entries(input)) {
    if (value === undefined) continue;
    if (Array.isArray(value)) {
      for (const item of value) headers.append(name, item);
    } else {
      headers.set(name, value);
    }
  }
  return headers;
}

async function toWebRequest(message: IncomingMessage, origin: string): Promise<Request> {
  const chunks: Buffer[] = [];
  for await (const chunk of message) chunks.push(Buffer.from(chunk));
  const body = Buffer.concat(chunks);
  const method = message.method ?? "GET";
  return new Request(new URL(message.url ?? "/", origin), {
    method,
    headers: webHeaders(message.headers),
    ...(method === "GET" || method === "HEAD" ? {} : { body }),
  });
}

const port = Number.parseInt(requireEnv("AGENT_ADMISSION_PORT", "8788"), 10);
const audience = requireEnv(
  "AGENT_ADMISSION_AUDIENCE",
  `http://127.0.0.1:${port}`,
);
const issuer = requireEnv(
  "AGENT_ADMISSION_ISSUER",
  "http://127.0.0.1:18080/realms/agent-admission-lab",
);
const databasePath = requireEnv(
  "AGENT_ADMISSION_DB",
  new URL("../.agent-admission-lab.sqlite3", import.meta.url).pathname,
);
const webAuthnOrigin = requireEnv(
  "AGENT_ADMISSION_WEBAUTHN_ORIGIN",
  `http://localhost:${port}`,
);
const webAuthnRpId = requireEnv("AGENT_ADMISSION_WEBAUTHN_RPID", "localhost");
const enrollmentToken = process.env.AGENT_ADMISSION_ENROLLMENT_TOKEN;
const webAuthnStepUpEnabled =
  process.env.AGENT_ADMISSION_WEBAUTHN_STEP_UP === "1";

if (process.env.AGENT_ADMISSION_ALLOW_INSECURE !== "1") {
  throw new Error(
    "This localhost lab requires AGENT_ADMISSION_ALLOW_INSECURE=1; deployed profiles must use HTTPS.",
  );
}

const grants = new GrantStore(databasePath);
const principals = new PrincipalStore(databasePath);
const verifier = new OAuthDpopAgentVerifier(
  {
    issuer,
    audience,
    allowInsecureLab: true,
  },
  grants,
);
const policy = new OpaAdmissionEngine();
const webAuthn = new WebAuthnPrincipalService(principals, grants, {
  rpName: "Ordivon Agent Admission Lab",
  rpID: webAuthnRpId,
  origin: webAuthnOrigin,
  audience,
});
const webAuthnRouter = createWebAuthnRouter(
  webAuthn,
  enrollmentToken === undefined ? {} : { enrollmentToken },
);
const app = createAgentAdmissionApp({
  verifier,
  store: grants,
  policy,
  audience,
  ...(webAuthnStepUpEnabled
    ? {
        approval: (effect, principalId) =>
          webAuthn.lookupEffectApproval(principalId, effect),
        onStepUp: (effect, principalId) =>
          webAuthn.registerStepUp(principalId, effect),
        consumeApproval: (effect, principalId) =>
          webAuthn.consumeEffectApproval(principalId, effect),
      }
    : {}),
});

const server = createServer(async (request, response) => {
  const webRequest = await toWebRequest(request, audience);
  const result = (await webAuthnRouter(webRequest)) ?? (await app(webRequest));
  response.statusCode = result.status;
  result.headers.forEach((value, name) => response.setHeader(name, value));
  response.end(Buffer.from(await result.arrayBuffer()));
});

server.listen(port, "127.0.0.1", () => {
  console.log(
    JSON.stringify({
      event: "listening",
      audience,
      issuer,
      databasePath,
      webAuthnOrigin,
      webAuthnRpId,
      enrollmentEnabled: enrollmentToken !== undefined,
      webAuthnStepUpEnabled,
    }),
  );
});

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    server.close(() => {
      principals.close();
      grants.close();
      process.exit(0);
    });
  });
}
