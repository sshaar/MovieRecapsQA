#!/usr/bin/env python3
"""
Download subtitles from OpenSubtitles URLs for MovieRecapsQA dataset.

This script downloads subtitle files from the URLs specified in the HuggingFace dataset.
The subtitles are saved with their movie name and video ID for easy identification.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

import requests
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


def download_subtitle(subtitle_url: str, output_path: Path, retries: int = 3) -> bool:
    """
    Download a subtitle file from OpenSubtitles.

    Args:
        subtitle_url: URL to download from
        output_path: Path to save the subtitle file
        retries: Number of retry attempts

    Returns:
        True if download successful, False otherwise
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    for attempt in range(retries):
        try:
            response = requests.get(subtitle_url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()

            # Get total file size for progress bar
            total_size = int(response.headers.get('content-length', 0))

            # Write file with progress bar
            with open(output_path, 'wb') as f:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)

            return True

        except requests.exceptions.RequestException as e:
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"  Error: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"  Failed after {retries} attempts: {e}")
                return False

    return False


def main():
    parser = argparse.ArgumentParser(
        description='Download subtitles for MovieRecapsQA dataset'
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
        default='data/subtitles',
        help='Directory to save downloaded subtitles'
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
        help='Limit number of subtitles to download (for testing)'
    )

    args = parser.parse_args()

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load recaps data from HuggingFace
    try:
        recaps = load_recaps_from_huggingface(args.dataset)
    except Exception as e:
        print(f"Error loading dataset from HuggingFace: {e}")
        sys.exit(1)

    print(f"Found {len(recaps)} movies to download subtitles for")

    # Limit if specified
    if args.limit:
        recaps = recaps[:args.limit]
        print(f"Limited to {args.limit} downloads")

    # Download subtitles
    successful = 0
    skipped = 0
    failed = 0

    for recap in tqdm(recaps, desc="Downloading subtitles"):
        video_id = recap['video_id']
        movie_name = recap['movie_name']
        subtitle_url = recap['subtitle_url']

        # Create output filename (will be .srt or .zip depending on what OpenSubtitles returns)
        # We'll detect the extension from the downloaded content
        base_filename = f"{movie_name}_{video_id}"
        output_path = output_dir / f"{base_filename}.srt"

        # Check if already exists
        if args.skip_existing:
            # Check for both .srt and .zip extensions
            if output_path.exists() or (output_dir / f"{base_filename}.zip").exists():
                tqdm.write(f"Skipping {movie_name} (already exists)")
                skipped += 1
                continue

        tqdm.write(f"Downloading: {movie_name}")

        # Download to temporary file first
        temp_path = output_dir / f"{base_filename}.tmp"

        if download_subtitle(subtitle_url, temp_path):
            # Check if it's a zip file (OpenSubtitles sometimes returns zip)
            with open(temp_path, 'rb') as f:
                header = f.read(4)

            if header[:2] == b'PK':  # ZIP file magic number
                final_path = output_dir / f"{base_filename}.zip"
            else:
                final_path = output_path

            # Rename temp file to final name
            temp_path.rename(final_path)
            successful += 1
        else:
            failed += 1
            # Clean up temp file if exists
            if temp_path.exists():
                temp_path.unlink()

    # Summary
    print("\n" + "="*50)
    print("Download Summary:")
    print(f"  Successful: {successful}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {failed}")
    print(f"  Total:      {len(recaps)}")
    print("="*50)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
