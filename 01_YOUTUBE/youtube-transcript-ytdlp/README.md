# YouTube Transcript Scraper (yt-dlp)

Alternative YouTube transcript downloader using **yt-dlp** instead of YouTube API.

## Why This Version?

- **No API key needed** - doesn't use YouTube Data API
- **Different rate limits** - may bypass transcript API limits
- **More robust** - yt-dlp is actively maintained
- **Auto-generated subs** - gets auto-generated captions automatically

## Quick Start

1. **Double-click `run.bat`**

That's it! The script will:

- Create virtual environment automatically
- Install dependencies
- Download all transcripts

## Configuration

Edit `scraper.py` to change:

```python
# Channels to scrape
CHANNELS = [
    "TruthisChrist",
    "AnswersInGenesis",
    # Add more...
]

# Limit videos (None = all)
MAX_VIDEOS = None  # or 10, 50, etc.
```

## Output

Transcripts saved to: `transcripts/<channel_name>/`

Files are in SRT format (subtitle format with timestamps).

## Manual Run

```powershell
# First time setup
python -m venv venv
.\venv\Scripts\pip.exe install -r requirements.txt

# Run scraper
.\venv\Scripts\python.exe scraper.py
```

## Advantages Over API Method

- No YouTube API quota limits
- No API key required
- Gets auto-generated captions
- More reliable for bulk downloads
- Different rate limiting system

## Note

This downloads subtitle files (.srt format) which include timestamps. If you want plain text, you can process the SRT files to remove timestamps.
