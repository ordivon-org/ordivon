"""Public Host social read facet; one PostgreSQL write owner remains SocialStore."""

from __future__ import annotations

from .social_message_queries import SocialMessageReadQueries
from .social_space_queries import SocialSpaceReadQueries
from .social_topic_queries import SocialTopicReadQueries


class SocialReadQueries(
    SocialSpaceReadQueries,
    SocialMessageReadQueries,
    SocialTopicReadQueries,
):
    """Reuses read-only facets; no independent datastore or authority."""
