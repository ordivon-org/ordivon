import { expect, test } from '@playwright/test';

const apiBaseURL = process.env.PFIOS_API_BASE_URL ?? 'http://127.0.0.1:8000';

test.describe('AegisOS release smoke', () => {
  test('booted release serves the MVP routes and health endpoints', async ({ page, request }) => {
    const health = await request.get(`${apiBaseURL}/api/v1/health`);
    expect(health.ok()).toBeTruthy();

    const history = await request.get(`${apiBaseURL}/api/v1/health/history`);
    expect(history.ok()).toBeTruthy();

    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();

    await page.goto('/analyze');
    await expect(page.getByRole('heading', { name: 'Workflow Execution Workspace' })).toBeVisible();

    await page.goto('/reviews');
    await expect(page.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
  });
});
