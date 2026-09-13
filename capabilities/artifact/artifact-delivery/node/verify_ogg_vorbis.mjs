import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import { createRequire } from 'node:module';

const packageRoot = process.env.ARTIFACT_NODE_PACKAGE_ROOT;
if (!packageRoot) throw new Error('ARTIFACT_NODE_PACKAGE_ROOT is required');
const require = createRequire(path.join(path.resolve(packageRoot), 'package.json'));
const { chromium, firefox } = require('@playwright/test');

const input = process.argv[2];
const expectedRate = Number(process.argv[3]);
if (!input || !Number.isInteger(expectedRate) || expectedRate <= 0) {
  console.error('usage: node verify_ogg_vorbis.mjs FILE.ogg EXPECTED_SAMPLE_RATE');
  process.exit(2);
}
const inputPath = path.resolve(input);
const bytes = fs.readFileSync(inputPath);
const base64 = bytes.toString('base64');

async function probe(name, browserType) {
  const executable = browserType.executablePath();
  if (!executable || !fs.existsSync(executable)) return { name, status: 'NOT_INSTALLED', executable };
  let browser;
  try {
    browser = await browserType.launch({ headless: true });
    const page = await browser.newPage();
    const decoded = await page.evaluate(async ({ base64, expectedRate }) => {
      const input = Uint8Array.from(atob(base64), c => c.charCodeAt(0));
      const Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) throw new Error('Web Audio AudioContext unavailable');
      const context = new Ctx({ sampleRate: expectedRate });
      try {
        const audio = await context.decodeAudioData(input.buffer.slice(0));
        return {
          sampleRate: audio.sampleRate,
          samplesPerChannel: audio.length,
          channels: audio.numberOfChannels,
          durationSeconds: audio.duration,
        };
      } finally {
        await context.close();
      }
    }, { base64, expectedRate });
    return { name, status: 'PASS', version: browser.version(), executable, ...decoded };
  } catch (error) {
    return { name, status: 'FAIL', executable, error: String(error?.message ?? error).slice(0, 4000) };
  } finally {
    if (browser) await browser.close();
  }
}

const chromiumResult = await probe('Chromium', chromium);
const firefoxResult = await probe('Firefox', firefox);
const result = {
  schemaVersion: 1,
  kind: 'artifact-ogg-vorbis-browser-matrix',
  subject: { path: inputPath, sha256: crypto.createHash('sha256').update(bytes).digest('hex') },
  tooling: { playwright: require('@playwright/test/package.json').version },
  browsers: { chromium: chromiumResult, firefox: firefoxResult },
  status: chromiumResult.status === 'PASS' && firefoxResult.status === 'PASS' ? 'PASS' : 'FAIL',
  sampleBoundaryAgreement: chromiumResult.status === 'PASS' && firefoxResult.status === 'PASS' && chromiumResult.samplesPerChannel === firefoxResult.samplesPerChannel,
  boundary: 'Browser decodeability and observed AudioBuffer facts only. Browser sample-boundary equality is reported, not treated as Vorbis standard authority.'
};
console.log(JSON.stringify(result, null, 2));
