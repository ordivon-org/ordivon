import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import process from 'node:process';
import { createRequire } from 'node:module';
const packageRoot = process.env.ARTIFACT_NODE_PACKAGE_ROOT;
const require = packageRoot ? createRequire(path.join(path.resolve(packageRoot), 'package.json')) : createRequire(import.meta.url);
const { chromium, firefox, webkit } = require('@playwright/test');
const axeModule = require('@axe-core/playwright');
const AxeBuilder = axeModule.default ?? axeModule;
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

const input = process.argv[2];
if (!input) {
  console.error('usage: node verify_html.mjs FILE.html');
  process.exit(2);
}
const inputPath = path.resolve(input);
const bytes = fs.readFileSync(inputPath);
const html = bytes.toString('utf8');
const sha256 = crypto.createHash('sha256').update(bytes).digest('hex');

async function checkBrowser(name, browserType, { axe = false } = {}) {
  const executable = browserType.executablePath();
  if (!executable || !fs.existsSync(executable)) {
    return { name, status: 'NOT_INSTALLED', executable };
  }
  let browser;
  try {
    browser = await browserType.launch({ headless: true });
    const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
    try {
      const page = await context.newPage();
      await page.setContent(html, { waitUntil: 'load' });
      const result = {
        name,
        status: 'PASS',
        version: browser.version(),
        executable,
        title: await page.title(),
        headingCount: await page.locator('h1').count(),
      };
      if (axe) {
        const report = await new AxeBuilder({ page }).analyze();
        result.accessibility = {
          status: report.violations.length === 0 ? 'PASS' : 'FAIL',
          violationCount: report.violations.length,
          violations: report.violations.map((item) => ({
            id: item.id,
            impact: item.impact,
            nodes: item.nodes.length,
          })),
        };
      }
      return result;
    } finally {
      await context.close();
    }
  } catch (error) {
    return {
      name,
      status: 'FAIL',
      executable,
      error: String(error?.message ?? error).slice(0, 4000),
    };
  } finally {
    if (browser) await browser.close();
  }
}

const browsers = {
  chromium: await checkBrowser('Chromium', chromium, { axe: true }),
  firefox: await checkBrowser('Firefox', firefox),
  webkit: await checkBrowser('WebKit', webkit),
};

const result = {
  schemaVersion: 1,
  kind: 'artifact-web-local-verification-evidence',
  status: browsers.chromium.status === 'PASS' && browsers.firefox.status === 'PASS' ? 'PASS' : 'FAIL',
  subject: {
    name: path.basename(input),
    path: inputPath,
    sha256,
  },
  tooling: {
    playwright: pkgVersion('@playwright/test'),
    axePlaywright: pkgVersion('@axe-core/playwright'),
  },
  browsers,
  boundary: 'Local browser/axe evidence only. Required renderer policy is evaluated by the delivery profile; unsupported WebKit host standing and deployed-origin behavior remain independent.',
};
console.log(JSON.stringify(result, null, 2));
