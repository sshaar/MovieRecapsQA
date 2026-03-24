"""
MovieRecapsQA Evaluation Framework

A comprehensive evaluation framework for question-answering models on the
MovieRecapsQA dataset.

Main components:
- data_loader: Load dataset from HuggingFace Hub
- model_inference: Generate responses using various model providers
- evaluator: Evaluate responses using LLM-as-a-judge
- analyze_results: Analyze and summarize evaluation results

Example usage:
    from eval.data_loader import MovieRecapsDataLoader
    from eval.model_inference import ModelInference

    data_loader = MovieRecapsDataLoader()
    model = ModelInference(provider='openai', model_name='gpt-4-turbo-preview')
"""

__version__ = "1.0.0"
__all__ = [
    "data_loader",
    "model_inference",
    "evaluator",
    "analyze_results",
    "config",
]
