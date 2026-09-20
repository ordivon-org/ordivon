import {existsSync, readdirSync} from 'node:fs';
import {homedir} from 'node:os';
import {join} from 'node:path';
import {Config} from '@remotion/cli/config';

function versionedExecutables(base: string, prefix: string, executableSuffix: string): string[] {
  if (!existsSync(base)) return [];
  return readdirSync(base, {withFileTypes: true})
    .filter((entry) => entry.isDirectory() && entry.name.startsWith(prefix))
    .map((entry) => entry.name)
    .sort((a, b) => b.localeCompare(a, undefined, {numeric: true}))
    .map((entry) => join(base, entry, executableSuffix))
    .filter((candidate) => existsSync(candidate));
}

function resolveLocalBrowser(): string | null {
  const explicit = process.env.ORDIVON_REMOTION_BROWSER;
  if (explicit) {
    if (!existsSync(explicit)) throw new Error(`ORDIVON_REMOTION_BROWSER does not exist: ${explicit}`);
    return explicit;
  }

  const cache = join(homedir(), '.cache');
  const candidates = [
    '/usr/bin/google-chrome-stable',
    '/usr/bin/google-chrome',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser',
    ...versionedExecutables(
      join(cache, 'ms-playwright'),
      'chromium_headless_shell-',
      'chrome-headless-shell-linux64/chrome-headless-shell',
    ),
    ...versionedExecutables(
      join(cache, 'puppeteer', 'chrome-headless-shell'),
      'linux-',
      'chrome-headless-shell-linux64/chrome-headless-shell',
    ),
  ];
  return candidates.find((candidate) => existsSync(candidate)) ?? null;
}

const localBrowser = resolveLocalBrowser();
if (localBrowser) {
  Config.setBrowserExecutable(localBrowser);
} else if (process.env.ORDIVON_REMOTION_ALLOW_BROWSER_DOWNLOAD !== '1') {
  throw new Error(
    'No local Chrome/Chromium executable is available for Remotion. Provision one once, set ORDIVON_REMOTION_BROWSER, or explicitly set ORDIVON_REMOTION_ALLOW_BROWSER_DOWNLOAD=1.',
  );
}

Config.setCodec('h264');
Config.setCrf(18);
Config.setPixelFormat('yuv420p');
Config.setColorSpace('bt709');
Config.setMuted(true);
Config.setOverwriteOutput(true);
Config.setLogLevel('warn');
