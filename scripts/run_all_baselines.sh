#!/usr/bin/env bash
# ==============================================================================
# PolicyGraph Baseline Comparison - Master Runner Script
# ==============================================================================
#
# Runs all baseline tools, parses results, generates comparison tables
# and visualizations. Usage:
#
#   bash scripts/run_all_baselines.sh [--skip-tfsec] [--skip-iam] [--only-wrap]
#
# Options:
#   --skip-tfsec    Skip tfsec (if not installed)
#   --skip-iam      Skip IAM Access Analyzer (if no AWS credentials)
#   --only-wrap     Only generate wrapped policies, don't run tools
#   --help          Show this help message
# ==============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Logging
LOG_FILE="results/baseline_run_$(date +%Y%m%d_%H%M%S).log"
mkdir -p results/figures

# Options
SKIP_TFSEC=false
SKIP_IAM=false
ONLY_WRAP=false

for arg in "$@"; do
    case $arg in
        --skip-tfsec) SKIP_TFSEC=true ;;
        --skip-iam) SKIP_IAM=true ;;
        --only-wrap) ONLY_WRAP=true ;;
        --help)
            head -20 "$0" | tail -15
            exit 0
            ;;
    esac
done

log() {
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date +%H:%M:%S)] ✓${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date +%H:%M:%S)] ⚠${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +%H:%M:%S)] ✗${NC} $1" | tee -a "$LOG_FILE"
}

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║        PolicyGraph Baseline Comparison Pipeline         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log "Started at $(date)"
log "Project root: $PROJECT_ROOT"
echo ""

# ==============================================================================
# Step 1: Check prerequisites
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Step 1: Checking prerequisites..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python
if command -v python3 &>/dev/null; then
    success "Python3: $(python3 --version 2>&1)"
else
    error "Python3 not found!"
    exit 1
fi

# PyYAML
if python3 -c "import yaml" 2>/dev/null; then
    success "PyYAML: installed"
else
    warn "PyYAML not installed. Installing..."
    pip install pyyaml >/dev/null 2>&1
fi

# Matplotlib
if python3 -c "import matplotlib" 2>/dev/null; then
    success "Matplotlib: installed"
else
    warn "Matplotlib not installed. Installing..."
    pip install matplotlib seaborn >/dev/null 2>&1
fi

# Checkov
if command -v checkov &>/dev/null; then
    success "Checkov: $(checkov --version 2>&1 | head -1)"
else
    warn "Checkov not found. Will attempt installation during run."
fi

# tfsec
if [ "$SKIP_TFSEC" = false ]; then
    if command -v tfsec &>/dev/null; then
        success "tfsec: $(tfsec --version 2>&1 | head -1)"
    else
        warn "tfsec not found. Will create placeholder results."
    fi
else
    log "tfsec: skipped (--skip-tfsec)"
fi

# AWS CLI
if [ "$SKIP_IAM" = false ]; then
    if command -v aws &>/dev/null; then
        if aws sts get-caller-identity &>/dev/null 2>&1; then
            success "AWS CLI: credentials configured"
        else
            warn "AWS CLI installed but credentials not configured"
            SKIP_IAM=true
        fi
    else
        warn "AWS CLI not found. Skipping IAM Access Analyzer."
        SKIP_IAM=true
    fi
else
    log "IAM Access Analyzer: skipped (--skip-iam)"
fi

# Policy files
POLICY_COUNT=$(ls data/raw/samples/*.json 2>/dev/null | grep -v LABELS | wc -l)
success "Policy files: $POLICY_COUNT"
echo ""

# ==============================================================================
# Step 2: Wrap policies for each tool
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Step 2: Wrapping policies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

log "  2a: Wrapping for Checkov (CloudFormation)..."
python3 scripts/wrappers/wrap_for_checkov.py 2>&1 | tee -a "$LOG_FILE"
success "CloudFormation wrapping complete"
echo ""

log "  2b: Wrapping for tfsec (Terraform)..."
python3 scripts/wrappers/wrap_for_tfsec.py 2>&1 | tee -a "$LOG_FILE"
success "Terraform wrapping complete"
echo ""

if [ "$ONLY_WRAP" = true ]; then
    success "Wrapping complete (--only-wrap specified)"
    exit 0
fi

# ==============================================================================
# Step 3: Run Checkov
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Step 3: Running Checkov..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 scripts/baselines/run_checkov.py 2>&1 | tee -a "$LOG_FILE"
success "Checkov scan complete"
echo ""

# ==============================================================================
# Step 4: Run tfsec
# ==============================================================================
if [ "$SKIP_TFSEC" = false ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Step 4: Running tfsec..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 scripts/baselines/run_tfsec.py 2>&1 | tee -a "$LOG_FILE"
    success "tfsec scan complete"
else
    log "Step 4: Skipping tfsec"
fi
echo ""

# ==============================================================================
# Step 5: Run IAM Access Analyzer
# ==============================================================================
if [ "$SKIP_IAM" = false ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "Step 5: Running IAM Access Analyzer..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    python3 scripts/baselines/run_iam_analyzer.py 2>&1 | tee -a "$LOG_FILE"
    success "IAM Access Analyzer complete"
else
    log "Step 5: Skipping IAM Access Analyzer (creating placeholder)"
    python3 scripts/baselines/run_iam_analyzer.py 2>&1 | tee -a "$LOG_FILE"
fi
echo ""

# ==============================================================================
# Step 6: Parse all results
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Step 6: Parsing results and computing metrics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 scripts/baselines/parse_baseline_results.py 2>&1 | tee -a "$LOG_FILE"
success "Results parsed"
echo ""

# ==============================================================================
# Step 7: Generate comparison
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Step 7: Generating comparison tables..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 scripts/baselines/compare_all_tools.py 2>&1 | tee -a "$LOG_FILE"
success "Comparison tables generated"
echo ""

# ==============================================================================
# Step 8: Create visualizations
# ==============================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
log "Step 8: Creating visualizations..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 scripts/baselines/visualize_comparison.py 2>&1 | tee -a "$LOG_FILE"
success "Visualizations created"
echo ""

# ==============================================================================
# Step 9: Summary
# ==============================================================================
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Pipeline Complete!                         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
log "Completed at $(date)"
echo ""
echo "Output files:"
echo "  results/checkov_results.json"
echo "  results/tfsec_results.json"
echo "  results/iam_analyzer_results.json"
echo "  results/all_baseline_metrics.json"
echo "  results/baseline_comparison.csv"
echo "  results/baseline_comparison.md"
echo "  results/figures/*.png"
echo "  $LOG_FILE"
echo ""

# Print comparison table from markdown
if [ -f results/baseline_comparison.md ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Comparison Summary:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    # Extract table from markdown
    grep -A 20 "^|" results/baseline_comparison.md | head -20
fi
echo ""
