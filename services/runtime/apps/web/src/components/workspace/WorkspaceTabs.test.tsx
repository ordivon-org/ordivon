import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, test, vi } from 'vitest';

import { WorkspaceTabs } from '@/components/workspace/WorkspaceTabs';

describe('WorkspaceTabs', () => {
  test('renders selectable and closable object tabs', () => {
    const onSelect = vi.fn();
    const onClose = vi.fn();

    render(
      <WorkspaceTabs
        tabs={[
          {
            id: 'review:1',
            type: 'review_detail',
            title: 'Review review:1',
            refId: 'review:1',
          },
        ]}
        activeTabId="review:1"
        onSelect={onSelect}
        onClose={onClose}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Review review:1' }));
    fireEvent.click(screen.getByRole('button', { name: 'Close Review review:1 tab' }));

    expect(onSelect).toHaveBeenCalledWith('review:1');
    expect(onClose).toHaveBeenCalledWith('review:1');
  });
});
