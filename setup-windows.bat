@echo off
echo ========================================
echo PolicyGraph Windows Setup
echo ========================================
echo.

REM Check Python version
python --version
echo.

REM Check if Python 3.11 or compatible
python -c "import sys; exit(0 if sys.version_info[:2] in [(3,9), (3,10), (3,11)] else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.9, 3.10, or 3.11 required
    echo You have a different version. Please install Python 3.11
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python version OK
echo.

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
if errorlevel 1 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install PyTorch
echo Installing PyTorch (CPU version)...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

REM Install DGL
echo Installing DGL...
pip install dgl==1.1.3 -f https://data.dgl.ai/wheels/repo.html

REM Install other dependencies
echo Installing other dependencies...
pip install scikit-learn pyyaml matplotlib pandas seaborn pytest

REM Install PolicyGraph
echo Installing PolicyGraph...
pip install -e .

REM Verify
echo.
echo Verifying installation...
python -c "import policygraph; print(f'PolicyGraph v{policygraph.__version__}')"

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To activate the environment in the future:
echo   .venv\Scripts\activate
echo.
pause
