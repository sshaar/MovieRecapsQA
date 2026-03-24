"""
LLM-as-a-judge evaluator for MovieRecapsQA responses.

This module evaluates model responses using prompt-based evaluation for
factuality, coherence, and relevance metrics.
"""

import json
import time
from typing import Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

import litellm
from litellm import completion
from tqdm import tqdm

from config import EvalConfig, PROMPTS_DIR, ModelConfig
from data_loader import MovieRecapsDataLoader, load_model_responses


class ClaimExtractor:
    """Extract atomic claims from model responses."""

    def __init__(
        self,
        provider: str = EvalConfig.EVALUATOR_PROVIDER,
        model_name: str = EvalConfig.EVALUATOR_MODEL,
        template_path: Optional[Path] = None
    ):
        """Initialize claim extractor."""
        self.provider = provider
        self.model_name = model_name
        litellm.drop_params = ModelConfig.LITELLM_DROP_PARAMS

        # Load template
        if template_path is None:
            template_path = PROMPTS_DIR / "movierecaps_claim_extraction.jinja"

        self.template_path = template_path

        # Setup Jinja environment
        env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
        self.template = env.get_template(template_path.name)

        # System message for claim extraction
        self.system_message = "You are a helpful assistant who can extract atomic claims from a piece of text."

    def extract_claims(self, question: str, response: str) -> List[str]:
        """
        Extract atomic claims from a model response.

        Args:
            question: The question being answered (for context)
            response: Model response text

        Returns:
            List of atomic claims
        """
        # Render prompt using template
        prompt = self.template.render(question=question, answer=response)

        messages = [
            {"role": "system", "content": self.system_message},
            {"role": "user", "content": prompt}
        ]

        # Define the JSON schema for structured output
        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "facts_schema",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "atomic_claims": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of atomic claims extracted from the model response"
                        }
                    },
                    "required": ["atomic_claims"],
                    "additionalProperties": False
                }
            }
        }

        try:
            result = completion(
                model=self.model_name,
                messages=messages,
                temperature=0.0,
                max_tokens=2048,
                response_format=response_format
            )

            # Parse the JSON response
            content = result.choices[0].message.content
            claims_data = json.loads(content)
            claims = claims_data.get('atomic_claims', [])

            return claims

        except Exception as e:
            print(f"Error extracting claims: {e}")
            # Fallback: split by sentences
            return [s.strip() + '.' for s in response.split('.') if s.strip()]


class PromptEvaluator:
    """Evaluator using Jinja prompt templates."""

    def __init__(
        self,
        metric: str,
        provider: str = EvalConfig.EVALUATOR_PROVIDER,
        model_name: str = EvalConfig.EVALUATOR_MODEL,
        template_path: Optional[Path] = None
    ):
        """
        Initialize prompt evaluator.

        Args:
            metric: Evaluation metric ('factuality', 'coherence', 'relevance')
            provider: Model provider for evaluation
            model_name: Model to use for evaluation
            template_path: Path to Jinja template (uses default if None)
        """
        self.metric = metric
        self.provider = provider
        self.model_name = model_name

        # Load template
        if template_path is None:
            template_path = PROMPTS_DIR / f"movierecaps_{metric}.jinja"

        self.template_path = template_path

        # Setup Jinja environment
        env = Environment(loader=FileSystemLoader(PROMPTS_DIR))
        self.template = env.get_template(template_path.name)

        litellm.drop_params = ModelConfig.LITELLM_DROP_PARAMS

        print(f"Initialized {metric} evaluator with {model_name}")

    def evaluate(
        self,
        question: str,
        claims: List[str],
        facts: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> Dict:
        """
        Evaluate claims using the prompt template.

        Args:
            question: The question being answered
            claims: List of claims extracted from model response
            facts: Ground truth facts (for factuality and relevance)
            context: SRT dialogue context (for factuality and relevance)

        Returns:
            Evaluation result dictionary
        """
        # Format claims for template
        claims_text = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])

        # Prepare template variables
        template_vars = {
            'question': question,
            'claims': claims_text,
        }

        # Add metric-specific variables
        if self.metric in ['factuality', 'relevance']:
            template_vars['facts'] = "\n".join([f"- {fact}" for fact in (facts or [])])
            template_vars['context'] = context or "No dialogue context available."

        # Render prompt
        prompt = self.template.render(**template_vars)

        # Call LLM evaluator
        messages = [{"role": "user", "content": prompt}]

        try:
            start_time = time.time()
            result = completion(
                model=self.model_name,
                messages=messages,
                temperature=EvalConfig.EVALUATION_TEMPERATURE,
                max_tokens=EvalConfig.MAX_EVALUATION_TOKENS
            )
            eval_time = time.time() - start_time

            response_text = result.choices[0].message.content

            # Parse JSON response
            # Try to extract JSON from markdown code blocks if present
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text

            evaluation = json.loads(json_text)
            evaluation['eval_time'] = eval_time
            evaluation['evaluator_model'] = self.model_name

            return evaluation

        except json.JSONDecodeError as e:
            print(f"Error parsing evaluation JSON: {e}")
            print(f"Response text: {response_text[:500]}...")
            return {
                'error': 'Failed to parse evaluation JSON',
                'raw_response': response_text,
                f'{self.metric}_score': -1
            }
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return {
                'error': str(e),
                f'{self.metric}_score': -1
            }


