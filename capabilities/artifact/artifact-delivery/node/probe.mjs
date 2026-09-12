import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
const packageRoot = process.env.ARTIFACT_NODE_PACKAGE_ROOT;
const require = packageRoot ? createRequire(path.join(path.resolve(packageRoot), 'package.json')) : createRequire(import.meta.url);
const { chromium, firefox, webkit } = require('@playwright/test');
const axeModule = require('@axe-core/playwright');
const AxeBuilder = axeModule.default ?? axeModule;
const { trace } = require('@opentelemetry/api');
const { NodeSDK } = require('@opentelemetry/sdk-node');
const pkgVersion = (name) => {
  let dir = path.dirname(require.resolve(name));
  for (;;) {
    const candidate = path.join(dir, 'package.json');
    if (fs.existsSync(candidate)) {
      const pkg = JSON.parse(fs.readFileSync(candidate, 'utf8'));
      if (pkg.name === name) return pkg.version;
    }
    const parent = path.dirname(dir);
    if (parent === dir) throw new Error(`package.json not found for ${name}`);
    dir = parent;
  }
};

const sdk = new NodeSDK();
const tracer = trace.getTracer('artifact-toolchain-probe');
if (!sdk || !tracer) throw new Error('OpenTelemetry SDK/API import probe failed');

const fixture = '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Artifact E2E</title></head><body><main><h1>Artifact Build &amp; Delivery E2E</h1><p>Web profile smoke.</p><a href="#ready">Continue</a><div id="ready" role="status">Ready</div></main></body></html>';

async function launchSmoke(name, browserType, runAxe = false) {
  const executable = browserType.executablePath();
  if (!executable || !fs.existsSync(executable)) {
    return { name, status: 'NOT_INSTALLED', executable };
  }
  const browser = await browserType.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  try {
    const page = await context.newPage();
    await page.setContent(fixture);
    const result = {
      name,
      status: 'PASS',
      version: browser.version(),
      executable,
      title: await page.title(),
      heading: await page.locator('h1').textContent(),
    };
    if (runAxe) {
      const axe = await new AxeBuilder({ page }).analyze();
      result.accessibility = {
        violationCount: axe.violations.length,
        violations: axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length })),
      };
      if (axe.violations.length !== 0) throw new Error(`axe reported ${axe.violations.length} violation(s)`);
    }
    return result;
  } finally {
    await context.close();
    await browser.close();
  }
}

const chromiumResult = await launchSmoke('chromium', chromium, true);
if (chromiumResult.status !== 'PASS') throw new Error(`Chromium smoke did not PASS: ${chromiumResult.status}`);
const firefoxResult = await launchSmoke('firefox', firefox, false);
if (firefoxResult.status !== 'PASS') throw new Error(`Firefox smoke did not PASS: ${firefoxResult.status}`);

const webkitExecutable = webkit.executablePath();
const webkitResult = {
  name: 'webkit',
  status: fs.existsSync(webkitExecutable) ? 'LOCAL_HOST_COMPATIBILITY_NOT_PROVEN' : 'NOT_INSTALLED',
  executable: webkitExecutable,
  note: 'WebKit is a release-profile secondary renderer. Local Arch is not a Playwright-supported WebKit host; target acceptance belongs in a supported Playwright runner rather than ABI symlink workarounds.',
};

console.log(JSON.stringify({
  ok: true,
  kind: 'artifact-build-delivery-web-toolchain-probe',
  versions: {
    node: process.version,
    playwright: pkgVersion('@playwright/test'),
    axePlaywright: pkgVersion('@axe-core/playwright'),
    otelApi: pkgVersion('@opentelemetry/api'),
    otelSdkNode: pkgVersion('@opentelemetry/sdk-node'),
  },
  browsers: {
    chromium: chromiumResult,
    firefox: firefoxResult,
    webkit: webkitResult,
  },
}, null, 2));
