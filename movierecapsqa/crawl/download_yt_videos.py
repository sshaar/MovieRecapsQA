#!/usr/bin/env python3
"""
Download YouTube recap videos (visual only, no audio) for MovieRecapsQA dataset.

This script downloads the recap videos from YouTube using yt-dlp.
Only the video stream is downloaded (no audio) to save space and bandwidth.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from datasets import load_dataset
from tqdm import tqdm


def load_recaps_from_huggingface(dataset_name: str = "sshaar/movierecapsqa") -> List[Dict]:
    """Load the recaps data from HuggingFace dataset."""
    print(f"Loading dataset from HuggingFace: {dataset_name}")
    dataset = load_dataset(dataset_name)

    # The dataset has a 'recaps' split
    recaps = dataset['recaps']

    # Convert to list of dicts
    recaps_list = []
    for item in recaps:
        recaps_list.append({
            'video_id': item['video_id'],
            'movie_name': item['movie_name'],
            'subtitle_url': item['subtitle_url'],
            'imdb_url': item['imdb_url']
        })

    return recaps_list


def check_ytdlp_installed() -> bool:
    """Check if yt-dlp is installed."""
    try:
        subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def download_video(
    video_id: str,
    output_path: Path,
    quality: str = 'best',
    rate_limit: str = None
) -> bool:
    """
    Download a YouTube video (video only, no audio) using yt-dlp.

    Args:
        video_id: YouTube video ID
        output_path: Path to save the video
        quality: Video quality selection ('best', '720', '480', etc.)
        rate_limit: Rate limit for download (e.g., '1M' for 1MB/s)

    Returns:
        True if download successful, False otherwise
    """
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    # Build yt-dlp command
    cmd = [
        'yt-dlp',
        '--no-audio',  # No audio stream
        '-f', f'bestvideo[height<={quality}]' if quality.isdigit() else 'bestvideo',
        '--output', str(output_path),
        '--no-playlist',
        '--no-warnings',
        '--newline',  # Progress on new lines (better for parsing)
    ]

    # Add rate limiting if specified
    if rate_limit:
        cmd.extend(['--limit-rate', rate_limit])

    # Add retries and error handling
    cmd.extend([
        '--retries', '3',
        '--fragment-retries', '3',
    ])

    cmd.append(youtube_url)

    try:
        # Run yt-dlp
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            return True
        else:
            print(f"  Error: {result.stderr.strip()}")
            return False

    except Exception as e:
        print(f"  Exception: {e}")
        return False


def get_video_info(video_id: str) -> Dict:
    """
    Get video information using yt-dlp.

    Args:
        video_id: YouTube video ID

    Returns:
        Dictionary with video info, or None if failed
    """
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    cmd = [
        'yt-dlp',
        '--dump-json',
        '--no-playlist',
        youtube_url
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except Exception:
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube recap videos for MovieRecapsQA dataset'
    )
    parser.add_argument(
        '--dataset',
        type=str,
        default='sshaar/movierecapsqa',
        help='HuggingFace dataset name'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/videos',
        help='Directory to save downloaded videos'
    )
    parser.add_argument(
        '--quality',
        type=str,
        default='720',
        choices=['best', '1080', '720', '480', '360'],
        help='Maximum video quality (height in pixels)'
    )
    parser.add_argument(
        '--format',
        type=str,
        default='mp4',
        choices=['mp4', 'webm', 'mkv'],
        help='Output video format'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip downloading if file already exists'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Limit number of videos to download (for testing)'
    )
    parser.add_argument(
        '--rate-limit',
        type=str,
        default=None,
        help='Download rate limit (e.g., "1M" for 1MB/s, "500K" for 500KB/s)'
    )
    parser.add_argument(
        '--check-availability',
        action='store_true',
        help='Only check if videos are available, do not download'
    )

    args = parser.parse_args()

    # Check if yt-dlp is installed
    if not check_ytdlp_installed():
        print("Error: yt-dlp is not installed.")
        print("Please install it using: pip install yt-dlp")
        sys.exit(1)

    print(f"yt-dlp is installed ✓")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load recaps data from HuggingFace
    try:
        recaps = load_recaps_from_huggingface(args.dataset)
    except Exception as e:
        print(f"Error loading dataset from HuggingFace: {e}")
        sys.exit(1)

    print(f"Found {len(recaps)} videos to download")

    # Limit if specified
    if args.limit:
        recaps = recaps[:args.limit]
        print(f"Limited to {args.limit} downloads")

    # Download or check videos
    successful = 0
    skipped = 0
    failed = 0
    unavailable = []

    for recap in tqdm(recaps, desc="Processing videos"):
        video_id = recap['video_id']
        movie_name = recap['movie_name']

        # Output filename
        output_filename = f"{movie_name}_{video_id}.{args.format}"
        output_path = output_dir / output_filename

        # Check availability mode
        if args.check_availability:
            tqdm.write(f"Checking: {movie_name} ({video_id})")
            info = get_video_info(video_id)
            if info is None:
                tqdm.write(f"  ✗ Unavailable or error")
                unavailable.append((video_id, movie_name))
                failed += 1
            else:
                tqdm.write(f"  ✓ Available - {info.get('title', 'Unknown')}")
                successful += 1
            continue

        # Check if already exists
        if args.skip_existing and output_path.exists():
            tqdm.write(f"Skipping {movie_name} (already exists)")
            skipped += 1
            continue

        tqdm.write(f"Downloading: {movie_name} ({video_id})")

        # Download video
        if download_video(
            video_id,
            output_path,
            quality=args.quality,
            rate_limit=args.rate_limit
        ):
            successful += 1
        else:
            failed += 1
            unavailable.append((video_id, movie_name))

    # Summary
    print("\n" + "="*50)
    if args.check_availability:
        print("Availability Check Summary:")
    else:
        print("Download Summary:")
    print(f"  Successful: {successful}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {failed}")
    print(f"  Total:      {len(recaps)}")

    if unavailable:
        print(f"\nUnavailable videos ({len(unavailable)}):")
        for video_id, movie_name in unavailable:
            print(f"  - {movie_name} ({video_id})")

    print("="*50)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
