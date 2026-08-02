import { spawn, type ChildProcess } from "node:child_process";


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

export interface ProcessInvocation {
  cwd: string;
  env: NodeJS.ProcessEnv;
  input?: string;
  timeoutMs: number;
  maximumOutputBytes?: number;
  signal?: AbortSignal;
}

export interface ProcessResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  elapsedMs: number;
}

export class ProcessAbortError extends Error {
  readonly reason: unknown;
  constructor(reason: unknown) {
    super(reason instanceof Error ? reason.message : "Provider process was interrupted by its caller");
    this.name = "ProcessAbortError";
    this.reason = reason;
  }
}

function killProcessTree(child: ChildProcess): void {
  if (child.pid && process.platform !== "win32") {
    try { process.kill(-child.pid, "SIGKILL"); return; } catch {}
  }
  try { child.kill("SIGKILL"); } catch {}
}

export async function runProcess(
  executable: string,
  args: string[],
  options: ProcessInvocation,
): Promise<ProcessResult> {
  if (options.signal?.aborted) throw new ProcessAbortError(options.signal.reason);
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
      detached: process.platform !== "win32",
    });
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    const cleanup = (): void => {
      clearTimeout(timer);
      options.signal?.removeEventListener("abort", abort);
    };
    const fail = (error: Error, kill = true): void => {
      if (settled) return;
      settled = true;
      cleanup();
      if (kill) killProcessTree(child);
      reject(error);
    };
    const abort = (): void => fail(new ProcessAbortError(options.signal?.reason));
    const timer = setTimeout(() => {
      fail(new ProviderAdapterError("timeout", `Provider process exceeded ${options.timeoutMs} ms`));
    }, options.timeoutMs);
    options.signal?.addEventListener("abort", abort, { once: true });
    const append = (target: "stdout" | "stderr", chunk: string): void => {
      if (settled) return;
      outputBytes += Buffer.byteLength(chunk);
      if (outputBytes > maximumOutputBytes) {
        fail(new ProviderAdapterError("process_failed", "Provider process output exceeded the configured limit"));
        return;
      }
      if (target === "stdout") stdout += chunk;
      else stderr += chunk;
    };
    child.stdout.on("data", (chunk: string) => append("stdout", chunk));
    child.stderr.on("data", (chunk: string) => append("stderr", chunk));
    child.on("error", (error) => {
      fail(new ProviderAdapterError("unavailable", `Provider executable failed to start: ${executable}`, { cause: error }), false);
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      cleanup();
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
