import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

async function expectNoCriticalA11yViolations(page: Parameters<typeof test>[0]['page']) {
  const accessibilityScanResults = await new AxeBuilder({ page })
    .disableRules(['color-contrast'])
    .analyze();

  expect(accessibilityScanResults.violations).toEqual([]);
}

test.describe('AegisOS accessibility smoke', () => {
  test('homepage command center is accessible at baseline', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();
    await expectNoCriticalA11yViolations(page);
  });

  test('analyze workspace is accessible at baseline', async ({ page }) => {
    await page.goto('/analyze');
    await expect(page.getByRole('heading', { name: 'Workflow Execution Workspace' })).toBeVisible();
    await expectNoCriticalA11yViolations(page);
  });

  test('review workbench is accessible at baseline', async ({ page }) => {
    await page.goto('/reviews');
    await expect(page.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
    await expectNoCriticalA11yViolations(page);
  });
});
