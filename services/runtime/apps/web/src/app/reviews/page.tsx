import { Suspense } from 'react';

import { ReviewConsole } from '@/components/features/reviews/ReviewConsole';
import { ConsolePageFrame } from '@/components/workspace/ConsolePageFrame';

export default function ReviewsPage() {
  return (
    <ConsolePageFrame>
      <Suspense fallback={<div style={{ padding: '1rem', color: 'var(--text-muted)' }}>Loading review workbench...</div>}>
        <ReviewConsole />
      </Suspense>
    </ConsolePageFrame>
  );
}
