"""Default configuration values for SignalSift."""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
LOGS_DIR = BASE_DIR / "logs"

# Database
DEFAULT_DB_PATH = DATA_DIR / "signalsift.db"

# Reddit defaults
DEFAULT_REDDIT_USER_AGENT = "SignalSift/1.0 (personal research tool)"
DEFAULT_REDDIT_MIN_SCORE = 10
DEFAULT_REDDIT_MIN_COMMENTS = 3
DEFAULT_REDDIT_MAX_AGE_DAYS = 30
DEFAULT_REDDIT_POSTS_PER_SUBREDDIT = 100
DEFAULT_REDDIT_REQUEST_DELAY = 2.0

# YouTube defaults
DEFAULT_YOUTUBE_MIN_DURATION = 300  # 5 minutes
DEFAULT_YOUTUBE_MAX_DURATION = 5400  # 90 minutes
DEFAULT_YOUTUBE_MAX_AGE_DAYS = 30
DEFAULT_YOUTUBE_VIDEOS_PER_CHANNEL = 10
DEFAULT_YOUTUBE_TRANSCRIPT_LANGUAGE = "en"
DEFAULT_YOUTUBE_TRANSCRIPT_MAX_LENGTH = 50000

# Scoring defaults
DEFAULT_MIN_RELEVANCE_SCORE = 30

# Report defaults
DEFAULT_MAX_ITEMS_PER_SECTION = 15
DEFAULT_EXCERPT_LENGTH = 300

# Logging defaults
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_MAX_SIZE_MB = 10
DEFAULT_LOG_BACKUP_COUNT = 3

# =============================================================================
# DEFAULT SUBREDDITS - Example communities (customize for your interests)
# =============================================================================
# Tier 1: High signal, professional discussions
# Tier 2: Medium signal, good community engagement
# Tier 3: Supplementary, broader topics

DEFAULT_SUBREDDITS = {
    1: [
        # Technology & Programming
        "programming",
        "webdev",
        "learnprogramming",
        # AI & Machine Learning
        "MachineLearning",
        "artificial",
        "LocalLLaMA",
    ],
    2: [
        # Startups & Business
        "startups",
        "Entrepreneur",
        "SideProject",
        # Tech News
        "technology",
        "tech",
        # Productivity
        "productivity",
        "getdisciplined",
    ],
    3: [
        # General Interest
        "InternetIsBeautiful",
        "dataisbeautiful",
        "todayilearned",
        # Self Improvement
        "selfimprovement",
        "DecidingToBeBetter",
    ],
}

# =============================================================================
# DEFAULT YOUTUBE CHANNELS - Example channels (customize for your interests)
# =============================================================================

DEFAULT_YOUTUBE_CHANNELS = {
    # Tech & Programming
    "UC8butISFwT-Wl7EV0hUK0BQ": "freeCodeCamp",
    "UCvjgXvBlHQA9_0IIrKCa8Nw": "Fireship",
    "UC-8QAzbLcRglXeN_MY9blyw": "Ben Awad",

    # AI & Tech News
    "UCWN3xxRkmTPmbKwht9FuE5A": "Siraj Raval",
    "UCbmNph6atAoGfqLoCL_duAg": "Sam Witteveen",
}

# =============================================================================
# DEFAULT KEYWORDS - Example keywords (customize for your interests)
# =============================================================================

DEFAULT_KEYWORDS = {
    "success_signals": [
        "finally figured out",
        "breakthrough",
        "game changer",
        "highly recommend",
        "works great",
        "solved it",
        "success story",
    ],
    "pain_points": [
        "struggling with",
        "frustrated",
        "need help",
        "doesn't work",
        "any alternatives",
        "looking for",
        "problem with",
    ],
    "tools": [
        "tool",
        "app",
        "software",
        "service",
        "platform",
        "solution",
    ],
    "trends": [
        "trending",
        "new release",
        "just launched",
        "announcement",
        "update",
        "beta",
    ],
}