def evaluate_responses(
    response_file: str,
    output_file: str,
    data_loader: MovieRecapsDataLoader,
    metrics: List[str] = EvalConfig.METRICS,
    evaluator_provider: str = EvalConfig.EVALUATOR_PROVIDER,
    evaluator_model: str = EvalConfig.EVALUATOR_MODEL,
    question_indices: Optional[List[int]] = None
) -> None:
    """
    Evaluate model responses using LLM-as-a-judge.

    Args:
        response_file: Path to JSONL file with model responses
        output_file: Path to save evaluation results
        data_loader: MovieRecapsQA data loader
        metrics: List of metrics to evaluate
        evaluator_provider: Provider for evaluator model
        evaluator_model: Model to use for evaluation
        question_indices: Optional list of specific question indices to evaluate
    """
    # Load responses
    print(f"Loading responses from: {response_file}")
    responses = load_model_responses(response_file)

    # Initialize evaluators
    claim_extractor = ClaimExtractor(evaluator_provider, evaluator_model)
    evaluators = {
        metric: PromptEvaluator(metric, evaluator_provider, evaluator_model)
        for metric in metrics
    }

    # Determine which responses to evaluate
    if question_indices is None:
        question_indices = sorted(responses.keys())

    print(f"Evaluating {len(question_indices)} responses...")
    print(f"Metrics: {', '.join(metrics)}")
    print(f"Output file: {output_file}")

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        for idx in tqdm(question_indices, desc="Evaluating responses"):
            if idx not in responses:
                print(f"\nWarning: No response found for question {idx}, skipping")
                continue

            response_data = responses[idx]

            # Skip if error in response
            if 'error' in response_data:
                print(f"\nSkipping question {idx} due to error in response")
                continue

            # Get evaluation item
            eval_item = data_loader.get_evaluation_item(idx)

            question = response_data['question']
            model_response = response_data['model_response']

            # Extract claims
            try:
                claims = claim_extractor.extract_claims(question, model_response)
            except Exception as e:
                print(f"\nError extracting claims for question {idx}: {e}")
                claims = [model_response]  # Use full response as single claim

            # Run evaluations
            evaluations = {}
            for metric in metrics:
                evaluator = evaluators[metric]

                # Prepare context based on metric
                facts = eval_item['facts'] if metric in ['factuality', 'relevance'] else None
                context = None  # TODO: Add SRT dialogue if available

                try:
                    eval_result = evaluator.evaluate(
                        question=question,
                        claims=claims,
                        facts=facts,
                        context=context
                    )
                    evaluations[metric] = eval_result
                except Exception as e:
                    print(f"\nError evaluating {metric} for question {idx}: {e}")
                    evaluations[metric] = {
                        'error': str(e),
                        f'{metric}_score': -1
                    }

            # Compile output
            output_data = {
                'question_idx': idx,
                'video_id': response_data.get('video_id'),
                'segment_id': response_data.get('segment_id'),
                'question_id': response_data.get('question_id'),
                'question': question,
                'model_response': model_response,
                'ground_truth_answer': response_data.get('ground_truth_answer'),
                'claims': claims,
                'evaluations': evaluations,
                'metadata': response_data.get('metadata', {}),
            }

            # Calculate aggregate score (average of all metrics)
            scores = [
                evaluations[m].get(f'{m}_score', -1)
                for m in metrics
                if evaluations[m].get(f'{m}_score', -1) >= 0
            ]
            if scores:
                output_data['aggregate_score'] = sum(scores) / len(scores)
            else:
                output_data['aggregate_score'] = -1

            f.write(json.dumps(output_data) + '\n')
            f.flush()

    print(f"\nEvaluation complete. Results saved to: {output_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate model responses on MovieRecapsQA")
    parser.add_argument(
        "--responses",
        type=str,
        required=True,
        help="JSONL file with model responses"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output JSONL file for evaluation results"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=None,
        help="HuggingFace dataset name (uses config default if not specified)"
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default="factuality,coherence,relevance",
        help="Comma-separated metrics to evaluate"
    )
    parser.add_argument(
        "--evaluator-provider",
        type=str,
        default=EvalConfig.EVALUATOR_PROVIDER,
        help="Model provider for evaluation"
    )
    parser.add_argument(
        "--evaluator-model",
        type=str,
        default=EvalConfig.EVALUATOR_MODEL,
        help="Model to use for evaluation"
    )
    parser.add_argument(
        "--indices",
        type=str,
        help="Comma-separated question indices to evaluate"
    )

    args = parser.parse_args()

    # Parse metrics
    metrics = [m.strip() for m in args.metrics.split(',')]

    # Parse question indices if provided
    question_indices = None
    if args.indices:
        indices = []
        for part in args.indices.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                indices.extend(range(start, end + 1))
            else:
                indices.append(int(part))
        question_indices = indices

    # Load dataset
    dataset_name = args.dataset if args.dataset else None
    data_loader = MovieRecapsDataLoader(dataset_name=dataset_name) if dataset_name else MovieRecapsDataLoader()

    # Run evaluation
    evaluate_responses(
        response_file=args.responses,
        output_file=args.output,
        data_loader=data_loader,
        metrics=metrics,
        evaluator_provider=args.evaluator_provider,
        evaluator_model=args.evaluator_model,
        question_indices=question_indices
    )
