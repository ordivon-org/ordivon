import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';

import { DecisionIntakePanel } from '@/components/features/analyze/DecisionIntakePanel';

const fetchMock = vi.fn();

describe('DecisionIntakePanel', () => {
  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test('renders required structured fields with explicit boolean answers', () => {
    render(<DecisionIntakePanel />);

    expect(screen.getByLabelText('Decision thesis')).toBeInTheDocument();
    expect(screen.getByLabelText('Stop loss')).toBeInTheDocument();
    expect(screen.getByLabelText('Position size usdt')).toHaveAttribute('type', 'number');
    expect(screen.getByLabelText('Max loss usdt')).toHaveAttribute('type', 'number');
    expect(screen.getByLabelText('Risk unit usdt')).toHaveAttribute('type', 'number');
    expect(screen.getByLabelText('Is revenge trade')).toHaveValue('');
    expect(screen.getByLabelText('Is chasing')).toHaveValue('');
  });

  test('submits a valid intake and shows governance as not started', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        id: 'intake_test_1',
        pack_id: 'finance',
        intake_type: 'controlled_decision',
        status: 'validated',
        validation_errors: [],
        governance_status: 'not_started',
        created_at: '2026-04-24T00:00:00+00:00',
      }),
    });

    render(<DecisionIntakePanel prioritized />);

    fireEvent.change(screen.getByLabelText('Decision direction'), { target: { value: 'long' } });
    fireEvent.change(screen.getByLabelText('Decision thesis'), { target: { value: 'Breakout aligns with plan' } });
    fireEvent.change(screen.getByLabelText('Stop loss'), { target: { value: 'Below intraday support' } });
    fireEvent.change(screen.getByLabelText('Position size usdt'), { target: { value: '150' } });
    fireEvent.change(screen.getByLabelText('Max loss usdt'), { target: { value: '25' } });
    fireEvent.change(screen.getByLabelText('Risk unit usdt'), { target: { value: '10' } });
    fireEvent.change(screen.getByLabelText('Emotional state'), { target: { value: 'calm' } });
    fireEvent.change(screen.getByLabelText('Is revenge trade'), { target: { value: 'no' } });
    fireEvent.change(screen.getByLabelText('Is chasing'), { target: { value: 'no' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save controlled decision intake' }));

    await waitFor(() => {
      expect(screen.getByText('Intake persistence result')).toBeInTheDocument();
    });
    expect(screen.getByText('validated')).toBeInTheDocument();
    expect(screen.getByText('not_started')).toBeInTheDocument();
  });

  test('renders structured validation errors from the API', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({
        id: 'intake_test_2',
        pack_id: 'finance',
        intake_type: 'controlled_decision',
        status: 'invalid',
        validation_errors: [{ field: 'thesis', code: 'required', message: 'thesis is required before governance.' }],
        governance_status: 'not_started',
        created_at: '2026-04-24T00:00:00+00:00',
      }),
    });

    render(<DecisionIntakePanel />);
    fireEvent.click(screen.getByRole('button', { name: 'Save controlled decision intake' }));

    await waitFor(() => {
      expect(screen.getByText(/thesis is required before governance/i)).toBeInTheDocument();
    });
  });
});
