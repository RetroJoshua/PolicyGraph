#!/bin/bash

echo "🚀 PolicyGraph Quick Start"
echo ""

# Activate venv
source .venv/bin/activate

# Train
echo "1️⃣  Training model (this may take a few minutes)..."
policygraph train --epochs 20

# Evaluate
echo ""
echo "2️⃣  Evaluating model..."
policygraph evaluate

# Show results
echo ""
echo "3️⃣  Results:"
cat results/evaluation_report.json | python -m json.tool

echo ""
echo "✅ Quick start complete!"
echo ""
echo "Results saved to: results/evaluation_report.json"
