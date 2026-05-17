# PolicyGraph - Windows Installation Guide

## ⚠️ Important: Python Version Requirement

**PolicyGraph requires Python 3.9, 3.10, or 3.11 (NOT 3.12 or 3.13)**

DGL (Deep Graph Library) doesn't support Python 3.12+ yet.

## Check Your Python Version

```cmd
python --version
```

If you see `Python 3.13.x` or `Python 3.12.x`, you need to install Python 3.11.

---

## Option A: Install Python 3.11 (Recommended)

### 1. Download Python 3.11
- Go to: https://www.python.org/downloads/
- Download **Python 3.11.x** (latest 3.11 version)
- Run the installer
- ✅ Check "Add Python to PATH"
- ✅ Check "Install for all users"

### 2. Verify Installation
```cmd
python --version
# Should show: Python 3.11.x
```

### 3. Create Virtual Environment with Python 3.11
```cmd
cd C:\Users\user\Documents\CMRIT\projects\PolicyGraph

# Use Python 3.11 specifically
py -3.11 -m venv .venv

# OR if py launcher doesn't work:
python -m venv .venv
```

### 4. Activate Virtual Environment
```cmd
.venv\Scripts\activate
```

You should see `(.venv)` in your prompt.

### 5. Install Dependencies Step-by-Step
```cmd
# Upgrade pip first
python -m pip install --upgrade pip

# Install PyTorch (CPU version for Windows)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install DGL (from DGL wheel server)
pip install dgl==1.1.3 -f https://data.dgl.ai/wheels/repo.html

# Install other dependencies
pip install scikit-learn pyyaml matplotlib pandas seaborn

# Finally, install PolicyGraph
pip install -e .
```

### 6. Verify Installation
```cmd
python -c "import policygraph; print(f'PolicyGraph v{policygraph.__version__}')"
```

Should print: `PolicyGraph v0.1.0`

---

## Option B: Manual Installation (If You Must Use Python 3.13)

⚠️ **Not recommended** - Limited compatibility

### Install CPU-only versions:
```cmd
# Install PyTorch
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Skip DGL, install NetworkX as fallback
pip install networkx scikit-learn pyyaml matplotlib pandas

# Manually edit setup.py to make DGL optional
```

**Note:** Some features won't work without DGL.

---

## Option C: Use Windows Subsystem for Linux (WSL)

If you have WSL installed:

```bash
# In WSL terminal
cd /mnt/c/Users/user/Documents/CMRIT/projects/PolicyGraph

# Use the Linux setup script
bash setup.sh
```

---

## Troubleshooting

### Error: "No matching distribution found for dgl"
**Cause:** Python version too new (3.12+)
**Solution:** Install Python 3.11 (see Option A)

### Error: "Microsoft Visual C++ 14.0 is required"
**Solution:** Install Visual Studio Build Tools
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
- Install "Desktop development with C++"

### Error: "torch" not found
**Solution:** 
```cmd
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

### DGL installation is slow
**Cause:** Building from source
**Solution:** Use pre-built wheels:
```cmd
pip install dgl==1.1.3 -f https://data.dgl.ai/wheels/repo.html
```

---

## Quick Start After Installation

```cmd
# Activate environment
.venv\Scripts\activate

# Train model
python scripts/train.py --epochs 20

# Evaluate
python scripts/evaluate.py

# Analyze a policy
python -m policygraph analyze data/raw/samples/escalation_passrole_lambda_create.json
```

---

## GPU Support (Optional)

If you have an NVIDIA GPU:

```cmd
# Install CUDA toolkit first
# Then install GPU version of PyTorch:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install GPU version of DGL:
pip install dgl-cu118==1.1.3 -f https://data.dgl.ai/wheels/repo.html
```
