"""Database module for SignalSift."""

from signalsift.database.connection import get_connection, initialize_database
from signalsift.database.models import (
    Keyword,
    ProcessingLogEntry,
    RedditThread,
    Report,
    Source,
    YouTubeVideo,
)
from signalsift.database.queries import (
    get_cache_stats,
    get_keywords_by_category,
    get_sources_by_type,
    get_unprocessed_content,
    insert_reddit_thread,
    insert_youtube_video,
    mark_content_processed,
    thread_exists,
    video_exists,
)

__all__ = [
    # Connection
    "get_connection",
    "initialize_database",
    # Models
    "RedditThread",
    "YouTubeVideo",
    "Report",
    "Keyword",
    "Source",
    "ProcessingLogEntry",
    # Queries
    "get_cache_stats",
    "get_keywords_by_category",
    "get_sources_by_type",
    "get_unprocessed_content",
    "insert_reddit_thread",
    "insert_youtube_video",
    "mark_content_processed",
    "thread_exists",
    "video_exists",
]
