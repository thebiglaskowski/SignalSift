"""Custom exceptions for SignalSift."""


class SignalSiftError(Exception):
    """Base exception for SignalSift."""

    pass


class ConfigurationError(SignalSiftError):
    """Raised when there's a configuration issue."""

    pass


class DatabaseError(SignalSiftError):
    """Raised when there's a database issue."""

    pass


class SourceError(SignalSiftError):
    """Raised when there's an issue with a data source."""

    pass


class RedditError(SourceError):
    """Raised when there's an issue with the Reddit API."""

    pass


class YouTubeError(SourceError):
    """Raised when there's an issue with the YouTube API."""

    pass


class ReportError(SignalSiftError):
    """Raised when there's an issue generating a report."""

    pass
