#!/bin/bash
#
# Complete evaluation pipeline for MovieRecapsQA
#
# Usage:
#   ./run_eval.sh <output_prefix>
#
# Example:
#   ./run_eval.sh gpt4-output
#   ./run_eval.sh lava-output
#

set -e  # Exit on error

# Check arguments
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <output_prefix>"
    echo ""
    echo "Examples:"
    echo "  $0 gpt4-output"
    echo "  $0 lava-output"
    exit 1
fi

OUTPUT_PREFIX=$1

# Create outputs directory
mkdir -p outputs

echo "=================================================="
echo "MovieRecapsQA Evaluation Pipeline"
echo "=================================================="
echo "Output Prefix: $OUTPUT_PREFIX"
echo ""


# Step 1: Evaluate responses
echo "Step 1: Evaluating responses..."
echo "--------------------------------------------------"
python evaluator.py \
    --responses "outputs/${OUTPUT_PREFIX}_responses.jsonl" \
    --output "outputs/${OUTPUT_PREFIX}_evaluation.jsonl"

echo ""
echo "✓ Evaluation complete: outputs/${OUTPUT_PREFIX}_evaluation.jsonl"
echo ""

# Step 2: Analyze results
echo "Step 2: Analyzing results..."
echo "--------------------------------------------------"
python analyze_results.py \
    --eval-file "outputs/${OUTPUT_PREFIX}_evaluation.jsonl" \
    --output-dir "outputs/${OUTPUT_PREFIX}_analysis"

echo ""
echo "✓ Analysis complete: outputs/${OUTPUT_PREFIX}_analysis/"
echo ""

echo "=================================================="
echo "Pipeline Complete!"
echo "=================================================="
echo ""
echo "Results:"
echo "  - Responses:  outputs/${OUTPUT_PREFIX}_responses.jsonl"
echo "  - Evaluation: outputs/${OUTPUT_PREFIX}_evaluation.jsonl"
echo "  - Analysis:   outputs/${OUTPUT_PREFIX}_analysis/"
echo ""
echo "View summary statistics:"
echo "  cat outputs/${OUTPUT_PREFIX}_analysis/summary_statistics.json"
echo ""
