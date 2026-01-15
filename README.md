# SignalSift

Personal community intelligence tool. Monitor Reddit, YouTube, and Hacker News for topics you care about.

## Features

- **Reddit Monitoring**: Track discussions via RSS (no API key needed) or API
- **YouTube Tracking**: Monitor channels and search for relevant videos
- **Hacker News**: Follow tech discussions and trends
- **Semantic Matching**: Find related content using spaCy word vectors
- **Trend Detection**: Identify rising topics and sentiment patterns
- **Markdown Reports**: Generate reports for review and analysis

## Installation

```bash
# Create conda environment
conda create -n signalsift python=3.11
conda activate signalsift

# Install package
pip install -e .

# Download spaCy model for semantic matching
python -m spacy download en_core_web_md
```

## Quick Start

```bash
# Initialize database with example sources
sift init

# Run a scan
sift scan

# Generate report
sift report

# Check status
sift status
```

## Configuration

1. Copy `.env.example` to `.env`
2. Add your API credentials (all optional):
   - **Reddit**: Works without credentials using RSS mode (default)
   - **YouTube**: Enable YouTube Data API v3 at Google Cloud Console
   - **OpenAI/Anthropic**: For optional LLM analysis

3. Customize `config.yaml`:
   - Add your subreddits of interest
   - Add YouTube channels to monitor
   - Configure keywords to track
   - Adjust scoring weights

## Reddit Modes

**RSS Mode** (default - no credentials needed):

```yaml
reddit:
  mode: "rss"
```

**API Mode** (requires approval):

```yaml
reddit:
  mode: "api"
```

## CLI Commands

```bash
sift init              # Initialize database
sift scan              # Scan all sources
sift scan --reddit     # Scan Reddit only
sift scan --youtube    # Scan YouTube only
sift report            # Generate markdown report
sift status            # Show database status
sift sources list      # List configured sources
sift sources add       # Add a source
sift keywords list     # List keywords
sift keywords add      # Add keywords
sift cache clear       # Clear old cached data
```

## Project Structure

```
SignalSift/
├── config.yaml         # Main configuration
├── .env                # API credentials (not in git)
├── data/               # SQLite database
├── logs/               # Log files
├── reports/            # Generated reports
└── src/signalsift/     # Source code
```

## License

MIT License - Personal use only.
