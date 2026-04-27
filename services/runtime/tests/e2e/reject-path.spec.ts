import { expect, test } from '@playwright/test';

test.describe('AegisOS reject path (low-quality thesis → blocked)', () => {
  test('homepage quick analyze with banned thesis shows rejection and hides plan action', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();
    await expect(page.getByText('Live command center for current system status')).toBeVisible();

    // Fill banned thesis
    await page
      .getByPlaceholder(
        'e.g. validate breakout strength, assess sentiment shift, summarize near-term risk...',
      )
      .fill('YOLO all in');
    await page.getByRole('button', { name: 'Analyze' }).click();

    await page.waitForURL(/\/analyze\?/);
    await expect(page.getByRole('heading', { name: 'Workflow Execution Workspace' })).toBeVisible();

    // Expect a rejection/blocked message visible within 15s
    await expect(page.getByText(/reject|blocked|not allowed/i).first()).toBeVisible({
      timeout: 15_000,
    });

    // Plan button should be disabled or hidden
    const planButton = page.getByRole('button', { name: /plan/i });
    if ((await planButton.count()) > 0) {
      await expect(planButton).toBeDisabled();
    } else {
      await expect(planButton).not.toBeVisible();
    }
  });
});
