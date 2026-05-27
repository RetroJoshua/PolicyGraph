import sys
from pathlib import Path

from setuptools import find_packages, setup

# Check Python version
if sys.version_info[:2] not in [(3, 9), (3, 10), (3, 11)]:
    print("=" * 60)
    print("ERROR: PolicyGraph requires Python 3.9, 3.10, or 3.11")
    print(f"You are using Python {sys.version_info.major}.{sys.version_info.minor}")
    print("")
    print("DGL (Deep Graph Library) doesn't support Python 3.12+ yet.")
    print("")
    print("Please install Python 3.11:")
    print("  Windows: https://www.python.org/downloads/")
    print("  Linux: sudo apt install python3.11")
    print("  Mac: brew install python@3.11")
    print("")
    print("See WINDOWS_SETUP.md for detailed Windows instructions.")
    print("=" * 60)
    sys.exit(1)

ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

INSTALL_REQUIRES = [
    "torch>=2.0.0",
    # DGL 1.1.x is the supported range. Note: 1.1.3 does NOT exist on the
    # DGL wheel server (https://data.dgl.ai/wheels/repo.html); the latest
    # available 1.1.x is 1.1.2. DGL 2.x introduces a graphbolt dependency
    # that we don't support yet, so cap below 1.2.0.
    "dgl>=1.1.0,<1.2.0",
    "networkx>=3.0",
    "pyyaml>=6.0",
    "scikit-learn>=1.2.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
    "tqdm>=4.65.0",
    "matplotlib>=3.7.0",
]

DEV_REQUIRES = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "tensorboard>=2.14.0",
]

setup(
    name="policygraph",
    version="0.1.0",
    description="Graph Neural Networks for AWS IAM policy security analysis",
    long_description=README,
    long_description_content_type="text/markdown",
    author="PolicyGraph Authors",
    license="MIT",
    python_requires=">=3.9",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=INSTALL_REQUIRES,
    extras_require={"dev": DEV_REQUIRES},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "policygraph=policygraph.__main__:main",
        ]
    },
    keywords=["aws", "iam", "security", "gnn", "dgl", "pytorch"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    project_urls={
        "Documentation": "https://github.com/RetroJoshua/PolicyGraph",
        "Source": "https://github.com/RetroJoshua/PolicyGraph",
        "Issues": "https://github.com/RetroJoshua/PolicyGraph/issues",
    },
)


# ---------------------------------------------------------------------------
# Post-install / post-build DGL version sanity check.
#
# When setup.py is executed directly (e.g. `python setup.py develop` or the
# post-install hook in `pip install -e .` environments), surface a clear
# warning if the installed DGL is outside the 1.1.x supported range. This is
# best-effort: we never raise here, because setup.py is also imported by
# tooling that doesn't have DGL on the path.
# ---------------------------------------------------------------------------
try:
    import dgl  # type: ignore

    _dgl_version = getattr(dgl, "__version__", "unknown")
    print(f"DGL version: {_dgl_version}")
    if not str(_dgl_version).startswith("1.1"):
        print(
            "Warning: Recommended DGL version is 1.1.x (currently using "
            f"{_dgl_version}). Install the supported version with:\n"
            "    pip install 'dgl>=1.1.0,<1.2.0' "
            "-f https://data.dgl.ai/wheels/repo.html"
        )
except ImportError:
    # DGL not yet installed (e.g. first-time install). The pip resolver will
    # pull it from INSTALL_REQUIRES.
    pass
