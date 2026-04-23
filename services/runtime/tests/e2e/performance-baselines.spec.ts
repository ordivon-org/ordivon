import { expect, test } from '@playwright/test';

async function expectPageLoadUnder(page: Parameters<typeof test>[0]['page'], url: string, thresholdMs: number) {
  const startedAt = Date.now();
  await page.goto(url);
  await page.waitForLoadState('networkidle');
  const elapsed = Date.now() - startedAt;
  expect(elapsed).toBeLessThan(thresholdMs);
}

test.describe('AegisOS web performance baselines', () => {
  test('homepage command center baseline', async ({ page }) => {
    await expectPageLoadUnder(page, '/', 8000);
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();
  });

  test('analyze workspace baseline', async ({ page }) => {
    await expectPageLoadUnder(page, '/analyze', 8000);
    await expect(page.getByRole('heading', { name: 'Workflow Execution Workspace' })).toBeVisible();
  });

  test('review workbench baseline', async ({ page }) => {
    await expectPageLoadUnder(page, '/reviews', 9000);
    await expect(page.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
  });
});
