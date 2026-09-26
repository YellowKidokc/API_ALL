"""
YouTube Transcript Scraper using yt-dlp
Alternative method - doesn't use YouTube API for transcripts
"""

import os
import subprocess
import json
from pathlib import Path
from tqdm import tqdm

# Bible Contradiction Channels
CHANNELS = [
    "TruthisChrist",
    "AnswersInGenesis",
    "MikeWinger",
    "DanPaterson",
    "BibleNerdMinistries",
    "LivingWaters",
    "HolyKoolaid",
]

OUTPUT_DIR = "transcripts"
MAX_VIDEOS = None  # None = all videos, or set a number like 10


def download_channel_transcripts(channel_name):
    """Download all transcripts from a YouTube channel using yt-dlp"""
    
    channel_url = f"https://www.youtube.com/@{channel_name}"
    output_path = Path(OUTPUT_DIR) / channel_name
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Processing: @{channel_name}")
    print(f"{'='*60}")
    
    # yt-dlp command to download subtitles only
    cmd = [
        "yt-dlp",
        "--skip-download",  # Don't download video
        "--write-auto-subs",  # Get auto-generated subs
        "--write-subs",  # Get manual subs if available
        "--sub-lang", "en",  # English only
        "--sub-format", "vtt",  # VTT format
        "--convert-subs", "srt",  # Convert to SRT
        "--output", str(output_path / "%(title)s.%(ext)s"),
        "--playlist-end", str(MAX_VIDEOS) if MAX_VIDEOS else "999999",
        "--no-warnings",
        "--progress",
        channel_url + "/videos"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Count downloaded files
        subtitle_files = list(output_path.glob("*.srt")) + list(output_path.glob("*.vtt"))
        print(f"\n✅ Downloaded {len(subtitle_files)} transcripts for @{channel_name}")
        
        return len(subtitle_files)
    
    except Exception as e:
        print(f"❌ Error processing @{channel_name}: {e}")
        return 0


def main():
    print("="*60)
    print("YouTube Transcript Scraper (yt-dlp method)")
    print("="*60)
    print(f"\n📋 Channels: {len(CHANNELS)}")
    for i, ch in enumerate(CHANNELS, 1):
        print(f"   {i}. @{ch}")
    
    print(f"\n📁 Output: {OUTPUT_DIR}/")
    print(f"🎬 Max videos: {'ALL' if not MAX_VIDEOS else MAX_VIDEOS}")
    print("\n" + "="*60)
    
    total_transcripts = 0
    
    for i, channel in enumerate(CHANNELS, 1):
        print(f"\n[{i}/{len(CHANNELS)}] Processing @{channel}...")
        count = download_channel_transcripts(channel)
        total_transcripts += count
    
    print("\n" + "="*60)
    print(f"✅ Complete! Downloaded {total_transcripts} total transcripts")
    print(f"📁 Location: {Path(OUTPUT_DIR).absolute()}")
    print("="*60)


if __name__ == "__main__":
    main()
