"""Content classification for SignalSift."""

from signalsift.processing.keywords import KeywordMatch

# Category signals for classification
CATEGORY_SIGNALS: dict[str, list[str]] = {
    # === Core pain points and success stories (All packages) ===
    "pain_point": [
        "struggling",
        "frustrated",
        "can't",
        "cannot",
        "help",
        "wish",
        "problem",
        "issue",
        "bug",
        "broken",
        "doesn't work",
        "not working",
        "traffic dropped",
        "lost rankings",
    ],
    "success_story": [
        "increased",
        "results",
        "case study",
        "working",
        "success",
        "achieved",
        "finally",
        "breakthrough",
        "doubled",
        "tripled",
        "hit first page",
        "ranking #1",
    ],
    "tool_comparison": [
        "vs",
        "versus",
        "compared",
        "comparison",
        "switched",
        "better than",
        "alternative",
        "instead of",
    ],
    "technique": [
        "strategy",
        "method",
        "approach",
        "how to",
        "tutorial",
        "guide",
        "step by step",
        "walkthrough",
    ],
    "industry_news": [
        "update",
        "algorithm",
        "announcement",
        "change",
        "news",
        "released",
        "launched",
        "rollout",
    ],

    # === ProfitForge-relevant categories ===
    "monetization": [
        "affiliate",
        "commission",
        "rpm",
        "revenue",
        "income",
        "adsense",
        "mediavine",
        "profit",
        "earnings",
        "monetize",
        "cpc",
        "cpm",
    ],
    "roi_analysis": [
        "roi",
        "return on investment",
        "cost per",
        "investment",
        "payoff",
        "break even",
    ],
    "ecommerce": [
        "amazon affiliate",
        "dropshipping",
        "shopify",
        "woocommerce",
        "product reviews",
        "buyer guide",
        "amazon associates",
    ],

    # === GEOForge-relevant categories ===
    "ai_visibility": [
        "chatgpt",
        "perplexity",
        "ai overview",
        "sge",
        "citation",
        "llm",
        "ai search",
        "gemini",
        "ai answers",
        "generative search",
    ],

    # === KeyForge-relevant categories ===
    "ai_content": [
        "ai writer",
        "ai generated",
        "ai detection",
        "bulk content",
        "ai writing",
        "generated content",
        "gpt-4",
        "content at scale",
    ],

    # === ImageForge-relevant categories ===
    "image_generation": [
        "dall-e",
        "midjourney",
        "stable diffusion",
        "ai images",
        "featured image",
        "ai art",
        "image generator",
    ],

    # === StaticForge-relevant categories ===
    "static_sites": [
        "static site",
        "jamstack",
        "page speed",
        "core web vitals",
        "lighthouse",
        "schema markup",
        "structured data",
    ],

    # === SniperForge-relevant categories ===
    "competitor_analysis": [
        "competitor",
        "outrank",
        "beat",
        "competition",
        "rival",
        "market leader",
        "content gap",
        "backlink gap",
    ],
    "content_brief": [
        "content brief",
        "outline",
        "structure",
        "format",
        "template",
        "framework",
    ],

    # === SeedForge/GapForge-relevant categories ===
    "keyword_research": [
        "keyword research",
        "keyword difficulty",
        "search volume",
        "long tail",
        "keyword gap",
        "seed keywords",
        "low competition",
        "people also ask",
    ],
    "local_seo": [
        "local seo",
        "google business",
        "local pack",
        "map pack",
        "local citations",
        "near me",
    ],
}

# Human-readable category names
CATEGORY_NAMES: dict[str, str] = {
    "pain_point": "Pain Point / Feature Opportunity",
    "success_story": "Success Story",
    "tool_comparison": "Tool Comparison",
    "technique": "Technique / Strategy",
    "industry_news": "Industry News",
    "monetization": "Monetization Intelligence (ProfitForge)",
    "roi_analysis": "ROI Analysis (ProfitForge)",
    "ecommerce": "E-commerce (ProfitForge)",
    "ai_visibility": "AI Visibility / GEO (GEOForge)",
    "ai_content": "AI Content Generation (KeyForge)",
    "image_generation": "Image Generation (ImageForge)",
    "static_sites": "Static Sites / Technical (StaticForge)",
    "competitor_analysis": "Competitor Analysis (SniperForge)",
    "content_brief": "Content Brief / Structure (SniperForge)",
    "keyword_research": "Keyword Research (SeedForge/GapForge)",
    "local_seo": "Local SEO (SeedForge/GapForge)",
    "general": "General",
}

# Map keyword categories from defaults.py to classification categories
KEYWORD_CATEGORY_MAP: dict[str, str] = {
    "success_signals": "success_story",
    "pain_points": "pain_point",
    "tool_mentions": "tool_comparison",
    "techniques": "technique",
    "keyword_research": "keyword_research",
    "monetization": "monetization",
    "ai_visibility": "ai_visibility",
    "content_generation": "ai_content",
    "image_generation": "image_generation",
    "static_sites": "static_sites",
    "competition": "competitor_analysis",
    "ecommerce": "ecommerce",
    "local_seo": "local_seo",
}


def classify_content(
    text: str,
    matched_keywords: list[KeywordMatch] | None = None,
) -> str:
    """
    Classify content into categories for report organization.

    Categories align with SEOForge suite packages for actionable insights.

    Args:
        text: The text content to classify.
        matched_keywords: Optional list of already-matched keywords.

    Returns:
        Category identifier string.
    """
    text_lower = text.lower()
    scores: dict[str, float] = {cat: 0.0 for cat in CATEGORY_SIGNALS}

    # Score based on signal presence
    for category, signals in CATEGORY_SIGNALS.items():
        for signal in signals:
            if signal in text_lower:
                scores[category] += 1.0

    # Factor in matched keyword categories
    if matched_keywords:
        for kw in matched_keywords:
            # Use the global category map
            mapped_category = KEYWORD_CATEGORY_MAP.get(kw.category)
            if mapped_category and mapped_category in scores:
                scores[mapped_category] += kw.weight * 2  # Keywords weighted more

    # Find the highest scoring category
    if scores:
        max_category = max(scores, key=scores.get)  # type: ignore
        if scores[max_category] > 0:
            return max_category

    return "general"


def get_category_name(category: str) -> str:
    """Get human-readable name for a category."""
    return CATEGORY_NAMES.get(category, category.replace("_", " ").title())


def get_primary_categories() -> list[str]:
    """Get list of primary category identifiers."""
    return list(CATEGORY_SIGNALS.keys())


def get_category_for_package(category: str) -> str | None:
    """
    Map a category to the most relevant SEOForge package.

    Returns:
        Package name or None if not directly related.
    """
    package_map = {
        # General categories relevant to all
        "pain_point": "All",
        "success_story": "All",
        "tool_comparison": "All",
        "technique": "SniperForge",
        "industry_news": "GEOForge",

        # ProfitForge - Monetization
        "monetization": "ProfitForge",
        "roi_analysis": "ProfitForge",
        "ecommerce": "ProfitForge",

        # GEOForge - AI Visibility
        "ai_visibility": "GEOForge",

        # KeyForge - Content Generation
        "ai_content": "KeyForge",

        # ImageForge - Image Generation
        "image_generation": "ImageForge",

        # StaticForge - Static Sites
        "static_sites": "StaticForge",

        # SniperForge - Competition Analysis
        "competitor_analysis": "SniperForge",
        "content_brief": "SniperForge",

        # SeedForge/GapForge - Keyword Research
        "keyword_research": "SeedForge/GapForge",
        "local_seo": "SeedForge/GapForge",
    }
    return package_map.get(category)
