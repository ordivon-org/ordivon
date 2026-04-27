import { expect, test } from '@playwright/test';

test.describe('AegisOS escalate path (emotional risk → human review)', () => {
  test('homepage analyze with emotional-risk thesis triggers escalation flag visible within 15s', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();

    await page
      .getByPlaceholder(
        'e.g. validate breakout strength, assess sentiment shift, summarize near-term risk...',
      )
      .fill(
        'BTC looks strong. Breaking above resistance with volume confirmation. Invalidated if price closes below 200 EMA on 1h.',
      );
    await page.getByRole('button', { name: 'Analyze' }).click();

    await page.waitForURL(/\analyze\?/);
    await expect(page.getByRole('heading', { name: 'Workflow Execution Workspace' })).toBeVisible();

    await expect(
      page.getByText(/escalat|human review|review required/i),
    ).toBeVisible({ timeout: 15_000 });
  });
});
