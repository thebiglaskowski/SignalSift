"""Relevance scoring algorithms for SignalSift."""

import re
from datetime import datetime

from signalsift.database.models import RedditThread, YouTubeVideo
from signalsift.database.queries import get_sources_by_type
from signalsift.processing.classification import classify_content
from signalsift.processing.keywords import (
    KeywordMatch,
    KeywordMatcher,
    get_matcher,
)
from signalsift.sources.base import ContentItem


def calculate_engagement_velocity(
    score: int,
    comments: int,
    created_timestamp: int,
    now: datetime | None = None,
) -> float:
    """
    Calculate engagement velocity (engagement per hour).

    Higher velocity = content is gaining traction quickly.

    Args:
        score: Upvotes/points.
        comments: Number of comments.
        created_timestamp: Unix timestamp of creation.
        now: Current time (defaults to now).

    Returns:
        Engagement per hour.
    """
    if now is None:
        now = datetime.now()

    age_hours = (now.timestamp() - created_timestamp) / 3600
    if age_hours < 0.5:
        age_hours = 0.5  # Minimum 30 minutes to avoid division issues

    total_engagement = score + (comments * 2)  # Comments weighted 2x
    velocity = total_engagement / age_hours

    return round(velocity, 2)


def get_velocity_bonus(velocity: float) -> float:
    """
    Calculate score bonus based on engagement velocity.

    Args:
        velocity: Engagement per hour.

    Returns:
        Score bonus (0-15 points).
    """
    if velocity >= 50:
        return 15  # Viral content
    elif velocity >= 20:
        return 10  # Hot content
    elif velocity >= 10:
        return 7  # Rising content
    elif velocity >= 5:
        return 4  # Active content
    elif velocity >= 2:
        return 2  # Moderate activity
    return 0  # Low activity


def contains_numbers(text: str) -> bool:
    """Check if text contains numeric values (potential metrics)."""
    # Look for patterns like percentages, dollar amounts, or standalone numbers
    patterns = [
        r"\d+%",  # Percentages
        r"\$\d+",  # Dollar amounts
        r"\d+k\b",  # Thousands (e.g., "100k")
        r"\d+\s*(views|visitors|users|clicks|sessions)",  # Traffic metrics
        r"increased\s+by\s+\d+",  # Increase mentions
        r"\d+\s*x\b",  # Multipliers (e.g., "3x")
    ]
    for pattern in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def get_source_tier(source_type: str, source_id: str) -> int:
    """Get the tier for a source. Returns 2 (medium) if not found."""
    sources = get_sources_by_type(source_type, enabled_only=False)
    for source in sources:
        if source.source_id == source_id:
            return source.tier
    return 2  # Default to medium tier


def calculate_reddit_score(
    thread: RedditThread,
    keyword_matches: list[KeywordMatch],
    source_tier: int = 2,
) -> float:
    """
    Calculate relevance score for a Reddit thread (0-100 scale).

    Scoring breakdown:
    - Engagement signals: max 40 points
    - Keyword matches: max 35 points
    - Content quality: max 15 points
    - Source tier bonus: max 10 points

    Args:
        thread: The Reddit thread to score.
        keyword_matches: List of keyword matches found in content.
        source_tier: Source tier (1=high, 2=medium, 3=low).

    Returns:
        Relevance score from 0-100.
    """
    score = 0.0

    # === Engagement signals (max 40 points) ===
    # Up to 20 pts for upvotes (1 point per 2.5 upvotes, capped at 20)
    score += min(thread.score / 2.5, 20)

    # Up to 15 pts for comments (1 point per ~1.3 comments, capped at 15)
    score += min(thread.num_comments / 1.33, 15)

    # Bonus for viral posts (100+ upvotes)
    if thread.score > 100:
        score += 5

    # === Keyword matches (max 35 points) ===
    keyword_score = 0.0
    for match in keyword_matches:
        # Weight * 5 points per match, with diminishing returns
        keyword_score += min(match.count, 3) * match.weight * 5
    score += min(keyword_score, 35)

    # === Content quality signals (max 15 points) ===
    text = (thread.title or "") + " " + (thread.selftext or "")

    # Has metrics/numbers (5 pts)
    if contains_numbers(text):
        score += 5

    # Detailed post - more than 500 chars (5 pts)
    if len(thread.selftext or "") > 500:
        score += 5

    # Quality flair (5 pts)
    quality_flairs = ["case study", "success", "strategy", "results", "guide", "tutorial"]
    if thread.flair and any(f in thread.flair.lower() for f in quality_flairs):
        score += 5

    # === Source tier bonus (max 10 points) ===
    if source_tier == 1:
        score += 10
    elif source_tier == 2:
        score += 5
    # Tier 3 gets no bonus

    # === Engagement velocity bonus (max 15 points) ===
    velocity = calculate_engagement_velocity(
        thread.score,
        thread.num_comments,
        thread.created_utc,
    )
    score += get_velocity_bonus(velocity)

    return min(score, 100)


