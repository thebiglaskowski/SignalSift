"""Content processing module for SignalSift."""

from signalsift.processing.classification import classify_content, get_category_name
from signalsift.processing.keywords import KeywordMatcher, find_matching_keywords
from signalsift.processing.scoring import (
    calculate_reddit_score,
    calculate_youtube_score,
    process_reddit_thread,
    process_youtube_video,
)

__all__ = [
    "classify_content",
    "get_category_name",
    "KeywordMatcher",
    "find_matching_keywords",
    "calculate_reddit_score",
    "calculate_youtube_score",
    "process_reddit_thread",
    "process_youtube_video",
]
