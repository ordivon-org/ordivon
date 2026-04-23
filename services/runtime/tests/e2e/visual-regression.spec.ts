import { expect, test } from '@playwright/test';

test.describe('AegisOS visual regression', () => {
  test('homepage command center remains visually stable', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();
    await expect(page.locator('main')).toHaveScreenshot('homepage-command-center.png', {
      animations: 'disabled',
      caret: 'hide',
      maxDiffPixelRatio: 0.05,
    });
  });

  test('analyze result state remains visually stable', async ({ page }) => {
    await page.goto('/analyze?query=Check%20BTC%20breakout%20continuation&symbol=BTC%2FUSDT&timeframe=1h&autoRun=true');
    await expect(page.getByText('Next Actions')).toBeVisible();
    await expect(page.locator('main')).toHaveScreenshot('analyze-result-state.png', {
      animations: 'disabled',
      caret: 'hide',
      maxDiffPixelRatio: 0.05,
    });
  });

  test('review queue-first layout remains visually stable', async ({ page }) => {
    await page.goto('/reviews?review_id=review_mvp_e2e_seed&recommendation_id=reco_mvp_e2e_seed');
    await expect(page.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
    await expect(page.locator('main')).toHaveScreenshot('reviews-queue-first-layout.png', {
      animations: 'disabled',
      caret: 'hide',
      maxDiffPixelRatio: 0.05,
    });
  });
});
