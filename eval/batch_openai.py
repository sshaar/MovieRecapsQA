"""
OpenAI Batch API integration for MovieRecapsQA evaluation.

This module provides utilities for processing large-scale evaluations using
OpenAI's Batch API, which offers:
- 50% cost reduction compared to standard API
- Separate 200k TPM rate limit
- 24-hour completion window

Usage:
    # Create batch files for claim extraction
    python batch_openai.py create-claims \
        --output-dir batches/claims \
        --batch-size 1000

    # Submit batches
    python batch_openai.py submit \
        --batch-dir batches/claims \
        --output batch_ids.json

    # Check status
    python batch_openai.py status --batch-ids batch_ids.json

    # Download results
    python batch_openai.py download \
        --batch-ids batch_ids.json \
        --output-dir batches/claims-output

    # Process results
    python batch_openai.py process-claims \
        --input-dir batches/claims-output \
        --output claims.jsonl
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from tqdm import tqdm
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader

from config import ModelConfig, EvalConfig, PROMPTS_DIR
from data_loader import MovieRecapsDataLoader


class OpenAIBatchProcessor:
    """Process MovieRecapsQA evaluations using OpenAI Batch API."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize batch processor.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
        """
        self.client = OpenAI(api_key=api_key or ModelConfig.OPENAI_API_KEY)
        self.env = Environment(loader=FileSystemLoader(PROMPTS_DIR))

    def create_claim_extraction_batches(
        self,
        data_loader: MovieRecapsDataLoader,
        output_dir: Path,
        batch_size: int = 1000,
        model: str = "gpt-4o-mini",
        question_indices: Optional[List[int]] = None
    ) -> List[Path]:
        """
        Create batch files for claim extraction.

        Args:
            data_loader: MovieRecapsQA data loader
            output_dir: Directory to save batch files
            batch_size: Number of requests per batch file
            model: OpenAI model to use
            question_indices: Optional list of question indices to process

        Returns:
            List of created batch file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template = self.env.get_template("movierecaps_claim_extraction.jinja")
        system_message = "You are a helpful assistant who can extract atomic claims from a piece of text."

        # JSON schema for structured output
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
                            "description": "List of atomic claims"
                        }
                    },
                    "required": ["atomic_claims"],
                    "additionalProperties": False
                }
            }
        }

        # Determine which questions to process
        if question_indices is None:
            question_indices = list(range(len(data_loader)))

        batch_files = []
        total_batches = (len(question_indices) + batch_size - 1) // batch_size

        print(f"Creating {total_batches} batch files for {len(question_indices)} questions...")

        for batch_idx in range(0, len(question_indices), batch_size):
            batch_file = output_dir / f"batch-{batch_idx:06d}.jsonl"
            batch_files.append(batch_file)

            with open(batch_file, 'w') as f:
                for idx in question_indices[batch_idx:batch_idx + batch_size]:
                    eval_item = data_loader.get_evaluation_item(idx)

                    # Render prompt
                    prompt = template.render(
                        question=eval_item['question'],
                        answer=eval_item['ground_truth_answer']
                    )

                    # Create batch request
                    request = {
                        "custom_id": f"{eval_item['video_id']}.{eval_item['segment_id']}.{eval_item['question_id']}.claims",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": prompt}
                            ],
                            "response_format": response_format,
                            "temperature": 0.0,
                        }
                    }

                    f.write(json.dumps(request) + '\n')

        print(f"✓ Created {len(batch_files)} batch files in {output_dir}/")
        return batch_files

    def create_evaluation_batches(
        self,
        data_loader: MovieRecapsDataLoader,
        claims_data: Dict,  # question_idx -> claims
        output_dir: Path,
        metric: str,
        batch_size: int = 1000,
        model: str = "gpt-4o-mini",
        question_indices: Optional[List[int]] = None
    ) -> List[Path]:
        """
        Create batch files for evaluation (factuality, coherence, or relevance).

        Args:
            data_loader: MovieRecapsQA data loader
            claims_data: Dictionary mapping question_idx to extracted claims
            output_dir: Directory to save batch files
            metric: Evaluation metric ('factuality', 'coherence', 'relevance')
            batch_size: Number of requests per batch file
            model: OpenAI model to use
            question_indices: Optional list of question indices to process

        Returns:
            List of created batch file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load template
        template = self.env.get_template(f"movierecaps_{metric}.jinja")
        system_message = f"You are an expert {metric} evaluator for video question answering systems."

        # Determine which questions to process
        if question_indices is None:
            question_indices = sorted(claims_data.keys())

        batch_files = []
        total_batches = (len(question_indices) + batch_size - 1) // batch_size

        print(f"Creating {total_batches} batch files for {metric} evaluation...")

        for batch_idx in range(0, len(question_indices), batch_size):
            batch_file = output_dir / f"batch-{metric}-{batch_idx:06d}.jsonl"
            batch_files.append(batch_file)

            with open(batch_file, 'w') as f:
                for idx in question_indices[batch_idx:batch_idx + batch_size]:
                    if idx not in claims_data:
                        continue

                    eval_item = data_loader.get_evaluation_item(idx)
                    claims = claims_data[idx]

                    if not claims:
                        continue

                    # Format claims for template
                    claims_text = "\n".join([f"{i+1}. {claim}" for i, claim in enumerate(claims)])

                    # Prepare template variables
                    template_vars = {
                        'question': eval_item['question'],
                        'claims': claims_text,
                    }

                    # Add metric-specific variables
                    if metric in ['factuality', 'relevance']:
                        facts = eval_item['facts']
                        template_vars['facts'] = "\n".join([f"- {fact}" for fact in facts])
                        template_vars['context'] = "No dialogue context available."  # TODO: Add SRT dialogue

                    # Render prompt
                    prompt = template.render(**template_vars)

                    # Create batch request
                    request = {
                        "custom_id": f"{eval_item['video_id']}.{eval_item['segment_id']}.{eval_item['question_id']}.{metric}",
                        "method": "POST",
                        "url": "/v1/chat/completions",
                        "body": {
                            "model": model,
                            "messages": [
                                {"role": "system", "content": system_message},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.0,
                            "max_tokens": 2048,
                        }
                    }

                    f.write(json.dumps(request) + '\n')

        print(f"✓ Created {len(batch_files)} batch files in {output_dir}/")
        return batch_files

    def submit_batches(
        self,
        batch_files: List[Path],
        description_prefix: str = "MovieRecapsQA"
    ) -> Dict[str, str]:
        """
        Submit batch files to OpenAI.

        Args:
            batch_files: List of batch file paths
            description_prefix: Prefix for batch descriptions

        Returns:
            Dictionary mapping batch file names to batch IDs
        """
        batch_ids = {}

        print(f"Submitting {len(batch_files)} batches to OpenAI...")

        for batch_file in tqdm(batch_files):
            # Upload file
            with open(batch_file, 'rb') as f:
                uploaded_file = self.client.files.create(
                    file=f,
                    purpose='batch'
                )

            # Create batch
            batch = self.client.batches.create(
                input_file_id=uploaded_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h",
                metadata={
                    "description": f"{description_prefix} - {batch_file.name}"
                }
            )

            batch_ids[batch_file.name] = batch.id
            print(f"  ✓ {batch_file.name} -> {batch.id}")

        print(f"\n✓ Submitted {len(batch_ids)} batches")
        return batch_ids

    def check_batch_status(self, batch_ids: Dict[str, str]) -> Dict[str, Dict]:
        """
        Check status of submitted batches.

        Args:
            batch_ids: Dictionary mapping batch names to batch IDs

        Returns:
            Dictionary with status information
        """
        statuses = {}

        print(f"Checking status of {len(batch_ids)} batches...\n")

        for batch_name, batch_id in batch_ids.items():
            batch = self.client.batches.retrieve(batch_id)
            statuses[batch_name] = {
                'batch_id': batch_id,
                'status': batch.status,
                'created_at': batch.created_at,
                'completed_at': batch.completed_at,
                'request_counts': {
                    'total': batch.request_counts.total,
                    'completed': batch.request_counts.completed,
                    'failed': batch.request_counts.failed,
                }
            }

            print(f"{batch_name}:")
            print(f"  Status: {batch.status}")
            print(f"  Progress: {batch.request_counts.completed}/{batch.request_counts.total}")
            if batch.request_counts.failed > 0:
                print(f"  Failed: {batch.request_counts.failed}")
            print()

        return statuses

    def download_results(
        self,
        batch_ids: Dict[str, str],
        output_dir: Path
    ) -> List[Path]:
        """
        Download completed batch results.

        Args:
            batch_ids: Dictionary mapping batch names to batch IDs
            output_dir: Directory to save results

        Returns:
            List of downloaded result file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        downloaded_files = []

        print(f"Downloading results to {output_dir}/...")

        for batch_name, batch_id in tqdm(batch_ids.items()):
            batch = self.client.batches.retrieve(batch_id)

            if batch.status != 'completed':
                print(f"  ⚠ Skipping {batch_name} (status: {batch.status})")
                continue

            if not batch.output_file_id:
                print(f"  ⚠ No output file for {batch_name}")
                continue

            # Download results
            result_content = self.client.files.content(batch.output_file_id)

            # Save to file
            output_file = output_dir / batch_name
            with open(output_file, 'wb') as f:
                f.write(result_content.content)

            downloaded_files.append(output_file)

        print(f"\n✓ Downloaded {len(downloaded_files)} result files")
        return downloaded_files

    def process_claim_results(
        self,
        result_files: List[Path],
        output_file: Path
    ) -> None:
        """
        Process claim extraction results into JSONL format.

        Args:
            result_files: List of batch result files
            output_file: Output JSONL file path
        """
        output_file = Path(output_file)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        print(f"Processing claim extraction results...")

        with open(output_file, 'w') as out_f:
            for result_file in tqdm(result_files):
                with open(result_file, 'r') as f:
                    for line in f:
                        result = json.loads(line)

                        # Parse custom_id
                        custom_id_parts = result['custom_id'].split('.')
                        video_id = custom_id_parts[0]
                        segment_id = int(custom_id_parts[1])
                        question_id = int(custom_id_parts[2])

                        # Extract claims from response
                        try:
                            content = result['response']['body']['choices'][0]['message']['content']
                            claims_data = json.loads(content)
                            claims = claims_data.get('atomic_claims', [])
                        except (KeyError, json.JSONDecodeError) as e:
                            print(f"Error processing {result['custom_id']}: {e}")
                            claims = []

                        # Save result
                        output_data = {
                            'video_id': video_id,
                            'segment_id': segment_id,
                            'question_id': question_id,
                            'claims': claims,
                            'custom_id': result['custom_id']
                        }

                        out_f.write(json.dumps(output_data) + '\n')

        print(f"✓ Processed results saved to {output_file}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="OpenAI Batch API for MovieRecapsQA")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create claim extraction batches
    create_claims = subparsers.add_parser('create-claims', help='Create claim extraction batch files')
    create_claims.add_argument('--output-dir', required=True, help='Output directory for batch files')
    create_claims.add_argument('--batch-size', type=int, default=1000, help='Requests per batch file')
    create_claims.add_argument('--model', default='gpt-4o-mini', help='OpenAI model to use')
    create_claims.add_argument('--indices', help='Question indices (e.g., 0-10 or 0,1,2)')

    # Create evaluation batches
    create_eval = subparsers.add_parser('create-eval', help='Create evaluation batch files')
    create_eval.add_argument('--claims-file', required=True, help='JSONL file with extracted claims')
    create_eval.add_argument('--output-dir', required=True, help='Output directory for batch files')
    create_eval.add_argument('--metric', required=True, choices=['factuality', 'coherence', 'relevance'])
    create_eval.add_argument('--batch-size', type=int, default=1000, help='Requests per batch file')
    create_eval.add_argument('--model', default='gpt-4o-mini', help='OpenAI model to use')

    # Submit batches
    submit = subparsers.add_parser('submit', help='Submit batch files to OpenAI')
    submit.add_argument('--batch-dir', required=True, help='Directory containing batch files')
    submit.add_argument('--output', required=True, help='Output JSON file for batch IDs')
    submit.add_argument('--description', default='MovieRecapsQA', help='Batch description prefix')

    # Check status
    status = subparsers.add_parser('status', help='Check batch status')
    status.add_argument('--batch-ids', required=True, help='JSON file with batch IDs')

    # Download results
    download = subparsers.add_parser('download', help='Download batch results')
    download.add_argument('--batch-ids', required=True, help='JSON file with batch IDs')
    download.add_argument('--output-dir', required=True, help='Output directory for results')

    # Process claim results
    process_claims = subparsers.add_parser('process-claims', help='Process claim extraction results')
    process_claims.add_argument('--input-dir', required=True, help='Directory with result files')
    process_claims.add_argument('--output', required=True, help='Output JSONL file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize processor
    processor = OpenAIBatchProcessor()

    if args.command == 'create-claims':
        # Parse indices if provided
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
        data_loader = MovieRecapsDataLoader()

        # Create batch files
        batch_files = processor.create_claim_extraction_batches(
            data_loader=data_loader,
            output_dir=Path(args.output_dir),
            batch_size=args.batch_size,
            model=args.model,
            question_indices=question_indices
        )

        print(f"\nNext steps:")
        print(f"  1. Submit batches: python batch_openai.py submit --batch-dir {args.output_dir} --output batch_ids.json")
        print(f"  2. Check status: python batch_openai.py status --batch-ids batch_ids.json")

    elif args.command == 'create-eval':
        # Load claims
        claims_data = {}
        with open(args.claims_file, 'r') as f:
            for line in f:
                data = json.loads(line)
                # Construct question_idx - need to map from video/segment/question IDs
                # This is a simplified version; you may need to adjust based on your data
                claims_data[data['question_id']] = data['claims']

        # Load dataset
        data_loader = MovieRecapsDataLoader()

        # Create batch files
        batch_files = processor.create_evaluation_batches(
            data_loader=data_loader,
            claims_data=claims_data,
            output_dir=Path(args.output_dir),
            metric=args.metric,
            batch_size=args.batch_size,
            model=args.model
        )

    elif args.command == 'submit':
        # Find all batch files
        batch_dir = Path(args.batch_dir)
        batch_files = sorted(batch_dir.glob('*.jsonl'))

        if not batch_files:
            print(f"No batch files found in {batch_dir}")
            return

        # Submit batches
        batch_ids = processor.submit_batches(batch_files, args.description)

        # Save batch IDs
        with open(args.output, 'w') as f:
            json.dump(batch_ids, f, indent=2)

        print(f"\n✓ Batch IDs saved to {args.output}")

    elif args.command == 'status':
        # Load batch IDs
        with open(args.batch_ids, 'r') as f:
            batch_ids = json.load(f)

        # Check status
        statuses = processor.check_batch_status(batch_ids)

        # Summary
        completed = sum(1 for s in statuses.values() if s['status'] == 'completed')
        in_progress = sum(1 for s in statuses.values() if s['status'] == 'in_progress')
        failed = sum(1 for s in statuses.values() if s['status'] == 'failed')

        print("Summary:")
        print(f"  Completed: {completed}/{len(batch_ids)}")
        print(f"  In Progress: {in_progress}/{len(batch_ids)}")
        print(f"  Failed: {failed}/{len(batch_ids)}")

    elif args.command == 'download':
        # Load batch IDs
        with open(args.batch_ids, 'r') as f:
            batch_ids = json.load(f)

        # Download results
        result_files = processor.download_results(batch_ids, Path(args.output_dir))

    elif args.command == 'process-claims':
        # Find all result files
        input_dir = Path(args.input_dir)
        result_files = sorted(input_dir.glob('*.jsonl'))

        if not result_files:
            print(f"No result files found in {input_dir}")
            return

        # Process results
        processor.process_claim_results(result_files, Path(args.output))


if __name__ == "__main__":
    main()
