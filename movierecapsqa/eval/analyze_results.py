"""
Analyze and summarize evaluation results.

This module provides utilities for analyzing evaluation results and
generating summary statistics.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict


def load_evaluation_results(eval_file: str) -> List[Dict]:
    """Load evaluation results from JSONL file."""
    results = []
    with open(eval_file, 'r') as f:
        for line in f:
            results.append(json.loads(line))
    return results


def compute_statistics(results: List[Dict], metrics: List[str]) -> Dict:
    """
    Compute summary statistics for evaluation results.

    Args:
        results: List of evaluation result dictionaries
        metrics: List of metrics to analyze

    Returns:
        Dictionary with statistics
    """
    stats = {
        'total_questions': len(results),
        'metrics': {}
    }

    for metric in metrics:
        scores = []
        label_counts = defaultdict(int)

        for result in results:
            if metric not in result.get('evaluations', {}):
                continue

            eval_data = result['evaluations'][metric]

            # Get overall score
            score = eval_data.get(f'{metric}_score', -1)
            if score >= 0:
                scores.append(score)

            # Count labels from claim evaluations
            claim_evals = eval_data.get('claim_evaluations', [])
            for claim_eval in claim_evals:
                label = claim_eval.get('label', 'UNKNOWN')
                label_counts[label] += 1

        # Compute statistics
        if scores:
            stats['metrics'][metric] = {
                'mean_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'num_evaluated': len(scores),
                'label_distribution': dict(label_counts),
                'scores': scores  # Keep for detailed analysis
            }
        else:
            stats['metrics'][metric] = {
                'mean_score': -1,
                'num_evaluated': 0,
                'label_distribution': {}
            }

    # Compute aggregate statistics
    aggregate_scores = [r.get('aggregate_score', -1) for r in results if r.get('aggregate_score', -1) >= 0]
    if aggregate_scores:
        stats['aggregate'] = {
            'mean_score': sum(aggregate_scores) / len(aggregate_scores),
            'min_score': min(aggregate_scores),
            'max_score': max(aggregate_scores),
        }

    return stats


def print_summary(stats: Dict) -> None:
    """Print summary statistics in a readable format."""
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)

    print(f"\nTotal Questions Evaluated: {stats['total_questions']}")

    if 'aggregate' in stats:
        print(f"\nAggregate Score (Mean): {stats['aggregate']['mean_score']:.2f} / 5.0")
        print(f"Range: {stats['aggregate']['min_score']:.2f} - {stats['aggregate']['max_score']:.2f}")

    print("\n" + "-"*60)
    print("Per-Metric Statistics")
    print("-"*60)

    for metric, metric_stats in stats['metrics'].items():
        print(f"\n{metric.upper()}")
        print(f"  Mean Score: {metric_stats['mean_score']:.2f} / 5.0")
        if 'min_score' in metric_stats:
            print(f"  Range: {metric_stats['min_score']:.2f} - {metric_stats['max_score']:.2f}")
        print(f"  Evaluated: {metric_stats['num_evaluated']} questions")

        if metric_stats['label_distribution']:
            print(f"  Label Distribution:")
            for label, count in sorted(metric_stats['label_distribution'].items()):
                print(f"    {label}: {count}")

    print("\n" + "="*60)


def create_dataframe(results: List[Dict], metrics: List[str]) -> pd.DataFrame:
    """
    Create a pandas DataFrame from evaluation results.

    Args:
        results: List of evaluation result dictionaries
        metrics: List of metrics

    Returns:
        DataFrame with results
    """
    rows = []
    for result in results:
        row = {
            'question_idx': result['question_idx'],
            'video_id': result.get('video_id'),
            'segment_id': result.get('segment_id'),
            'question': result['question'],
            'model_response': result['model_response'],
            'ground_truth': result.get('ground_truth_answer'),
            'aggregate_score': result.get('aggregate_score', -1),
        }

        # Add metric scores
        for metric in metrics:
            if metric in result.get('evaluations', {}):
                score = result['evaluations'][metric].get(f'{metric}_score', -1)
                row[f'{metric}_score'] = score
            else:
                row[f'{metric}_score'] = -1

        rows.append(row)

    return pd.DataFrame(rows)


def export_summary(
    eval_file: str,
    output_dir: str,
    metrics: List[str] = ['factuality', 'coherence', 'relevance']
) -> None:
    """
    Export summary statistics and CSV.

    Args:
        eval_file: Path to evaluation JSONL file
        output_dir: Directory to save outputs
        metrics: List of metrics to analyze
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load results
    print(f"Loading results from: {eval_file}")
    results = load_evaluation_results(eval_file)

    # Compute statistics
    stats = compute_statistics(results, metrics)

    # Print summary
    print_summary(stats)

    # Save statistics as JSON
    stats_file = output_path / "summary_statistics.json"
    # Remove 'scores' list for cleaner JSON output
    stats_clean = {
        'total_questions': stats['total_questions'],
        'aggregate': stats.get('aggregate', {}),
        'metrics': {
            k: {kk: vv for kk, vv in v.items() if kk != 'scores'}
            for k, v in stats['metrics'].items()
        }
    }
    with open(stats_file, 'w') as f:
        json.dump(stats_clean, f, indent=2)
    print(f"\nStatistics saved to: {stats_file}")

    # Create and save DataFrame
    df = create_dataframe(results, metrics)
    csv_file = output_path / "evaluation_results.csv"
    df.to_csv(csv_file, index=False)
    print(f"CSV saved to: {csv_file}")

    # Save score distribution
    for metric in metrics:
        if metric in stats['metrics'] and 'scores' in stats['metrics'][metric]:
            scores = stats['metrics'][metric]['scores']
            score_dist_file = output_path / f"{metric}_score_distribution.txt"
            with open(score_dist_file, 'w') as f:
                f.write(f"{metric.upper()} Score Distribution\n")
                f.write("="*40 + "\n\n")
                for score in range(6):
                    count = scores.count(score)
                    pct = (count / len(scores) * 100) if scores else 0
                    bar = "█" * int(pct / 2)
                    f.write(f"Score {score}: {count:4d} ({pct:5.1f}%) {bar}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze MovieRecapsQA evaluation results")
    parser.add_argument(
        "--eval-file",
        type=str,
        required=True,
        help="JSONL file with evaluation results"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./analysis",
        help="Directory to save analysis outputs"
    )
    parser.add_argument(
        "--metrics",
        type=str,
        default="factuality,coherence,relevance",
        help="Comma-separated metrics to analyze"
    )

    args = parser.parse_args()

    metrics = [m.strip() for m in args.metrics.split(',')]

    export_summary(
        eval_file=args.eval_file,
        output_dir=args.output_dir,
        metrics=metrics
    )
