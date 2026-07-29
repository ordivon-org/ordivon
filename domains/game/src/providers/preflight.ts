import { accessSync, constants, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

import type { MissionProviderName } from "../mission-control/catalog.ts";

export interface ProviderPreflightEntry {
  providerId: MissionProviderName;
  ready: boolean;
  deterministic: boolean;
  executableReady: boolean;
  credentialsReady: boolean | null;
  summary: string;
}

export interface ProviderPreflight {
  schemaVersion: 1;
  kind: "ordivon.game.provider-preflight";
  providers: ProviderPreflightEntry[];
}

function executableReady(path: string): boolean {
  try {
    accessSync(path, constants.X_OK);
    return true;
  } catch {
    return false;
  }
}

function hermesCredentialsReady(path: string): boolean {
  try {
    return readFileSync(path, "utf8")
      .split(/\r?\n/)
      .some((line) => line.startsWith("DEEPSEEK_API_KEY=") && line.length > "DEEPSEEK_API_KEY=".length);
  } catch {
    return false;
  }
}

export interface ProviderPreflightOptions {
  codexExecutable?: string;
  hermesExecutable?: string;
  hermesCredentialPath?: string;
}

export function providerPreflight(
  options: ProviderPreflightOptions = {},
): ProviderPreflight {
  const codexInstalled = executableReady(options.codexExecutable ?? "/usr/bin/codex");
  const hermesInstalled = executableReady(options.hermesExecutable ?? "/root/.local/bin/hermes");
  const hermesCredentials = hermesCredentialsReady(
    options.hermesCredentialPath ?? join(homedir(), ".hermes", ".env"),
  );
  const fixture: ProviderPreflightEntry = {
    providerId: "fixture",
    ready: true,
    deterministic: true,
    executableReady: true,
    credentialsReady: null,
    summary: "Ready · deterministic local cognition",
  };
  const codex: ProviderPreflightEntry = {
    providerId: "codex",
    ready: codexInstalled,
    deterministic: false,
    executableReady: codexInstalled,
    credentialsReady: null,
    summary: codexInstalled
      ? "CLI installed · authentication is verified on invocation"
      : "Codex CLI is not installed at /usr/bin/codex",
  };
  const hermes: ProviderPreflightEntry = {
    providerId: "hermes",
    ready: hermesInstalled && hermesCredentials,
    deterministic: false,
    executableReady: hermesInstalled,
    credentialsReady: hermesCredentials,
    summary: !hermesInstalled
      ? "Hermes CLI is not installed"
      : hermesCredentials
        ? "CLI and DeepSeek credentials are configured"
        : "Hermes credential file has no DEEPSEEK_API_KEY",
  };
  const byId = new Map<MissionProviderName, ProviderPreflightEntry>([
    [fixture.providerId, fixture],
    [codex.providerId, codex],
    [hermes.providerId, hermes],
  ]);
  const chain = (
    providerId: "codex-hermes" | "hermes-codex",
    first: ProviderPreflightEntry,
    second: ProviderPreflightEntry,
  ): ProviderPreflightEntry => ({
    providerId,
    ready: first.ready || second.ready,
    deterministic: false,
    executableReady: first.executableReady || second.executableReady,
    credentialsReady: first.credentialsReady === true || second.credentialsReady === true
      ? true
      : first.credentialsReady === false || second.credentialsReady === false
        ? false
        : null,
    summary: first.ready
      ? `Ready · ${first.providerId} primary, ${second.providerId} fallback`
      : second.ready
        ? `Ready through ${second.providerId} fallback`
        : "Neither Provider is ready",
  });
  return {
    schemaVersion: 1,
    kind: "ordivon.game.provider-preflight",
    providers: [
      fixture,
      codex,
      hermes,
      chain("codex-hermes", codex, hermes),
      chain("hermes-codex", hermes, codex),
    ],
  };
}
