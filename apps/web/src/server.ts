import { createWebApp } from "./app.ts";
import { loadConfig } from "./config.ts";
import { SecurityAgentRequestVerifier } from "./security-agent-verifier.ts";
import { WebStore } from "./store.ts";

const config = loadConfig();
const store = new WebStore(config.databasePath);
const agentVerifier =
  config.agentIssuer === undefined
    ? undefined
    : new SecurityAgentRequestVerifier(config, store);
const app = await createWebApp(config, {
  store,
  ...(agentVerifier === undefined ? {} : { agentVerifier }),
});
app.addHook("onClose", async () => {
  store.close();
});

await app.listen({ host: config.host, port: config.port });
