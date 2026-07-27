import { spawn } from "node:child_process";

import { ProviderAdapterError } from "./types.ts";

export interface ProcessInvocation {
  cwd: string;
  env: NodeJS.ProcessEnv;
  input?: string;
  timeoutMs: number;
  maximumOutputBytes?: number;
}

export interface ProcessResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  elapsedMs: number;
}

export async function runProcess(
  executable: string,
  args: string[],
  options: ProcessInvocation,
): Promise<ProcessResult> {
  const maximumOutputBytes = options.maximumOutputBytes ?? 1_000_000;
  const startedAt = performance.now();
  return await new Promise<ProcessResult>((resolve, reject) => {
    let settled = false;
    let stdout = "";
    let stderr = "";
    let outputBytes = 0;
    const child = spawn(executable, args, {
      cwd: options.cwd,
      env: options.env,
      stdio: ["pipe", "pipe", "pipe"],
    });
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGKILL");
      reject(new ProviderAdapterError("timeout", `Provider process exceeded ${options.timeoutMs} ms`));
    }, options.timeoutMs);
    const append = (target: "stdout" | "stderr", chunk: string): void => {
      if (settled) return;
      outputBytes += Buffer.byteLength(chunk);
      if (outputBytes > maximumOutputBytes) {
        settled = true;
        clearTimeout(timer);
        child.kill("SIGKILL");
        reject(new ProviderAdapterError("process_failed", "Provider process output exceeded the configured limit"));
        return;
      }
      if (target === "stdout") stdout += chunk;
      else stderr += chunk;
    };
    child.stdout.on("data", (chunk: string) => append("stdout", chunk));
    child.stderr.on("data", (chunk: string) => append("stderr", chunk));
    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(new ProviderAdapterError("unavailable", `Provider executable failed to start: ${executable}`, { cause: error }));
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({
        exitCode: Number(code ?? -1),
        stdout,
        stderr,
        elapsedMs: performance.now() - startedAt,
      });
    });
    if (options.input !== undefined) child.stdin.end(options.input);
    else child.stdin.end();
  });
}
