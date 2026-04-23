import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import AnalyzeInput from '@/components/features/analyze/AnalyzeInput';

describe('AnalyzeInput', () => {
  test('renders finance-pack-owned options and submits selected values', () => {
    const onRun = vi.fn();
    render(<AnalyzeInput onRun={onRun} isLoading={false} />);

    expect(screen.getByLabelText('Symbol / Contract')).toHaveValue('BTC/USDT');
    expect(screen.getByRole('button', { name: '1h' })).toHaveAttribute('type', 'button');

    fireEvent.change(screen.getByLabelText('Query / Intent'), {
      target: { value: 'Check ETH momentum shift' },
    });
    fireEvent.change(screen.getByLabelText('Symbol / Contract'), {
      target: { value: 'ETH/USDT' },
    });
    fireEvent.click(screen.getByRole('button', { name: '4h' }));
    fireEvent.click(screen.getByRole('button', { name: 'Execute Analyze Workflow' }));

    expect(onRun).toHaveBeenCalledWith('Check ETH momentum shift', 'ETH/USDT', '4h');
  });
});
