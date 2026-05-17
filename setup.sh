#!/bin/bash

echo "🚀 PolicyGraph Setup Script"
echo "============================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version || python --version

# Determine python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

echo "Using: $PYTHON_CMD"
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
$PYTHON_CMD -m venv .venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created"
echo ""

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip -q

echo "✅ pip upgraded"
echo ""

# Install PolicyGraph
echo "📥 Installing PolicyGraph..."
pip install -e . -q

if [ $? -ne 0 ]; then
    echo "❌ Failed to install PolicyGraph"
    exit 1
fi

echo "✅ PolicyGraph installed"
echo ""

# Verify installation
echo "🔍 Verifying installation..."
python -c "import policygraph; print(f'PolicyGraph v{policygraph.__version__}')"

if [ $? -ne 0 ]; then
    echo "❌ Installation verification failed"
    exit 1
fi

echo "✅ Installation verified"
echo ""

# Install pytest
echo "🧪 Installing pytest..."
pip install pytest -q

echo "✅ pytest installed"
echo ""

# Run tests
echo "🧪 Running tests..."
pytest tests/ -v

if [ $? -ne 0 ]; then
    echo "⚠️  Some tests failed"
else
    echo "✅ All tests passed"
fi

echo ""
echo "=============================="
echo "✅ Setup Complete!"
echo "=============================="
echo ""
echo "Next steps:"
echo "1. Activate the virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Try analyzing a policy:"
echo "   policygraph analyze data/raw/samples/escalation_passrole_lambda_create.json"
echo ""
echo "3. Train the model:"
echo "   policygraph train"
echo ""
echo "4. Run baseline comparison:"
echo "   bash scripts/run_all_baselines.sh"
echo ""
