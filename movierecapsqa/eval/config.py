"""
Configuration for MovieRecapsQA evaluation.

This module contains configuration settings for model evaluation including
model providers, API keys, and evaluation parameters.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Directories
EVAL_DIR = Path(__file__).parent
PROJECT_ROOT = EVAL_DIR.parent
PROMPTS_DIR = EVAL_DIR / "prompts"
OUTPUTS_DIR = EVAL_DIR / "outputs"

# Ensure output directory exists
OUTPUTS_DIR.mkdir(exist_ok=True)

# HuggingFace Dataset
DATASET_NAME = os.getenv("HF_DATASET_NAME", "sshaar/movierecaps-qa")

# Model Configuration
class ModelConfig:
    """Configuration for different model providers."""

    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

    # Anthropic Configuration
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    ANTHROPIC_DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-opus-20240229")

    # VLLM Configuration
    VLLM_MODEL_PATH = os.getenv("VLLM_MODEL_PATH", "meta-llama/Llama-2-7b-chat-hf")
    VLLM_TENSOR_PARALLEL_SIZE = int(os.getenv("VLLM_TENSOR_PARALLEL_SIZE", "1"))
    VLLM_GPU_MEMORY_UTILIZATION = float(os.getenv("VLLM_GPU_MEMORY_UTILIZATION", "0.9"))

    # LiteLLM Configuration
    LITELLM_DROP_PARAMS = True  # Drop unsupported params automatically


# Evaluation Configuration
class EvalConfig:
    """Configuration for evaluation parameters."""

    # Evaluator model (for LLM-as-a-judge evaluation)
    EVALUATOR_PROVIDER = os.getenv("EVALUATOR_PROVIDER", "openai")
    EVALUATOR_MODEL = os.getenv("EVALUATOR_MODEL", "gpt-4-turbo-preview")

    # Temperature settings
    GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.7"))
    EVALUATION_TEMPERATURE = float(os.getenv("EVALUATION_TEMPERATURE", "0.0"))

    # Max tokens
    MAX_GENERATION_TOKENS = int(os.getenv("MAX_GENERATION_TOKENS", "512"))
    MAX_EVALUATION_TOKENS = int(os.getenv("MAX_EVALUATION_TOKENS", "2048"))

    # Batch size
    BATCH_SIZE = int(os.getenv("BATCH_SIZE", "1"))

    # Metrics to evaluate
    METRICS = ["factuality", "coherence", "relevance"]


# Prompt Templates
PROMPT_TEMPLATES = {
    "claim_extraction": PROMPTS_DIR / "movierecaps_claim_extraction.jinja",
    "factuality": PROMPTS_DIR / "movierecaps_factuality.jinja",
    "coherence": PROMPTS_DIR / "movierecaps_coherence.jinja",
    "relevance": PROMPTS_DIR / "movierecaps_relevance.jinja",
}
