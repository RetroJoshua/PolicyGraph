# PolicyGraph - Complete Setup Guide

## Prerequisites
- Python 3.9 or higher
- pip (Python package manager)
- Git

## Step-by-Step Setup

### 1. Navigate to Repository
```bash
cd PolicyGraph  # Or wherever you cloned it
```

### 2. Create Virtual Environment
```bash
# Create the virtual environment
python3 -m venv .venv

# OR if python3 doesn't work, try:
python -m venv .venv
```

### 3. Activate Virtual Environment

**On Linux/Mac:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

You should see `(.venv)` appear in your terminal prompt.

### 4. Upgrade pip
```bash
pip install --upgrade pip
```

### 5. Install PolicyGraph
```bash
# Install in editable mode with all dependencies
pip install -e .
```

This will install:
- torch (PyTorch)
- dgl (Deep Graph Library)
- scikit-learn
- PyYAML
- matplotlib
- and all other dependencies

### 6. Verify Installation
```bash
# Check version
python -c "import policygraph; print(f'PolicyGraph v{policygraph.__version__}')"

# Should print: PolicyGraph v0.1.0
```

### 7. Run Tests
```bash
# Install pytest if needed
pip install pytest

# Run all tests
pytest tests/ -v
```

### 8. Quick Test Run
```bash
# Analyze a sample policy
policygraph analyze data/raw/samples/escalation_passrole_lambda_create.json
```

## Troubleshooting

### Issue: "command not found: python3"
**Solution:** Try `python` instead of `python3`

### Issue: "No module named 'torch'"
**Solution:** Run `pip install -e .` again

### Issue: DGL installation fails
**Solution:**
```bash
# Install DGL manually
pip install dgl==1.1.3 -f https://data.dgl.ai/wheels/repo.html
```

### Issue: "policygraph: command not found"
**Solution:** Make sure virtual environment is activated and run `pip install -e .`

## Quick Start Commands

After setup, you can use:
```bash
# Train model
policygraph train

# Evaluate model
policygraph evaluate

# Analyze single policy
policygraph analyze <policy.json>

# Batch analysis
policygraph batch data/raw/samples/

# Run baseline comparison
bash scripts/run_all_baselines.sh
```