def calculate_youtube_score(
    video: YouTubeVideo,
    keyword_matches: list[KeywordMatch],
    source_tier: int = 1,
) -> float:
    """
    Calculate relevance score for a YouTube video (0-100 scale).

    Scoring breakdown:
    - Engagement signals: max 30 points
    - Keyword matches: max 35 points
    - Content quality: max 20 points
    - Source tier bonus: max 15 points

    Args:
        video: The YouTube video to score.
        keyword_matches: List of keyword matches found in content.
        source_tier: Source tier (1=high, 2=medium, 3=low).

    Returns:
        Relevance score from 0-100.
    """
    score = 0.0

    # === Engagement signals (max 30 points) ===
    # Up to 15 pts for views (normalized for SEO content)
    score += min(video.view_count / 666.67, 15)  # ~10k views = 15 pts

    # Up to 10 pts for likes
    score += min(video.like_count / 50, 10)  # ~500 likes = 10 pts

    # High engagement ratio bonus (>4% like ratio)
    if video.view_count > 0:
        like_ratio = video.like_count / video.view_count
        if like_ratio > 0.04:
            score += 5

    # === Keyword matches (max 35 points) ===
    keyword_score = 0.0
    for match in keyword_matches:
        keyword_score += min(match.count, 5) * match.weight * 3  # Transcripts have more text
    score += min(keyword_score, 35)

    # === Content quality signals (max 20 points) ===
    # Sweet spot duration: 10-40 minutes (10 pts)
    duration = video.duration_seconds or 0
    if 600 <= duration <= 2400:
        score += 10
    elif 300 <= duration < 600 or 2400 < duration <= 3600:
        score += 5

    # Transcript available (5 pts)
    if video.transcript_available:
        score += 5

    # Substantial transcript content (5 pts)
    if video.transcript and len(video.transcript) > 2000:
        score += 5

    # === Source tier bonus (max 15 points) ===
    if source_tier == 1:
        score += 15
    elif source_tier == 2:
        score += 8
    # Tier 3 gets no bonus

    return min(score, 100)


def process_reddit_thread(
    item: ContentItem,
    matcher: KeywordMatcher | None = None,
) -> RedditThread:
    """
    Process a Reddit content item: score it, classify it, and convert to model.

    Args:
        item: ContentItem from the Reddit source.
        matcher: Optional KeywordMatcher instance. Uses default if not provided.

    Returns:
        Fully processed RedditThread model.
    """
    if matcher is None:
        matcher = get_matcher()

    # Find keyword matches
    full_text = item.title + " " + item.content
    matches = matcher.find_matches(full_text)

    # Get source tier
    source_tier = get_source_tier("reddit", item.source_id)

    # Create thread model
    import hashlib
    from datetime import datetime

    content_hash = hashlib.sha256(full_text.encode()).hexdigest()

    thread = RedditThread(
        id=item.id,
        subreddit=item.source_id,
        title=item.title,
        author=item.metadata.get("author"),
        selftext=item.content,
        url=item.url,
        score=item.metadata.get("score", 0),
        num_comments=item.metadata.get("num_comments", 0),
        created_utc=int(item.created_at.timestamp()),
        flair=item.metadata.get("flair"),
        captured_at=int(datetime.now().timestamp()),
        content_hash=content_hash,
        matched_keywords=matcher.get_matched_keywords(matches),
    )

    # Calculate relevance score
    thread.relevance_score = calculate_reddit_score(thread, matches, source_tier)

    # Classify content
    thread.category = classify_content(full_text, matches)

    return thread


