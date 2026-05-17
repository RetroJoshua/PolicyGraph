from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

INSTALL_REQUIRES = [
    "torch>=2.0.0",
    "dgl>=1.1.0,<2.0.0",
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
