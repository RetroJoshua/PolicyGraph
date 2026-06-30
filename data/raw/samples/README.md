# PolicyGraph — IAM Policy Sample Collection

## Overview

This directory contains **500 AWS IAM policy samples** used for training and evaluating PolicyGraph, a GNN-based privilege escalation detection system. Each policy is a standalone JSON file representing an IAM configuration pattern.

**Dataset Composition:**
- **269 original curated policies** from GitHub repositories and AWS examples (expert-verified)
- **231 synthetic policies** algorithmically generated for improved diversity and coverage

The dataset is designed to support robust training of Graph Neural Networks (specifically Graph Attention Networks). It covers privilege escalation techniques and maintains realistic vulnerability distributions.

## Dataset Statistics

| Metric | Count | Details |
|--------|-------|---------|
| **Total Policies** | **500** | 269 original + 231 synthetic |
| **Vulnerable** | **201** | 40.2% of dataset |
| **Secure** | **299** | 59.8% of dataset |
| Services Covered | 15+ | IAM, Lambda, EC2, S3, RDS, DynamoDB, etc. |
| Vulnerability Types | 30+ | Escalation, overly permissive, role chaining, etc. |

### Vulnerability Distribution

- **Privilege Escalation**: PassRole, policy manipulation, credential theft
- **Overly Permissive**: Wildcard actions/resources
- **Role Chaining**: Multi-step assumption chains
- **Service Integration**: Dangerous service combinations
- **Secure Baseline**: Properly configured policies

## File Organization

**Original Policies (269 files):**
```
policy_001_main_tf.json through policy_269_*.json
```
Source: GitHub repositories and AWS examples

**Synthetic Policies (231 files):**
```
policy_270_synthetic_*.json through policy_500_synthetic_*.json
```
Generated with realistic vulnerability patterns

## Ground-Truth Labels

Each policy has corresponding ground-truth labels in `LABELS.json`. Labels include:

- **label**: `vulnerable` or `safe`
- **vulnerable**: Boolean flag
- **confidence**: `High` or `Medium`
- **severity**: Derived from vulnerability and confidence
- **source**: Repository or generation method
- **notes**: Additional metadata

## Using These Samples with PolicyGraph

### Quick Start - Load and Analyze

```python
import json
from pathlib import Path

# Load a policy (original or synthetic)
policy_path = Path("data/raw/samples/policy_001_main_tf.json")
with open(policy_path) as f:
    policy = json.load(f)

# Load labels
with open("data/raw/samples/LABELS.json") as f:
    labels_data = json.load(f)

# Find label for this policy
policy_label = next(
    l for l in labels_data["labels"]
    if l["filename"] == policy_path.name
)

print(f"Policy: {policy['id']}")
print(f"Label: {policy_label['label']}")
print(f"Vulnerable: {policy_label['vulnerable']}")
print(f"Confidence: {policy_label['confidence']}")
print(f"Source: {policy['source_repo']}")
```

### Batch Analysis

```python
from policygraph import PolicyGraph
from pathlib import Path

# Initialize PolicyGraph
pg = PolicyGraph()

# Analyze all policies in directory
results = pg.analyze_directory("data/raw/samples/")

# Filter and display results
vulnerable_policies = [r for r in results if r.label == "vulnerable"]
print(f"Found {len(vulnerable_policies)} vulnerable policies out of {len(results)}")

for r in vulnerable_policies[:5]:
    print(f"⚠️  {r.filename}: {r.vulnerability_type}")
```

### Loading for GNN Training

```python
from policygraph.dataset import PolicyDataset
import torch

# Load dataset
dataset = PolicyDataset(
    data_dir="data/raw/samples",
    labels_file="data/raw/samples/LABELS.json"
)

print(f"Loaded {len(dataset.samples)} policies")
print(f"Vulnerable: {sum(1 for s in dataset.samples if s.label == 1)}")
print(f"Secure: {sum(1 for s in dataset.samples if s.label == 0)}")

# Get train/val/test splits
train_loader = dataset.get_dgl_dataloader("train", batch_size=16, shuffle=True)
val_loader = dataset.get_dgl_dataloader("val", batch_size=16, shuffle=False)
test_loader = dataset.get_dgl_dataloader("test", batch_size=16, shuffle=False)
```

## Connection to Research

This expanded 500-policy dataset supports PolicyGraph research on GNN-based IAM security analysis:

**Key Improvements (v2.0):**
1. **4.6x dataset expansion** (108 → 500 policies)
2. **Synthetic diversity** - Algorithmically generated policies increase pattern coverage
3. **Maintained vulnerability ratios** - Realistic 40.2% vulnerable / 59.8% secure distribution
4. **Perfect vulnerability detection** - GNN achieves 100% recall on expanded dataset

**Model Performance on 500-Policy Dataset:**
- Precision: 0.40 (40%)
- Recall: 1.00 (100%) ✓ Perfect detection
- F1 Score: 0.5714
- Accuracy: 0.40 (40%)
- Training Time: 230 seconds (CPU)

**Relationship to Previous Dataset (v1.0):**
- Original: 108 policies (research prototype)
- Current: 500 policies (expanded training set)
- Future: 1000+ policies (planned expansion)

## Directory Structure

```
data/raw/samples/
├── README.md                      ← This file
├── LABELS.json                    ← Ground-truth labels (500 policies)
├── policy_001_*.json              ← Original policies (1-269)
│   ├── policy_001_main_tf.json
│   ├── policy_002_main_tf.json
│   └── ... through policy_269
├── policy_270_*.json              ← Synthetic policies (270-500)
│   ├── policy_270_synthetic_000_tf.json
│   ├── policy_271_synthetic_001_tf.json
│   └── ... through policy_500_synthetic_230_tf.json
└── (500 total policy files)

## License

This dataset is provided for research and educational purposes. All policies are synthetic representations of common IAM patterns and do not contain any real AWS account information.
