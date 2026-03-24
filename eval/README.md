# MovieRecapsQA Evaluation Framework

Evaluation framework for MovieRecapsQA dataset supporting:
- **Real-time API**: OpenAI, Anthropic, VLLM via LiteLLM
- **Batch API**: OpenAI Batch API (50% cost discount)
- **Metrics**: Factuality, Coherence, Relevance

## Installation

```bash
cd eval
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your API keys
```

Required in `.env`:
```bash
OPENAI_API_KEY=sk-...
HF_DATASET_NAME=your-username/movierecaps-qa
```

## Batch Evaluation

### Quick Start
```bash
# Complete pipeline
./run_batch_pipeline.sh all
```

### Step-by-Step

**1. Create batch files**
```bash
python batch_openai.py create-claims \
    --output-dir batches/claims \
    --batch-size 1000 \
    --model gpt-4o-mini
```

**2. Submit to OpenAI**
```bash
python batch_openai.py submit \
    --batch-dir batches/claims \
    --output batches/batch_ids.json
```

**3. Check status**
```bash
python batch_openai.py status --batch-ids batches/batch_ids.json
```

**4. Download results (when complete)**
```bash
python batch_openai.py download \
    --batch-ids batches/batch_ids.json \
    --output-dir batches/claims-output
```

**5. Process results**
```bash
python batch_openai.py process-claims \
    --input-dir batches/claims-output \
    --output data/extracted_claims.jsonl
```

### Evaluation Batches

After extracting claims, create evaluation batches:

```bash
for metric in factuality coherence relevance; do
    python batch_openai.py create-eval \
        --claims-file data/extracted_claims.jsonl \
        --output-dir batches/${metric} \
        --metric ${metric} \
        --model gpt-4o-mini

    python batch_openai.py submit \
        --batch-dir batches/${metric} \
        --output batches/${metric}_ids.json
done
```

## Input/Output Formats

### Model Responses (JSONL)
```json
{
  "question_idx": 0,
  "question": "What type of film is this?",
  "model_response": "It is a thriller film.",
  "video_id": "0sYXzirol6A",
  "segment_id": 0,
  "question_id": 0
}
```

### Evaluation Results (JSONL)
```json
{
  "question_idx": 0,
  "claims": ["The film is a thriller."],
  "evaluations": {
    "factuality": {
      "factuality_score": 4,
      "claim_evaluations": [...]
    },
    "coherence": {"coherence_score": 5},
    "relevance": {"relevance_score": 5}
  },
  "aggregate_score": 4.67
}
```

## Metrics

All metrics scored 0-5:
- **Factuality**: Claims supported by ground truth
- **Coherence**: Internally consistent
- **Relevance**: Addresses the question
- **Aggregate**: Average of all three