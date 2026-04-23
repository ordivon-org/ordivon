import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import QuickAnalyze from '@/components/features/dashboard/QuickAnalyze';

const push = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
}));

describe('QuickAnalyze', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    push.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('routes into the analyze workspace with pack-owned defaults', () => {
    render(<QuickAnalyze />);

    fireEvent.change(screen.getByPlaceholderText(/validate breakout strength/i), {
      target: { value: 'Check BTC breakout continuation' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Analyze' }));

    act(() => {
      vi.advanceTimersByTime(350);
    });

    expect(push).toHaveBeenCalledWith(
      '/analyze?query=Check+BTC+breakout+continuation&symbol=BTC%2FUSDT&timeframe=1h&autoRun=true',
    );
  });
});
