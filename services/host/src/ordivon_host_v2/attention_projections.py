"""Host Attention read facade; no independent event-bus or cursor authority.

Subscription list is independent. Reentry composes the original same-MVCC
Delta and Topic cursor read under its one transaction.
"""

from __future__ import annotations

from .attention_reentry_queries import AttentionReentryQueries
from .attention_subscription_queries import AttentionSubscriptionQueries
from .attention_subscription_queries import TargetKind as TargetKind


class AttentionReadProjections(AttentionSubscriptionQueries, AttentionReentryQueries):
    """Existing AttentionStore read API, now assembled from narrow capabilities."""

    dsn: str
