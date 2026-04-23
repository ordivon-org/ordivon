import { expect, test } from '@playwright/test';

const seedRecommendationId = 'reco_mvp_e2e_seed';
const seedReviewId = 'review_mvp_e2e_seed';

test.describe('AegisOS MVP gold path', () => {
  test('homepage quick analyze hands off into execution workspace and onward to reviews', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Command Center' })).toBeVisible();
    await expect(page.getByText('Live command center for current system status')).toBeVisible();

    await page.getByPlaceholder('e.g. validate breakout strength, assess sentiment shift, summarize near-term risk...').fill('Check BTC breakout continuation');
    await page.getByRole('button', { name: 'Analyze' }).click();

    await page.waitForURL(/\/analyze\?/);
    await expect(page.getByRole('heading', { name: 'Workflow Execution Workspace' })).toBeVisible();
    await expect(page.getByText('Next Actions')).toBeVisible();
    await expect(page.getByText('This workspace owns execution and immediate inspection only.')).toBeVisible();

    const reviewWorkbenchLink = page.getByRole('link', { name: 'Hand off recommendation to review workbench' });
    await expect(reviewWorkbenchLink).toBeVisible();
    await reviewWorkbenchLink.click();

    await page.waitForURL(/\/reviews\?recommendation_id=/);
    await expect(page.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
    await expect(page.getByText('Queue-first supervision')).toBeVisible();
  });

  test('homepage review preview hands off seeded supervision work into the review workbench', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByText('Command-center preview of supervision-needed review objects.')).toBeVisible();
    await expect(page.getByText(`Recommendation: ${seedRecommendationId}`)).toBeVisible();

    await page.locator(`a[href="/reviews?review_id=${seedReviewId}&recommendation_id=${seedRecommendationId}"]`).click();

    await page.waitForURL(new RegExp(`/reviews\\?review_id=${seedReviewId}&recommendation_id=${seedRecommendationId}`));
    await expect(page.getByRole('heading', { name: 'Review Workbench' })).toBeVisible();
    await expect(page.getByText('Pending Review Queue')).toBeVisible();
    await expect(page.getByRole('button', { name: /recommendation_postmortem/i })).toBeVisible();
  });
});
