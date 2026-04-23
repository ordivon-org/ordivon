import { defineConfig, devices } from '@playwright/test';

const baseURL = process.env.PFIOS_E2E_BASE_URL ?? 'http://127.0.0.1:3000';
const apiBaseURL = process.env.PFIOS_API_BASE_URL ?? 'http://127.0.0.1:8000';
const apiPort = new URL(apiBaseURL).port || '8000';
const webPort = new URL(baseURL).port || '3000';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 60_000,
  snapshotPathTemplate: '{testDir}/__snapshots__/{arg}{ext}',
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL,
    trace: 'on-first-retry',
    viewport: { width: 1440, height: 900 },
  },
  webServer: [
    {
      command: `python -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port ${apiPort}`,
      url: `${apiBaseURL}/api/v1/health`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `pnpm --dir apps/web clean && pnpm --dir apps/web exec next dev --hostname 127.0.0.1 --port ${webPort}`,
      url: baseURL,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
