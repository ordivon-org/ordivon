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
const deadlineMs = 60_000;
const completionGraceMs = 500;
const terminationGraceMs = 2_000;
let sawSuccess = false;
let settled = false;
let deadlineExpired = false;
let completionTimer;
let killTimer;
let hardExitTimer;

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

function clearTimers() {
  clearTimeout(deadline);
  clearTimeout(completionTimer);
  clearTimeout(killTimer);
  clearTimeout(hardExitTimer);
}

function scheduleHardExit(code) {
  hardExitTimer = setTimeout(() => {
    // A detached Wrangler descendant can keep inherited pipe handles alive after the
    // direct child has completed. At this point terminal authority is already known.
    process.exit(code);
  }, terminationGraceMs);
}

function observeOutput(stream, destination) {
  let retained = "";
  stream.on("data", (chunk) => {
    destination.write(chunk);
    retained = (retained + chunk.toString("utf8")).slice(-4096);
    if (!deadlineExpired && !sawSuccess && retained.includes(successMarker)) {
      sawSuccess = true;
      clearTimeout(deadline);
      completionTimer = setTimeout(() => {
        terminate("SIGTERM");
        scheduleHardExit(0);
      }, completionGraceMs);
    }
  });
}

observeOutput(child.stdout, process.stdout);
observeOutput(child.stderr, process.stderr);

const deadline = setTimeout(() => {
  if (settled || sawSuccess) return;
  deadlineExpired = true;
  console.error("Wrangler dry-run did not reach its success marker within 60 seconds.");
  terminate("SIGTERM");
  killTimer = setTimeout(() => terminate("SIGKILL"), terminationGraceMs);
  hardExitTimer = setTimeout(() => process.exit(1), terminationGraceMs + 500);
}, deadlineMs);

child.on("error", (error) => {
  if (settled) return;
  settled = true;
  clearTimers();
  console.error(`Unable to start Wrangler: ${error.message}`);
  process.exit(1);
});

child.on("exit", (code, signal) => {
  if (settled) return;
  settled = true;
  clearTimers();
  if (!deadlineExpired && (code === 0 || (sawSuccess && signal !== null))) {
    process.exitCode = 0;
    return;
  }
  if (deadlineExpired) {
    process.exitCode = 1;
    return;
  }
  console.error(
    `Wrangler dry-run failed before success (code=${String(code)}, signal=${String(signal)}).`
  );
  process.exitCode = code ?? 1;
});
