#!/bin/bash
#
# Complete batch processing pipeline for MovieRecapsQA evaluation
#
# Usage:
#   ./run_batch_pipeline.sh [stage]
#
# Stages:
#   1-create-claims    - Create claim extraction batch files
#   2-submit-claims    - Submit claim batches to OpenAI
#   3-status-claims    - Check claim batch status
#   4-download-claims  - Download claim results
#   5-process-claims   - Process claim results
#   all                - Run full pipeline (will pause between stages)
#
# Example:
#   ./run_batch_pipeline.sh all
#   ./run_batch_pipeline.sh 3-status-claims
#

set -e  # Exit on error

BATCH_DIR="batches"
CLAIMS_DIR="${BATCH_DIR}/claims"
CLAIMS_OUTPUT_DIR="${BATCH_DIR}/claims-output"
CLAIMS_BATCH_IDS="${BATCH_DIR}/claims_batch_ids.json"
CLAIMS_DATA="data/extracted_claims.jsonl"

BATCH_SIZE=1000
MODEL="gpt-4o-mini"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

stage_1_create_claims() {
    echo -e "${GREEN}=== Stage 1: Creating Claim Extraction Batches ===${NC}"
    python batch_openai.py create-claims \
        --output-dir "${CLAIMS_DIR}" \
        --batch-size ${BATCH_SIZE} \
        --model ${MODEL}
    echo -e "${GREEN}✓ Batch files created in ${CLAIMS_DIR}/${NC}\n"
}

stage_2_submit_claims() {
    echo -e "${GREEN}=== Stage 2: Submitting Batches to OpenAI ===${NC}"
    python batch_openai.py submit \
        --batch-dir "${CLAIMS_DIR}" \
        --output "${CLAIMS_BATCH_IDS}" \
        --description "MovieRecapsQA Claims Extraction"
    echo -e "${GREEN}✓ Batches submitted. IDs saved to ${CLAIMS_BATCH_IDS}${NC}\n"
    echo -e "${YELLOW}Note: Batches will complete within 24 hours.${NC}"
    echo -e "${YELLOW}Run './run_batch_pipeline.sh 3-status-claims' to check progress.${NC}\n"
}

stage_3_status_claims() {
    echo -e "${GREEN}=== Stage 3: Checking Batch Status ===${NC}"
    if [ ! -f "${CLAIMS_BATCH_IDS}" ]; then
        echo -e "${RED}Error: ${CLAIMS_BATCH_IDS} not found. Run stage 2 first.${NC}"
        exit 1
    fi
    python batch_openai.py status --batch-ids "${CLAIMS_BATCH_IDS}"
}

stage_4_download_claims() {
    echo -e "${GREEN}=== Stage 4: Downloading Results ===${NC}"
    if [ ! -f "${CLAIMS_BATCH_IDS}" ]; then
        echo -e "${RED}Error: ${CLAIMS_BATCH_IDS} not found. Run stage 2 first.${NC}"
        exit 1
    fi
    python batch_openai.py download \
        --batch-ids "${CLAIMS_BATCH_IDS}" \
        --output-dir "${CLAIMS_OUTPUT_DIR}"
    echo -e "${GREEN}✓ Results downloaded to ${CLAIMS_OUTPUT_DIR}/${NC}\n"
}

stage_5_process_claims() {
    echo -e "${GREEN}=== Stage 5: Processing Results ===${NC}"
    mkdir -p data
    python batch_openai.py process-claims \
        --input-dir "${CLAIMS_OUTPUT_DIR}" \
        --output "${CLAIMS_DATA}"
    echo -e "${GREEN}✓ Processed claims saved to ${CLAIMS_DATA}${NC}\n"
}

wait_for_completion() {
    echo -e "${YELLOW}Waiting for batches to complete...${NC}"
    echo -e "${YELLOW}Checking status every 5 minutes. Press Ctrl+C to stop.${NC}\n"

    while true; do
        # Get status
        python batch_openai.py status --batch-ids "${CLAIMS_BATCH_IDS}" > /tmp/batch_status.txt 2>&1

        # Check if all completed
        if grep -q "Completed: $(wc -l < "${CLAIMS_BATCH_IDS}")" /tmp/batch_status.txt 2>/dev/null; then
            echo -e "\n${GREEN}All batches completed!${NC}\n"
            break
        fi

        # Show current status
        cat /tmp/batch_status.txt

        # Wait 5 minutes
        echo -e "\n${YELLOW}Checking again in 5 minutes...${NC}"
        sleep 300
    done
}

run_all() {
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}MovieRecapsQA Batch Processing - Full Pipeline${NC}"
    echo -e "${GREEN}================================================${NC}\n"

    # Stage 1: Create batches
    stage_1_create_claims

    # Stage 2: Submit batches
    stage_2_submit_claims

    # Wait for user confirmation or auto-wait
    echo -e "${YELLOW}Choose an option:${NC}"
    echo -e "  1) Wait automatically (checks every 5 minutes)"
    echo -e "  2) I'll check manually later"
    read -p "Enter choice (1 or 2): " choice

    if [ "$choice" = "1" ]; then
        wait_for_completion

        # Stage 4: Download
        stage_4_download_claims

        # Stage 5: Process
        stage_5_process_claims

        echo -e "${GREEN}================================================${NC}"
        echo -e "${GREEN}Pipeline Complete!${NC}"
        echo -e "${GREEN}================================================${NC}"
        echo -e "\nClaims data: ${CLAIMS_DATA}"
        echo -e "\nNext steps:"
        echo -e "  - Use ${CLAIMS_DATA} for evaluation"
        echo -e "  - Run evaluation pipeline with eval scripts"
        echo -e "\n"
    else
        echo -e "\n${YELLOW}To resume later, run:${NC}"
        echo -e "  ./run_batch_pipeline.sh 3-status-claims  # Check status"
        echo -e "  ./run_batch_pipeline.sh 4-download-claims  # Download when ready"
        echo -e "  ./run_batch_pipeline.sh 5-process-claims  # Process results"
        echo -e "\n"
    fi
}

# Main script
case "${1:-all}" in
    1-create-claims)
        stage_1_create_claims
        ;;
    2-submit-claims)
        stage_2_submit_claims
        ;;
    3-status-claims)
        stage_3_status_claims
        ;;
    4-download-claims)
        stage_4_download_claims
        ;;
    5-process-claims)
        stage_5_process_claims
        ;;
    all)
        run_all
        ;;
    *)
        echo "Usage: $0 [stage]"
        echo ""
        echo "Stages:"
        echo "  1-create-claims    - Create claim extraction batch files"
        echo "  2-submit-claims    - Submit claim batches to OpenAI"
        echo "  3-status-claims    - Check claim batch status"
        echo "  4-download-claims  - Download claim results"
        echo "  5-process-claims   - Process claim results"
        echo "  all                - Run full pipeline"
        echo ""
        echo "Example:"
        echo "  $0 all"
        echo "  $0 3-status-claims"
        exit 1
        ;;
esac
