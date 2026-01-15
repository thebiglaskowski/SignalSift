"""SQLite schema definitions for SignalSift."""

SCHEMA_SQL = """
-- ============================================================================
-- Core content tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS reddit_threads (
    id TEXT PRIMARY KEY,              -- Reddit's thing ID (e.g., "t3_abc123")
    subreddit TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT,
    selftext TEXT,                    -- Post body content
    url TEXT NOT NULL,
    score INTEGER DEFAULT 0,          -- Upvotes at capture time
    num_comments INTEGER DEFAULT 0,
    created_utc INTEGER NOT NULL,     -- Unix timestamp
    flair TEXT,

    -- Processing metadata
    captured_at INTEGER NOT NULL,     -- When we scraped it
    content_hash TEXT,                -- SHA256 of title+selftext for change detection
    relevance_score REAL DEFAULT 0,   -- Our calculated score
    matched_keywords TEXT,            -- JSON array of matched keywords
    category TEXT,                    -- "pain_point", "success_story", "tool_mention", etc.

    -- Report tracking
    processed INTEGER DEFAULT 0,      -- 0=new, 1=included in a report
    report_id TEXT,                   -- Which report included this

    UNIQUE(id)
);

CREATE INDEX IF NOT EXISTS idx_reddit_subreddit ON reddit_threads(subreddit);
CREATE INDEX IF NOT EXISTS idx_reddit_created ON reddit_threads(created_utc);
CREATE INDEX IF NOT EXISTS idx_reddit_processed ON reddit_threads(processed);
CREATE INDEX IF NOT EXISTS idx_reddit_score ON reddit_threads(relevance_score);

CREATE TABLE IF NOT EXISTS youtube_videos (
    id TEXT PRIMARY KEY,              -- YouTube video ID
    channel_id TEXT NOT NULL,
    channel_name TEXT,
    title TEXT NOT NULL,
    description TEXT,
    url TEXT NOT NULL,
    duration_seconds INTEGER,
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    published_at INTEGER NOT NULL,    -- Unix timestamp

    -- Transcript data
    transcript TEXT,                  -- Full transcript text
    transcript_available INTEGER DEFAULT 0,

    -- Processing metadata
    captured_at INTEGER NOT NULL,
    content_hash TEXT,                -- SHA256 of title+transcript
    relevance_score REAL DEFAULT 0,
    matched_keywords TEXT,            -- JSON array
    category TEXT,

    -- Report tracking
    processed INTEGER DEFAULT 0,
    report_id TEXT,

    UNIQUE(id)
);

CREATE INDEX IF NOT EXISTS idx_youtube_channel ON youtube_videos(channel_id);
CREATE INDEX IF NOT EXISTS idx_youtube_published ON youtube_videos(published_at);
CREATE INDEX IF NOT EXISTS idx_youtube_processed ON youtube_videos(processed);

-- Report tracking
CREATE TABLE IF NOT EXISTS reports (
    id TEXT PRIMARY KEY,              -- UUID
    generated_at INTEGER NOT NULL,
    filepath TEXT NOT NULL,
    reddit_count INTEGER DEFAULT 0,
    youtube_count INTEGER DEFAULT 0,
    date_range_start INTEGER,
    date_range_end INTEGER,
    config_snapshot TEXT              -- JSON of config used for this report
);

-- Keyword configuration (can be updated without code changes)
CREATE TABLE IF NOT EXISTS keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT NOT NULL,           -- "success", "pain_point", "tool", "technique"
    weight REAL DEFAULT 1.0,          -- Scoring weight
    enabled INTEGER DEFAULT 1,

    UNIQUE(keyword, category)
);

-- Source configuration
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,        -- "reddit" or "youtube"
    source_id TEXT NOT NULL,          -- subreddit name or channel ID
    display_name TEXT,
    tier INTEGER DEFAULT 2,           -- 1=high, 2=medium, 3=low priority
    enabled INTEGER DEFAULT 1,
    last_fetched INTEGER,

    UNIQUE(source_type, source_id)
);

-- Processing log for debugging
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,
    action TEXT NOT NULL,             -- "scan", "report", "cache_hit", "error"
    source_type TEXT,
    source_id TEXT,
    details TEXT                      -- JSON with additional info
);

-- ============================================================================
-- Hacker News content table
-- ============================================================================

CREATE TABLE IF NOT EXISTS hackernews_items (
    id TEXT PRIMARY KEY,              -- HN item ID (prefixed with "hn_")
    title TEXT NOT NULL,
    author TEXT,
    story_text TEXT,                  -- Content for Ask HN / Show HN posts
    url TEXT NOT NULL,                -- HN discussion URL
    external_url TEXT,                -- External link if any
    points INTEGER DEFAULT 0,
    num_comments INTEGER DEFAULT 0,
    created_utc INTEGER NOT NULL,     -- Unix timestamp
    story_type TEXT,                  -- "story", "ask_hn", "show_hn"

    -- Processing metadata
    captured_at INTEGER NOT NULL,
    content_hash TEXT,
    relevance_score REAL DEFAULT 0,
    matched_keywords TEXT,            -- JSON array
    category TEXT,

    -- Report tracking
    processed INTEGER DEFAULT 0,
    report_id TEXT,

    UNIQUE(id)
);

CREATE INDEX IF NOT EXISTS idx_hn_created ON hackernews_items(created_utc);
CREATE INDEX IF NOT EXISTS idx_hn_processed ON hackernews_items(processed);
CREATE INDEX IF NOT EXISTS idx_hn_score ON hackernews_items(relevance_score);

-- ============================================================================
-- Trend tracking tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS keyword_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT NOT NULL,
    period_start TEXT NOT NULL,       -- ISO timestamp
    period_end TEXT NOT NULL,
    mention_count INTEGER NOT NULL,
    avg_engagement REAL NOT NULL,
    sample_titles TEXT,               -- JSON array
    created_at TEXT NOT NULL,

    UNIQUE(keyword, period_start, period_end)
);

CREATE INDEX IF NOT EXISTS idx_trends_keyword ON keyword_trends(keyword);
CREATE INDEX IF NOT EXISTS idx_trends_period ON keyword_trends(period_start, period_end);

-- ============================================================================
-- Competitive intelligence tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS tool_mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    category TEXT,                    -- Tool category (backlink, content, etc.)
    sentiment TEXT,                   -- positive, negative, neutral, switching_from, switching_to
    sentiment_score REAL,             -- -1.0 to 1.0
    context TEXT,                     -- Surrounding text
    source_type TEXT,                 -- reddit, youtube, hackernews
    source_id TEXT,                   -- ID of the source item
    source_title TEXT,
    captured_at TEXT NOT NULL,

    UNIQUE(tool_name, source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_tool_mentions_tool ON tool_mentions(tool_name);
CREATE INDEX IF NOT EXISTS idx_tool_mentions_date ON tool_mentions(captured_at);
CREATE INDEX IF NOT EXISTS idx_tool_mentions_sentiment ON tool_mentions(sentiment);

-- ============================================================================
-- Enhanced content analysis tables
-- ============================================================================

CREATE TABLE IF NOT EXISTS content_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,        -- reddit, youtube, hackernews
    source_id TEXT NOT NULL,          -- ID of the analyzed item
    analysis_type TEXT NOT NULL,      -- llm, sentiment, entity
    analysis_data TEXT NOT NULL,      -- JSON with analysis results
    analyzed_at TEXT NOT NULL,

    UNIQUE(source_type, source_id, analysis_type)
);

CREATE INDEX IF NOT EXISTS idx_analysis_source ON content_analysis(source_type, source_id);

-- ============================================================================
-- Engagement velocity tracking (for delta reports)
-- ============================================================================

CREATE TABLE IF NOT EXISTS engagement_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    snapshot_time INTEGER NOT NULL,   -- Unix timestamp
    score INTEGER,                    -- Upvotes/points at snapshot time
    comments INTEGER,                 -- Comments at snapshot time
    views INTEGER,                    -- Views (YouTube only)

    UNIQUE(source_type, source_id, snapshot_time)
);

CREATE INDEX IF NOT EXISTS idx_snapshots_source ON engagement_snapshots(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON engagement_snapshots(snapshot_time);
"""


def get_schema_sql() -> str:
    """Return the complete schema SQL."""
    return SCHEMA_SQL
