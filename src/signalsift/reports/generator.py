"""Report generation for SignalSift."""

import json
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from signalsift import __version__
from signalsift.config import get_settings
from signalsift.database.models import RedditThread, Report, YouTubeVideo
from signalsift.database.queries import (
    get_cache_stats,
    get_unprocessed_content,
    insert_report,
    mark_content_processed,
)
from signalsift.exceptions import ReportError
from signalsift.processing.classification import get_category_name
from signalsift.processing.scoring import calculate_engagement_velocity
from signalsift.utils.logging import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """Generate markdown reports from cached content."""

    def __init__(self) -> None:
        """Initialize the report generator."""
        self.settings = get_settings()
        self._env: Environment | None = None

    @property
    def env(self) -> Environment:
        """Get or create the Jinja2 environment."""
        if self._env is None:
            template_dir = Path(__file__).parent / "templates"
            self._env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            # Add custom filters
            self._env.filters["truncate"] = self._truncate
            self._env.filters["format_number"] = self._format_number
            self._env.filters["format_datetime"] = self._format_datetime
        return self._env

    def generate(
        self,
        output_path: Path | None = None,
        min_score: float | None = None,
        since_days: int | None = None,
        max_items: int | None = None,
        include_processed: bool = False,
        preview: bool = False,
        delta: bool = False,
        include_trends: bool = True,
        include_competitive: bool = True,
    ) -> Path:
        """
        Generate a markdown report.

        Args:
            output_path: Custom output path. Uses default if not provided.
            min_score: Minimum relevance score to include.
            since_days: Only include content from last N days.
            max_items: Maximum items per section.
            include_processed: Include previously processed content.
            preview: If True, don't mark content as processed.
            delta: If True, only include new content since last report.
            include_trends: Include trend analysis section.
            include_competitive: Include competitive intelligence section.

        Returns:
            Path to the generated report.
        """
        # Get content
        if include_processed:
            from signalsift.database.queries import get_reddit_threads, get_youtube_videos

            since_timestamp = None
            if since_days:
                since_timestamp = int(
                    (datetime.now() - __import__("datetime").timedelta(days=since_days)).timestamp()
                )

            threads = get_reddit_threads(
                since_timestamp=since_timestamp,
                min_score=min_score,
                limit=max_items,
            )
            videos = get_youtube_videos(
                since_timestamp=since_timestamp,
                min_score=min_score,
                limit=max_items,
            )
        else:
            threads, videos = get_unprocessed_content(
                min_score=min_score or self.settings.scoring.min_relevance_score,
                since_days=since_days,
                reddit_limit=max_items,
                youtube_limit=max_items,
            )

        if not threads and not videos:
            raise ReportError("No content to include in report")

        # Build context
        context = self._build_context(
            threads,
            videos,
            include_trends=include_trends,
            include_competitive=include_competitive,
        )

        # Render template
        template = self.env.get_template("default.md.j2")
        content = template.render(**context)

        # Determine output path
        if output_path is None:
            output_path = self._get_default_output_path()

        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")

        logger.info(f"Report generated: {output_path}")

        # Create report record and mark content as processed
        if not preview:
            report_id = str(uuid.uuid4())
            report = Report(
                id=report_id,
                generated_at=int(datetime.now().timestamp()),
                filepath=str(output_path),
                reddit_count=len(threads),
                youtube_count=len(videos),
                date_range_start=min(
                    [t.created_utc for t in threads] + [v.published_at for v in videos]
                )
                if threads or videos
                else None,
                date_range_end=max(
                    [t.created_utc for t in threads] + [v.published_at for v in videos]
                )
                if threads or videos
                else None,
                config_snapshot=json.dumps(
                    {
                        "min_score": min_score,
                        "since_days": since_days,
                        "max_items": max_items,
                    }
                ),
            )
            insert_report(report)

            mark_content_processed(
                report_id=report_id,
                thread_ids=[t.id for t in threads],
                video_ids=[v.id for v in videos],
            )

        return output_path

    def _build_context(
        self,
        threads: list[RedditThread],
        videos: list[YouTubeVideo],
        include_trends: bool = True,
        include_competitive: bool = True,
    ) -> dict[str, Any]:
        """Build the template context from content."""
        now = datetime.now()

        # Add velocity to threads for "rising" detection
        threads_with_velocity = []
        for thread in threads:
            velocity = calculate_engagement_velocity(
                thread.score,
                thread.num_comments,
                thread.created_utc,
            )
            # Attach velocity as attribute for template use
            thread_dict = {
                "thread": thread,
                "velocity": velocity,
                "is_rising": velocity >= 10,  # Rising if >10 engagement/hour
            }
            threads_with_velocity.append(thread_dict)

        # Sort by velocity to identify rising content
        rising_content = sorted(
            threads_with_velocity,
            key=lambda x: x["velocity"],
            reverse=True,
        )[:10]

        # Get trend analysis if enabled
        trends_data = None
        if include_trends:
            try:
                from signalsift.processing.trends import analyze_trends
                trends_data = analyze_trends(current_period_days=7)
            except Exception as e:
                logger.warning(f"Could not get trend data: {e}")

        # Get competitive intelligence if enabled
        competitive_data = None
        if include_competitive:
            try:
                from signalsift.processing.competitive import get_competitive_intel
                intel = get_competitive_intel()
                competitive_data = {
                    "tool_stats": intel.get_tool_stats(days=30)[:10],
                    "feature_gaps": intel.identify_feature_gaps(days=30)[:5],
                    "market_movers": intel.get_market_movers(days=30),
                }
            except Exception as e:
                logger.warning(f"Could not get competitive data: {e}")

        # Calculate date range
        all_timestamps = [t.created_utc for t in threads] + [v.published_at for v in videos]
        date_range_start = datetime.fromtimestamp(min(all_timestamps)) if all_timestamps else now
        date_range_end = datetime.fromtimestamp(max(all_timestamps)) if all_timestamps else now

        # Group content by category
        pain_points = [t for t in threads if t.category == "pain_point"]
        success_stories = [t for t in threads if t.category == "success_story"]
        tool_mentions = [t for t in threads if t.category == "tool_comparison"]

        # Monetization intelligence
        monetization_items = [
            t for t in threads if t.category in ("monetization", "roi_analysis", "ecommerce")
        ]

        # AI visibility
        ai_visibility_items = [t for t in threads if t.category == "ai_visibility"]

        # Keyword research
        keyword_research_items = [
            t for t in threads if t.category in ("keyword_research", "local_seo")
        ]

        # Content generation
        content_generation_items = [t for t in threads if t.category == "ai_content"]

        # Competition analysis
        competition_items = [
            t for t in threads if t.category in ("competitor_analysis", "content_brief")
        ]

        # Image generation
        image_generation_items = [t for t in threads if t.category == "image_generation"]

        # Static sites and performance
        static_sites_items = [t for t in threads if t.category == "static_sites"]

        # Sort all categories by relevance
        for item_list in [
            pain_points,
            success_stories,
            tool_mentions,
            monetization_items,
            ai_visibility_items,
            keyword_research_items,
            content_generation_items,
            competition_items,
            image_generation_items,
            static_sites_items,
        ]:
            item_list.sort(key=lambda x: x.relevance_score, reverse=True)

        # Group by source
        reddit_by_subreddit: dict[str, list[RedditThread]] = defaultdict(list)
        for thread in threads:
            reddit_by_subreddit[thread.subreddit].append(thread)

        youtube_by_channel: dict[str, list[YouTubeVideo]] = defaultdict(list)
        for video in videos:
            channel = video.channel_name or video.channel_id
            youtube_by_channel[channel].append(video)

        # Get top themes (most common categories)
        category_counts: dict[str, int] = defaultdict(int)
        for thread in threads:
            if thread.category:
                category_counts[thread.category] += 1
        for video in videos:
            if video.category:
                category_counts[video.category] += 1

        top_themes = [
            get_category_name(cat)
            for cat, _ in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        # Get cache stats
        cache_stats = get_cache_stats()

        # Build sources summary
        reddit_sources = len(reddit_by_subreddit)
        youtube_sources = len(youtube_by_channel)
        sources_summary = f"{reddit_sources} subreddits, {youtube_sources} YouTube channels"

        # Limit items per section
        max_per_section = self.settings.reports.max_items_per_section
        excerpt_length = self.settings.reports.excerpt_length

        return {
            # Report metadata
            "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date_range_start": date_range_start.strftime("%Y-%m-%d"),
            "date_range_end": date_range_end.strftime("%Y-%m-%d"),
            "sources_summary": sources_summary,
            "version": __version__,
            # Summary stats
            "reddit_count": len(threads),
            "youtube_count": len(videos),
            "new_count": len(threads) + len(videos),
            "top_themes": top_themes,
            # Categorized content
            "pain_points": [
                self._thread_to_context(t, excerpt_length) for t in pain_points[:max_per_section]
            ],
            "success_stories": [
                self._thread_to_context(t, excerpt_length)
                for t in success_stories[:max_per_section]
            ],
            "tool_mentions": [
                self._thread_to_context(t, excerpt_length) for t in tool_mentions[:max_per_section]
            ],
            "monetization_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in monetization_items[:max_per_section]
            ],
            "ai_visibility_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in ai_visibility_items[:max_per_section]
            ],
            "keyword_research_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in keyword_research_items[:max_per_section]
            ],
            "content_generation_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in content_generation_items[:max_per_section]
            ],
            "competition_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in competition_items[:max_per_section]
            ],
            "image_generation_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in image_generation_items[:max_per_section]
            ],
            "static_sites_insights": [
                self._thread_to_context(t, excerpt_length)
                for t in static_sites_items[:max_per_section]
            ],
            # YouTube content
            "youtube_videos": [
                self._video_to_context(v, excerpt_length) for v in videos[:max_per_section]
            ],
            # Full index
            "reddit_by_subreddit": {
                sub: [self._thread_to_context(t, excerpt_length) for t in threads_list]
                for sub, threads_list in reddit_by_subreddit.items()
            },
            "youtube_by_channel": {
                channel: [self._video_to_context(v, excerpt_length) for v in videos_list]
                for channel, videos_list in youtube_by_channel.items()
            },
            # Rising content (high engagement velocity)
            "rising_content": [
                {
                    **self._thread_to_context(item["thread"], excerpt_length),
                    "velocity": item["velocity"],
                }
                for item in rising_content
                if item["is_rising"]
            ],
            # Trend analysis
            "trends": (
                [
                    {
                        "topic": t.topic,
                        "change": f"+{t.change_percent}%" if t.change_percent > 0 else f"{t.change_percent}%",
                        "direction": t.direction,
                        "mention_count": t.current_count,
                    }
                    for t in trends_data.emerging[:5]
                ]
                if trends_data
                else []
            ),
            "emerging_trends": (
                [{"topic": t.topic, "change": f"+{t.change_percent}%", "count": t.current_count}
                 for t in trends_data.emerging[:5]]
                if trends_data else []
            ),
            "declining_trends": (
                [{"topic": t.topic, "change": f"{t.change_percent}%", "count": t.current_count}
                 for t in trends_data.declining[:5]]
                if trends_data else []
            ),
            "new_topics": (
                [{"topic": t.topic, "count": t.current_count} for t in trends_data.new_topics[:5]]
                if trends_data else []
            ),
            # Competitive intelligence
            "competitive_intel": competitive_data,
            "top_tools": (
                [
                    {
                        "name": s.tool_name,
                        "mentions": s.mention_count,
                        "sentiment": "positive" if s.avg_sentiment > 0.1 else "negative" if s.avg_sentiment < -0.1 else "neutral",
                    }
                    for s in competitive_data["tool_stats"][:5]
                ]
                if competitive_data else []
            ),
            "feature_gaps": (
                [
                    {
                        "tool": g.tool,
                        "description": g.feature_description[:100],
                        "demand": g.demand_level,
                        "opportunity": g.opportunity,
                    }
                    for g in competitive_data["feature_gaps"][:5]
                ]
                if competitive_data else []
            ),
            # Cache stats
            "cache_stats": cache_stats,
        }

    def _thread_to_context(
        self, thread: RedditThread, excerpt_length: int
    ) -> dict[str, Any]:
        """Convert a Reddit thread to template context."""
        excerpt = (thread.selftext or "")[:excerpt_length]
        if len(thread.selftext or "") > excerpt_length:
            excerpt += "..."

        return {
            "title": thread.title,
            "url": thread.url,
            "source_badge": f"r/{thread.subreddit}",
            "relevance_score": round(thread.relevance_score),
            "engagement": f"{thread.score}↑ · {thread.num_comments} comments",
            "excerpt": excerpt,
            "category": thread.category,
            "score": thread.score,
            "num_comments": thread.num_comments,
            "matched_keywords": thread.matched_keywords,
            # Optional insight fields (populated by AI analysis if enabled)
            "feature_suggestion": None,
            "takeaway": None,
            "monetization_angle": None,
            "geo_opportunity": None,
            "keyword_opportunity": None,
            "content_strategy": None,
            "competitive_angle": None,
            "image_opportunity": None,
            "tech_insight": None,
        }

    def _video_to_context(
        self, video: YouTubeVideo, excerpt_length: int
    ) -> dict[str, Any]:
        """Convert a YouTube video to template context."""
        transcript_excerpt = (video.transcript or "")[:excerpt_length]
        if len(video.transcript or "") > excerpt_length:
            transcript_excerpt += "..."

        return {
            "title": video.title,
            "url": video.url,
            "channel_name": video.channel_name or video.channel_id,
            "relevance_score": round(video.relevance_score),
            "view_count": video.view_count,
            "like_count": video.like_count,
            "duration_formatted": video.duration_formatted,
            "duration_seconds": video.duration_seconds,
            "transcript_excerpt": transcript_excerpt,
            "transcript_available": video.transcript_available,
            "category": video.category,
            "matched_keywords": video.matched_keywords,
            "insights": None,
        }

    def _get_default_output_path(self) -> Path:
        """Get the default output path for a report."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = self.settings.reports.filename_format.format(
            date=date_str,
            time=datetime.now().strftime("%H%M%S"),
        )
        return self.settings.reports.output_directory / filename

    @staticmethod
    def _truncate(text: str, length: int = 50) -> str:
        """Truncate text to specified length."""
        if len(text) <= length:
            return text
        return text[: length - 3] + "..."

    @staticmethod
    def _format_number(value: int) -> str:
        """Format large numbers (e.g., 1500 -> 1.5K)."""
        if value >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if value >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)

    @staticmethod
    def _format_datetime(timestamp: int) -> str:
        """Format a Unix timestamp as a date string."""
        return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


def generate_report(**kwargs: Any) -> Path:
    """Convenience function to generate a report."""
    generator = ReportGenerator()
    return generator.generate(**kwargs)
