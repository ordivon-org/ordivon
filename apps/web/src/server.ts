import { createWebApp } from "./app.ts";
import { loadConfig } from "./config.ts";

const config = loadConfig();
const app = await createWebApp(config);

await app.listen({ host: config.host, port: config.port });
