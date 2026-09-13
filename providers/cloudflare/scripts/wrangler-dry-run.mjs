import { spawn } from "node:child_process";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));
const executable = join(
  root,
  "node_modules",
  ".bin",
  process.platform === "win32" ? "wrangler.cmd" : "wrangler"
);
const successMarker = "--dry-run: exiting now.";
let sawSuccess = false;
let settled = false;
let completionTimer;

const child = spawn(
  executable,
  ["deploy", "--dry-run", "--outdir", "dist"],
  {
    cwd: root,
    stdio: ["ignore", "pipe", "pipe"],
    detached: process.platform !== "win32"
  }
);

function terminate(signal) {
  if (child.exitCode !== null || child.signalCode !== null) return;
  try {
    if (process.platform === "win32") child.kill(signal);
    else process.kill(-child.pid, signal);
  } catch {
    child.kill(signal);
  }
}

function observeOutput(stream, destination) {
  let retained = "";
  stream.on("data", (chunk) => {
    destination.write(chunk);
    retained = (retained + chunk.toString("utf8")).slice(-4096);
    if (!sawSuccess && retained.includes(successMarker)) {
      sawSuccess = true;
      completionTimer = setTimeout(() => terminate("SIGTERM"), 500);
      completionTimer.unref();
    }
  });
}

observeOutput(child.stdout, process.stdout);
observeOutput(child.stderr, process.stderr);

const deadline = setTimeout(() => {
  if (settled) return;
  console.error("Wrangler dry-run did not reach its success marker within 60 seconds.");
  terminate("SIGTERM");
  setTimeout(() => terminate("SIGKILL"), 2000).unref();
}, 60_000);
deadline.unref();

child.on("error", (error) => {
  settled = true;
  clearTimeout(deadline);
  clearTimeout(completionTimer);
  console.error(`Unable to start Wrangler: ${error.message}`);
  process.exitCode = 1;
});

child.on("exit", (code, signal) => {
  if (settled) return;
  settled = true;
  clearTimeout(deadline);
  clearTimeout(completionTimer);
  if (code === 0 || (sawSuccess && signal !== null)) {
    process.exitCode = 0;
    return;
  }
  console.error(
    `Wrangler dry-run failed before success (code=${String(code)}, signal=${String(signal)}).`
  );
  process.exitCode = code ?? 1;
});