def process_youtube_video(
    item: ContentItem,
    matcher: KeywordMatcher | None = None,
) -> YouTubeVideo:
    """
    Process a YouTube content item: score it, classify it, and convert to model.

    Args:
        item: ContentItem from the YouTube source.
        matcher: Optional KeywordMatcher instance. Uses default if not provided.

    Returns:
        Fully processed YouTubeVideo model.
    """
    if matcher is None:
        matcher = get_matcher()

    # Find keyword matches in title and transcript
    full_text = item.title + " " + (item.content or "")
    matches = matcher.find_matches(full_text)

    # Get source tier
    source_tier = get_source_tier("youtube", item.source_id)

    # Create video model
    import hashlib
    from datetime import datetime

    content_hash = hashlib.sha256(full_text.encode()).hexdigest()

    video = YouTubeVideo(
        id=item.id,
        channel_id=item.source_id,
        channel_name=item.metadata.get("channel_name"),
        title=item.title,
        description=item.metadata.get("description"),
        url=item.url,
        duration_seconds=item.metadata.get("duration_seconds"),
        view_count=item.metadata.get("view_count", 0),
        like_count=item.metadata.get("like_count", 0),
        published_at=int(item.created_at.timestamp()),
        transcript=item.content if item.content else None,
        transcript_available=item.metadata.get("transcript_available", False),
        captured_at=int(datetime.now().timestamp()),
        content_hash=content_hash,
        matched_keywords=matcher.get_matched_keywords(matches),
    )

    # Calculate relevance score
    video.relevance_score = calculate_youtube_score(video, matches, source_tier)

    # Classify content
    video.category = classify_content(full_text, matches)

    return video


def calculate_hackernews_score(
    points: int,
    num_comments: int,
    created_utc: int,
    keyword_matches: list[KeywordMatch],
    story_type: str = "story",
) -> float:
    """
    Calculate relevance score for a Hacker News item (0-100 scale).

    Scoring breakdown:
    - Engagement signals: max 40 points
    - Keyword matches: max 35 points
    - Content signals: max 15 points
    - Velocity bonus: max 10 points

    Args:
        points: HN points (upvotes).
        num_comments: Number of comments.
        created_utc: Unix timestamp of creation.
        keyword_matches: List of keyword matches found.
        story_type: "story", "ask_hn", or "show_hn".

    Returns:
        Relevance score from 0-100.
    """
    score = 0.0

    # === Engagement signals (max 40 points) ===
    # HN points are harder to get than Reddit upvotes
    score += min(points / 2, 25)  # Up to 25 pts for 50+ points

    # Comments are valuable on HN
    score += min(num_comments / 2, 15)  # Up to 15 pts for 30+ comments

    # === Keyword matches (max 35 points) ===
    keyword_score = 0.0
    for match in keyword_matches:
        keyword_score += min(match.count, 3) * match.weight * 5
    score += min(keyword_score, 35)

    # === Content type bonus (max 15 points) ===
    # Ask HN often has valuable discussions
    if story_type == "ask_hn":
        score += 10
    elif story_type == "show_hn":
        score += 5

    # High comment ratio indicates discussion-worthy content
    if points > 0 and num_comments / points > 0.5:
        score += 5

    # === Velocity bonus (max 10 points) ===
    velocity = calculate_engagement_velocity(points, num_comments, created_utc)
    score += min(get_velocity_bonus(velocity), 10)

    return min(score, 100)


def process_hackernews_item(
    item: ContentItem,
    matcher: KeywordMatcher | None = None,
) -> dict:
    """
    Process a Hacker News content item: score it, classify it, return data dict.

    Args:
        item: ContentItem from the HackerNews source.
        matcher: Optional KeywordMatcher instance.

    Returns:
        Dict with processed HN item data ready for database insertion.
    """
    import hashlib
    from datetime import datetime

    if matcher is None:
        matcher = get_matcher()

    # Find keyword matches
    full_text = item.title + " " + (item.content or "")
    matches = matcher.find_matches(full_text)

    content_hash = hashlib.sha256(full_text.encode()).hexdigest()

    # Calculate score
    relevance_score = calculate_hackernews_score(
        points=item.metadata.get("points", 0),
        num_comments=item.metadata.get("num_comments", 0),
        created_utc=int(item.created_at.timestamp()),
        keyword_matches=matches,
        story_type=item.metadata.get("story_type", "story"),
    )

    # Classify content
    category = classify_content(full_text, matches)

    return {
        "id": item.id,
        "title": item.title,
        "author": item.metadata.get("author"),
        "story_text": item.content,
        "url": item.url,
        "external_url": item.metadata.get("external_url"),
        "points": item.metadata.get("points", 0),
        "num_comments": item.metadata.get("num_comments", 0),
        "created_utc": int(item.created_at.timestamp()),
        "story_type": item.metadata.get("story_type", "story"),
        "captured_at": int(datetime.now().timestamp()),
        "content_hash": content_hash,
        "relevance_score": relevance_score,
        "matched_keywords": matcher.get_matched_keywords(matches),
        "category": category,
    }
