# MovieRecapsQA: A Multimodal Open-Ended Video Question-Answering Benchmark

[![Website](https://img.shields.io/badge/Website-View-blue)](website/index.html)
[![Code](https://img.shields.io/badge/Code-View-green)](code/)
[![Dataset](https://img.shields.io/badge/Dataset-HuggingFace-yellow)](https://huggingface.co/datasets/sshaar/movierecapsqa)
[![Paper](https://img.shields.io/badge/Paper-arXiv-red)](https://arxiv.org/abs/2601.02536)


## Dataset

The MovieRecaps dataset consists of:
- **74 recap videos** from YouTube
- **1,430 segments** with timestamps
- **8,263 question-answer pairs** with verbose/vague variants
- **Unique atomic facts** linked to segments and questions via IDs

**Copyright Notice**: This benchmark does NOT include:
- Full-length movie files
- Movie subtitle files
- YouTube recap video files or captions



## Benchmark Results

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

### Relevance Scores

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

### Factuality Scores

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


## Citation

If you use this dataset, please cite our CVPR 2026 paper:

```bibtex
@inproceedings{shaar2026movierecapsqa,
  title={MovieRecapsQA: A Multimodal Open-Ended Video Question-Answering Benchmark},
  author={Shaar, Shaden and Thymes, Bradon and Chaixanien, Sirawut and Cardie, Claire and Hariharan, Bharath},
  booktitle={Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)},
  year={2026},
  note={arXiv preprint arXiv:2601.02536}
}
```

## License

This benchmark is released under CC-BY-4.0 license.

**External Resources**: Full-length movie files, movie subtitle files, and YouTube recap video files/captions are NOT included in this benchmark to respect copyright. URLs are provided to access movie subtitles and metadata through proper channels, subject to their respective terms of service.
