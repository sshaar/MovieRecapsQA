---
license: cc-by-4.0
task_categories:
- visual-question-answering
- video-text-to-text
- question-answering
language:
- en
pretty_name: MovieRecapsQA Benchmark
size_categories:
- 1K<n<10K
tags:
- video-qa
- long-video-understanding
- multimodal-qa
- video-and-text-qa
- video-question-answering
configs:
- config_name: default
  data_files:
  - split: questions
    path: "data/questions.json"
  - split: recaps
    path: "data/recaps.json"
  - split: segments
    path: "data/segments.json"
  - split: facts
    path: "data/facts.json"
---

# MovieRecapsQA: A Multimodal Open-Ended Video Question-Answering Benchmark

## Benchmark Description

MovieRecapsQA is a benchmark for evaluating **multimodal question answering** with **video and text as context**. The benchmark assesses long-form video understanding in vision-language models using 8,263 question-answer pairs about YouTube movie recap videos. Questions require reasoning over both visual content (video frames) and textual content (dialogue/subtitles), aligned with atomic facts and movie subtitles for temporal grounding. It is designed to evaluate multimodal comprehension across dialogue, visual scenes, and narrative understanding in extended video content.

**Copyright Notice**: This benchmark does NOT include:
- Full-length movie files
- Movie subtitle files
- YouTube recap video files or captions

URLs are provided to enable researchers to access movie subtitles and IMDb metadata through proper channels.

### Benchmark Structure

The benchmark is organized into 4 normalized tables to eliminate fact duplication:

#### 1. `recaps` (74 entries)
Each entry represents a unique YouTube recap video. Multiple recap videos may cover the same movie.
- `video_id`: Unique identifier for the YouTube recap video
- `movie_name`: Name of the movie that this recap video is about
- `subtitle_url`: Direct download link for the movie's subtitle file
- `imdb_url`: IMDb page URL for the movie

#### 2. `segments` (1,430 entries)
- `video_id`: Reference to recaps table
- `segment_id`: Segment number within the recap video
- `movie_start_time`: Start timestamp in the full-length movie subtitle file (seconds)
- `movie_end_time`: End timestamp in the full-length movie subtitle file (seconds)
- `recap_start_time`: Start timestamp in the YouTube recap video (seconds)
- `recap_end_time`: End timestamp in the YouTube recap video (seconds)
- `fact_ids`: List of fact IDs associated with this segment

#### 3. `questions` (8,263 entries)
- `video_id`: Reference to recaps table
- `segment_id`: Reference to segments table
- `question_id`: Question number within the segment
- `question`: The question text
- `answer`: The answer text
- `verbose_question`: More detailed version of the question
- `vague_answer`: Intentionally vague version of the answer
- `aligned_fact_ids`: List of fact IDs aligned with this question

#### 4. `facts` (unique facts across all segments)
- `fact_id`: Global unique identifier for the fact
- `video_id`: Reference to recaps table
- `segment_id`: Reference to segments table
- `fact`: The atomic fact text (cleaned, no numbering prefix)

### Loading the Benchmark

The benchmark data is stored as JSON files in the `data/` directory. Load them as follows:

```python
from datasets import load_dataset
import json

# Load each table
recaps = json.loads(load_dataset("sshaar/movierecapsqa", data_files="data/recaps.json", split="train")[0]["text"])
segments = json.loads(load_dataset("sshaar/movierecapsqa", data_files="data/segments.json", split="train")[0]["text"])
questions = json.loads(load_dataset("sshaar/movierecapsqa", data_files="data/questions.json", split="train")[0]["text"])
facts = json.loads(load_dataset("sshaar/movierecapsqa", data_files="data/facts.json", split="train")[0]["text"])

# Or download directly from the repository
from huggingface_hub import hf_hub_download
import json

recaps_path = hf_hub_download(repo_id="sshaar/movierecapsqa", filename="data/recaps.json", repo_type="dataset")
with open(recaps_path) as f:
    recaps = json.load(f)

segments_path = hf_hub_download(repo_id="sshaar/movierecapsqa", filename="data/segments.json", repo_type="dataset")
with open(segments_path) as f:
    segments = json.load(f)

questions_path = hf_hub_download(repo_id="sshaar/movierecapsqa", filename="data/questions.json", repo_type="dataset")
with open(questions_path) as f:
    questions = json.load(f)

facts_path = hf_hub_download(repo_id="sshaar/movierecapsqa", filename="data/facts.json", repo_type="dataset")
with open(facts_path) as f:
    facts = json.load(f)
```

