"""Pydantic settings models for SignalSift configuration."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from signalsift.config.defaults import (
    DEFAULT_DB_PATH,
    DEFAULT_EXCERPT_LENGTH,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_MAX_SIZE_MB,
    DEFAULT_MAX_ITEMS_PER_SECTION,
    DEFAULT_MIN_RELEVANCE_SCORE,
    DEFAULT_REDDIT_MAX_AGE_DAYS,
    DEFAULT_REDDIT_MIN_COMMENTS,
    DEFAULT_REDDIT_MIN_SCORE,
    DEFAULT_REDDIT_POSTS_PER_SUBREDDIT,
    DEFAULT_REDDIT_REQUEST_DELAY,
    DEFAULT_REDDIT_USER_AGENT,
    DEFAULT_YOUTUBE_MAX_AGE_DAYS,
    DEFAULT_YOUTUBE_MAX_DURATION,
    DEFAULT_YOUTUBE_MIN_DURATION,
    DEFAULT_YOUTUBE_TRANSCRIPT_LANGUAGE,
    DEFAULT_YOUTUBE_TRANSCRIPT_MAX_LENGTH,
    DEFAULT_YOUTUBE_VIDEOS_PER_CHANNEL,
    LOGS_DIR,
    REPORTS_DIR,
)


class DatabaseSettings(BaseModel):
    """Database configuration."""

    path: Path = DEFAULT_DB_PATH


class RedditSettings(BaseModel):
    """Reddit configuration."""

    mode: str = "rss"  # "api" (requires credentials) or "rss" (no credentials needed)
    client_id: str = ""
    client_secret: str = ""
    user_agent: str = DEFAULT_REDDIT_USER_AGENT
    min_score: int = DEFAULT_REDDIT_MIN_SCORE
    min_comments: int = DEFAULT_REDDIT_MIN_COMMENTS
    max_age_days: int = DEFAULT_REDDIT_MAX_AGE_DAYS
    posts_per_subreddit: int = DEFAULT_REDDIT_POSTS_PER_SUBREDDIT
    request_delay_seconds: float = DEFAULT_REDDIT_REQUEST_DELAY
    include_comments: bool = False

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        """Validate Reddit mode."""
        valid_modes = ["api", "rss"]
        v = v.lower()
        if v not in valid_modes:
            raise ValueError(f"Invalid Reddit mode: {v}. Must be one of {valid_modes}")
        return v


class YouTubeSettings(BaseModel):
    """YouTube configuration."""

    api_key: str = ""
    min_duration_seconds: int = DEFAULT_YOUTUBE_MIN_DURATION
    max_duration_seconds: int = DEFAULT_YOUTUBE_MAX_DURATION
    max_age_days: int = DEFAULT_YOUTUBE_MAX_AGE_DAYS
    videos_per_channel: int = DEFAULT_YOUTUBE_VIDEOS_PER_CHANNEL
    include_search: bool = True
    search_queries_per_run: int = 5
    transcript_language: str = DEFAULT_YOUTUBE_TRANSCRIPT_LANGUAGE
    transcript_max_length: int = DEFAULT_YOUTUBE_TRANSCRIPT_MAX_LENGTH


class ScoringWeights(BaseModel):
    """Scoring weight configuration."""

    engagement: float = 1.0
    keywords: float = 1.2
    content_quality: float = 1.0
    source_tier: float = 0.8


class ScoringSettings(BaseModel):
    """Scoring configuration."""

    min_relevance_score: int = DEFAULT_MIN_RELEVANCE_SCORE
    weights: ScoringWeights = Field(default_factory=ScoringWeights)


class ReportSettings(BaseModel):
    """Report generation configuration."""

    output_directory: Path = REPORTS_DIR
    filename_format: str = "{date}.md"
    max_items_per_section: int = DEFAULT_MAX_ITEMS_PER_SECTION
    include_full_index: bool = True
    excerpt_length: int = DEFAULT_EXCERPT_LENGTH


class LoggingSettings(BaseModel):
    """Logging configuration."""

    level: str = DEFAULT_LOG_LEVEL
    file: Path = LOGS_DIR / "signalsift.log"
    max_size_mb: int = DEFAULT_LOG_MAX_SIZE_MB
    backup_count: int = DEFAULT_LOG_BACKUP_COUNT

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v


class Settings(BaseSettings):
    """Main settings class for SignalSift."""

    model_config = SettingsConfigDict(
        env_prefix="SIGNALSIFT_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    reddit: RedditSettings = Field(default_factory=RedditSettings)
    youtube: YouTubeSettings = Field(default_factory=YouTubeSettings)
    scoring: ScoringSettings = Field(default_factory=ScoringSettings)
    reports: ReportSettings = Field(default_factory=ReportSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    # Direct environment variable mappings
    reddit_client_id: str = Field(default="", alias="REDDIT_CLIENT_ID")
    reddit_client_secret: str = Field(default="", alias="REDDIT_CLIENT_SECRET")
    youtube_api_key: str = Field(default="", alias="YOUTUBE_API_KEY")

    def model_post_init(self, __context: Any) -> None:
        """Post-init hook to merge environment variables into nested settings."""
        if self.reddit_client_id and not self.reddit.client_id:
            self.reddit.client_id = self.reddit_client_id
        if self.reddit_client_secret and not self.reddit.client_secret:
            self.reddit.client_secret = self.reddit_client_secret
        if self.youtube_api_key and not self.youtube.api_key:
            self.youtube.api_key = self.youtube_api_key

    def ensure_directories(self) -> None:
        """Create required directories if they don't exist."""
        self.database.path.parent.mkdir(parents=True, exist_ok=True)
        self.reports.output_directory.mkdir(parents=True, exist_ok=True)
        self.logging.file.parent.mkdir(parents=True, exist_ok=True)

    def has_reddit_credentials(self) -> bool:
        """Check if Reddit credentials are configured."""
        return bool(self.reddit.client_id and self.reddit.client_secret)

    def has_youtube_credentials(self) -> bool:
        """Check if YouTube credentials are configured."""
        return bool(self.youtube.api_key)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    settings = Settings()
    settings.ensure_directories()
    return settings
