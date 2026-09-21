import { createServer, type IncomingHttpHeaders, type IncomingMessage } from "node:http";

import { createAgentAdmissionApp } from "./app.ts";
import { GrantStore } from "./grant-store.ts";
import { OAuthDpopAgentVerifier } from "./oauth-verifier.ts";
import { OpaAdmissionEngine } from "./opa.ts";

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
const origin = requireEnv(
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

if (process.env.AGENT_ADMISSION_ALLOW_INSECURE !== "1") {
  throw new Error(
    "This localhost lab requires AGENT_ADMISSION_ALLOW_INSECURE=1; deployed profiles must use HTTPS.",
  );
}

const store = new GrantStore(databasePath);
const verifier = new OAuthDpopAgentVerifier(
  {
    issuer,
    audience: origin,
    allowInsecureLab: true,
  },
  store,
);
const policy = new OpaAdmissionEngine();
const app = createAgentAdmissionApp({ verifier, store, policy, audience: origin });

const server = createServer(async (request, response) => {
  const result = await app(await toWebRequest(request, origin));
  response.statusCode = result.status;
  result.headers.forEach((value, name) => response.setHeader(name, value));
  response.end(Buffer.from(await result.arrayBuffer()));
});

server.listen(port, "127.0.0.1", () => {
  console.log(JSON.stringify({ event: "listening", origin, issuer, databasePath }));
});

for (const signal of ["SIGINT", "SIGTERM"] as const) {
  process.on(signal, () => {
    server.close(() => {
      store.close();
      process.exit(0);
    });
  });
}