### Accessing External Resources

The benchmark provides URLs to external resources that are not included due to copyright:

- **Movie Subtitles**: Use `subtitle_url` from the `recaps` table to download subtitle files for the full-length movies
- **Movie Metadata**: Use `imdb_url` from the `recaps` table for information about the full-length movies
- **YouTube Recap Videos**: Use `video_id` to access the original recap videos on YouTube (not the full-length movies)
- **Temporal Alignment**: Use `movie_start_time`/`movie_end_time` to locate dialogue in movie subtitles, and `recap_start_time`/`recap_end_time` to locate segments in the recap videos

## Usage

### Data Crawling

Scripts are provided to download external resources (subtitles and videos):

```bash
# Clone the repository
git clone https://github.com/sshaar/MovieRecapsQA.git
cd MovieRecapsQA

# Install dependencies
pip install -r requirements.txt

# Download movie subtitles from OpenSubtitles
python movierecapsqa/crawl/download_subtitles.py --skip-existing

# Download YouTube recap videos (visual only, no audio)
python movierecapsqa/crawl/download_yt_videos.py --quality 720 --skip-existing
```

For more options and detailed documentation, see the [crawl README](https://github.com/sshaar/MovieRecapsQA/blob/main/movierecapsqa/crawl/README.md).

### Evaluation Framework

An evaluation framework is included to assess vision-language models on the benchmark using **Factuality**, **Coherence**, and **Relevance** metrics:

```bash
cd movierecapsqa/eval

# Configure API keys
cp .env.example .env
# Edit .env and add your API keys

# Using OpenAI Batch API (cost-effective, 50% discount)
./run_batch_pipeline.sh all

# Using real-time APIs (OpenAI, Anthropic, VLLM via LiteLLM)
./run_eval.sh your-model-output
```

The framework supports:
- **Real-time API**: OpenAI, Anthropic, VLLM via LiteLLM
- **Batch API**: OpenAI Batch API for cost savings

For detailed documentation, see the [eval README](https://github.com/sshaar/MovieRecapsQA/blob/main/movierecapsqa/eval/README.md).

### Benchmark Statistics

- **Total Recap Videos**: 74
- **Total Segments**: 1,430
- **Total Questions**: 8,263

### Benchmark Results

Performance of state-of-the-art vision-language models and human annotators on MovieRecapsQA. Results are reported as mean scores (scale 1-5) across different question types and categories.

**Question Types:**
- **Dialogue**: Questions about spoken content in the recap video
- **Scene**: Questions about visual content only
- **Multimodal**: Questions requiring both visual and dialogue understanding

**Question Categories:**
- **CRD**: Character Reasoning & Dialogue
- **NPA**: Narrative Progression & Action
- **STA**: Story Theme & Analysis
- **TEMP**: Temporal Understanding
- **TH**: Theory of Mind

#### Relevance Scores

| Model | Overall | Dialogue | Scene | Multimodal | CRD | NPA | STA | TEMP | TH |
|-------|---------|----------|-------|------------|-----|-----|-----|------|-----|
| **Best Human*** | **4.59** | -- | -- | -- | -- | -- | -- | -- | -- |
| **Avg. Human*** | 4.01 | 4.27 | 3.97 | 4.00 | 4.05 | 3.98 | **4.41** | -- | 4.11 |
| **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** |
| **GPT-4o** | 3.97 | 3.71 | 3.55 | 3.84 | 3.78 | 3.73 | 3.32 | 3.59 | 3.76 |
| **Amazon Nova Lite** | 3.93 | **4.12** | **3.82** | **3.99** | **3.97** | **3.95** | 3.81 | **3.94** | **4.23** |
| **Claude 3.5 Sonnet** | 3.92 | 3.88 | 3.71 | 3.83 | 3.86 | 3.72 | 3.61 | **3.99** | 3.82 |
| **Qwen2.5-VL** | 3.83 | 3.93 | 3.69 | 3.72 | 3.78 | 3.75 | 3.80 | 3.90 | 3.91 |
| **Gemini-2.5-Flash** | 3.70 | 3.66 | 3.45 | 3.67 | 3.67 | 3.58 | 3.38 | 3.41 | 3.62 |
| **MiniCPM-o** | 3.61 | 3.54 | 3.55 | 3.52 | 3.52 | 3.50 | 3.56 | 3.66 | 3.74 |
| **LLaVA-NeXT-Video** | 3.35 | 3.36 | 3.35 | 3.33 | 3.30 | 3.31 | 3.37 | 3.54 | 3.52 |

#### Factuality Scores

| Model | Overall | Dialogue | Scene | Multimodal | CRD | NPA | STA | TEMP | TH |
|-------|---------|----------|-------|------------|-----|-----|-----|------|-----|
| **Best Human*** | **4.53** | -- | -- | -- | -- | -- | -- | -- | -- |
| **Avg. Human*** | 4.01 | 4.17 | 3.84 | 3.98 | 4.07 | 3.86 | **4.15** | -- | **4.14** |
| **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** | **---** |
| **GPT-4o** | 3.99 | **3.76** | 3.43 | **3.66** | **3.73** | **3.64** | 3.10 | **3.58** | 3.55 |
| **Claude 3.5 Sonnet** | 3.76 | 3.69 | 3.17 | 3.58 | 3.65 | 3.42 | 3.12 | 3.30 | 3.44 |
| **Amazon Nova Lite** | 3.53 | 3.73 | 3.35 | 3.58 | 3.59 | 3.60 | 3.15 | 3.51 | 3.37 |
| **Qwen2.5-VL** | 3.47 | 3.50 | 3.28 | 3.35 | 3.42 | 3.40 | 3.07 | 3.39 | 3.27 |
| **Gemini-2.5-Flash** | 3.26 | 3.34 | 2.65 | 3.03 | 3.15 | 3.00 | 2.57 | 2.53 | 3.16 |
| **MiniCPM-o** | 3.21 | 3.15 | 3.00 | 3.09 | 3.14 | 3.10 | 2.76 | 3.02 | 3.02 |
| **LLaVA-NeXT-Video** | 2.96 | 2.99 | 2.88 | 2.88 | 2.99 | 2.90 | 2.65 | 3.04 | 2.78 |

*Human performance evaluated on a sample of 118 questions. TEMP scores for humans were not available. **Bold** indicates the best model score in each column (excluding human benchmarks). For complete results including ablation studies (frame-only and dialogue-only variants), see the paper.

### Citation

If you use this benchmark in your research, please cite our CVPR 2026 paper:

```bibtex
@inproceedings{shaar2026movierecapsqa,
  title={MovieRecapsQA: A Multimodal Open-Ended Video Question-Answering Benchmark},
  author={Shaar, Shaden and Thymes, Bradon and Chaixanien, Sirawut and Cardie, Claire and Hariharan, Bharath},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  year={2026},
  url={https://arxiv.org/abs/2601.02536}
}
```

### License

This benchmark is released under CC-BY-4.0 license.

**External Resources**: Full-length movie files, movie subtitle files, and YouTube recap video files/captions are NOT included in this benchmark to respect copyright. URLs are provided to access movie subtitles and metadata through proper channels, subject to their respective terms of service.

