"""Base class for data source adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ContentItem:
    """Generic content item from any source."""

    id: str
    source_type: str  # "reddit" or "youtube"
    source_id: str  # subreddit name or channel ID
    title: str
    content: str  # selftext or transcript
    url: str
    created_at: datetime
    metadata: dict[str, Any]


class BaseSource(ABC):
    """Abstract base class for all data sources."""

    @abstractmethod
    def fetch(
        self,
        since: datetime | None = None,
        limit: int | None = None,
    ) -> list[ContentItem]:
        """
        Fetch content from the source.

        Args:
            since: Only fetch content created after this datetime.
            limit: Maximum number of items to fetch.

        Returns:
            List of ContentItem objects.
        """
        pass

    @abstractmethod
    def get_source_type(self) -> str:
        """Return the source type identifier (e.g., 'reddit', 'youtube')."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the source connection is working."""
        pass
