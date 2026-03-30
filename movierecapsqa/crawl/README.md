# MovieRecapsQA Data Crawlers

This directory contains scripts to download the external resources (subtitles and videos) for the MovieRecapsQA dataset.

## Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

The scripts will automatically download the dataset metadata from HuggingFace (`sshaar/movierecapsqa`) to get the subtitle URLs and video IDs.

## Scripts

### 1. Download Subtitles (`download_subtitles.py`)

Downloads movie subtitles from OpenSubtitles URLs specified in the HuggingFace dataset.

**Basic usage:**
```bash
python movierecapsqa/crawl/download_subtitles.py
```

**Options:**
```bash
python movierecapsqa/crawl/download_subtitles.py \
    --dataset sshaar/movierecapsqa \
    --output-dir data/subtitles \
    --skip-existing \
    --limit 10
```

**Parameters:**
- `--dataset`: HuggingFace dataset name (default: `sshaar/movierecapsqa`)
- `--output-dir`: Directory to save subtitles (default: `data/subtitles`)
- `--skip-existing`: Skip files that already exist
- `--limit`: Limit number of downloads for testing

**Output:**
- Subtitles are saved as `{movie_name}_{video_id}.srt` or `.zip`
- Progress is shown with a progress bar
- Summary statistics are displayed at the end

### 2. Download YouTube Videos (`download_yt_videos.py`)

Downloads YouTube recap videos (visual only, no audio) using yt-dlp.

**Basic usage:**
```bash
python movierecapsqa/crawl/download_yt_videos.py
```

**Options:**
```bash
python movierecapsqa/crawl/download_yt_videos.py \
    --dataset sshaar/movierecapsqa \
    --output-dir data/videos \
    --quality 720 \
    --format mp4 \
    --skip-existing \
    --rate-limit 1M \
    --limit 5
```

**Parameters:**
- `--dataset`: HuggingFace dataset name (default: `sshaar/movierecapsqa`)
- `--output-dir`: Directory to save videos (default: `data/videos`)
- `--quality`: Maximum video quality in pixels (choices: `best`, `1080`, `720`, `480`, `360`)
- `--format`: Output format (choices: `mp4`, `webm`, `mkv`)
- `--skip-existing`: Skip files that already exist
- `--rate-limit`: Download rate limit (e.g., `1M` for 1MB/s, `500K` for 500KB/s)
- `--limit`: Limit number of downloads for testing
- `--check-availability`: Only check if videos are available without downloading

**Output:**
- Videos are saved as `{movie_name}_{video_id}.{format}`
- Only video stream is downloaded (no audio)
- Progress is shown for each download
- Summary statistics are displayed at the end

**Check availability before downloading:**
```bash
python movierecapsqa/crawl/download_yt_videos.py --check-availability
```

## Example Workflow

1. **Test with a small sample:**
   ```bash
   # Download 5 subtitles for testing
   python movierecapsqa/crawl/download_subtitles.py --limit 5

   # Download 5 videos for testing
   python movierecapsqa/crawl/download_yt_videos.py --limit 5 --quality 480
   ```

2. **Check video availability:**
   ```bash
   python movierecapsqa/crawl/download_yt_videos.py --check-availability
   ```

3. **Download all data:**
   ```bash
   # Download all subtitles
   python movierecapsqa/crawl/download_subtitles.py --skip-existing

   # Download all videos (with rate limiting)
   python movierecapsqa/crawl/download_yt_videos.py \
       --quality 720 \
       --format mp4 \
       --skip-existing \
       --rate-limit 1M
   ```

## Notes

- **Subtitles**: OpenSubtitles may rate-limit requests. The script includes retry logic with exponential backoff.
- **Videos**: Some YouTube videos may be unavailable due to region restrictions, copyright claims, or removal. Use `--check-availability` to verify before downloading.
- **Storage**: Video files can be large. A 720p video typically ranges from 50-200MB depending on length.
- **Resumability**: Both scripts support `--skip-existing` to resume interrupted downloads.
- **Rate Limiting**: Use `--rate-limit` for the video downloader to avoid bandwidth issues.

## Troubleshooting

**yt-dlp not found:**
```bash
pip install yt-dlp
```

**Permission errors:**
```bash
chmod +x movierecapsqa/crawl/*.py
```

**HTTP errors from OpenSubtitles:**
- Wait a few minutes between retries
- OpenSubtitles may have rate limits
- Some subtitle files may no longer be available

**YouTube download fails:**
- Check if the video is still available on YouTube
- Try a lower quality setting
- Some videos may be region-restricted
- Use `--check-availability` to verify access
