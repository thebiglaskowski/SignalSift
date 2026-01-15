"""Data source adapters for SignalSift."""

from signalsift.sources.base import BaseSource, ContentItem
from signalsift.sources.reddit import RedditSource
from signalsift.sources.reddit_rss import RedditRSSSource
from signalsift.sources.youtube import YouTubeSource

__all__ = ["BaseSource", "ContentItem", "RedditSource", "RedditRSSSource", "YouTubeSource"]
