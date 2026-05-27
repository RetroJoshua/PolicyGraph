#!/bin/bash
# PolicyGraph Labeling Workflow
# ==============================
#
# Quick-start commands for the dataset expansion pipeline.
# See LABELING_GUIDE.md and DATASET_EXPANSION.md for full documentation.

set -e
cd "$(dirname "$0")/.."

echo "PolicyGraph Labeling Workflow"
echo "=============================="
echo ""
echo "Step 1: Score all policies with the model (2-3 minutes)"
echo "  python scripts/label_scraped_policies.py --scraped data/scraped_policies --out data/labeled_policies --model checkpoints/long/best_model.pt --score-only"
echo ""
echo "Step 2: Review policies interactively (can quit and resume)"
echo "  python scripts/label_scraped_policies.py --scraped data/scraped_policies --out data/labeled_policies --review-only"
echo ""
echo "Step 3: Merge with original dataset"
echo "  python scripts/merge_labeled_datasets.py --original data/raw/samples --new data/labeled_policies --output data/raw/samples_expanded"
echo ""
echo "Step 4: Update config.yaml to use expanded dataset"
echo "  # Edit config.yaml: data_dir: data/raw/samples_expanded"
echo ""
echo "Step 5: Retrain with expanded dataset"
echo "  policygraph train"
echo ""
echo "────────────────────────────────────────"
echo ""
echo "Other useful commands:"
echo ""
echo "  # Test on 5 policies first"
echo "  python scripts/label_scraped_policies.py --scraped data/scraped_policies --out data/labeled_policies --model checkpoints/long/best_model.pt --limit 5"
echo ""
echo "  # Check labeling progress"
echo "  python -c \"import json; s=json.load(open('data/labeled_policies/labeling_state.json')); print(f'Reviewed: {s[\\\"total_reviewed\\\"]}')\""
echo ""
echo "  # Dry-run merge (see stats without writing)"
echo "  python scripts/merge_labeled_datasets.py --original data/raw/samples --new data/labeled_policies --output data/raw/samples_expanded --dry-run"
echo ""
