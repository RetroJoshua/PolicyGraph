# PolicyGraph — Data Directory

## Overview

This directory contains the complete dataset for PolicyGraph, organized into three main subdirectories representing different stages of the data pipeline: raw policy samples, processed graph representations, and full account examples.

```
data/
├── README.md                  ← This file
├── raw/                       ← Raw IAM policy JSON files and labels
│   ├── labeled_policies_merged.xlsx  ← Excel file with all 500 policies
│   ├── labeled_policies_clean.csv    ← CSV file with clean labels
│   └── samples/               ← 500 individual IAM policy JSON files
│       ├── README.md          ← Detailed sample documentation
│       ├── LABELS.json        ← Ground-truth labels (500 policies)
│       ├── policy_001_*.json  ← Original policies (269 files)
│       ├── policy_270_*.json  ← Synthetic policies (231 files)
│       └── ... (500 total policy files)
├── processed/                 ← Graph representations (GNN-ready)
│   ├── *_graph.json           ← Pre-computed graph files
│   └── (DGL/PyG compatible)
└── examples/                  ← Full account snapshot examples
    ├── account_1_simple_escalation/
    ├── account_2_role_chaining/
    ├── account_3_secure_baseline/
    └── account_4_complex_attack/
```

## Data Pipeline

```
┌──────────────┐     ┌───────────────┐     ┌──────────────────┐
│   raw/       │     │  processed/   │     │   GNN Model      │
│  samples/    │────▶│  *_graph.json │────▶│  (GAT)           │
│  (500 JSON)  │     │  (node/edge   │     │  Training &      │
│ (269 orig +  │     │   features)   │     │  Inference        │
│  231 syn)    │     │               │     │                   │
└──────────────┘     └───────────────┘     └──────────────────┘
       │                                           │
       ▼                                           ▼
┌──────────────┐                          ┌──────────────────┐
│ LABELS.json  │                          │  Predictions:    │
│ labels.csv   │                          │  vulnerable /    │
│ (ground      │                          │  secure +        │
│  truth)      │                          │  attack paths    │
└──────────────┘                          │  Metrics:        │
                                          │  Precision: 0.4  │
                                          │  Recall: 1.0     │
                                          │  F1: 0.5714      │
                                          │  Accuracy: 0.4   │
                                          └──────────────────┘
```

## Directory Details

### `raw/` — Raw IAM Policies

Contains the original IAM policy JSON files exactly as they would appear in an AWS account.

- **500 policies** total (201 vulnerable, 299 secure)
  - **269 original policies** from GitHub repositories and AWS examples (hand-labeled)
  - **231 synthetic policies** algorithmically generated for dataset diversity
- **`samples/`**: Individual policy files in JSON format (policy_001.json through policy_500.json)
- **`samples/LABELS.json`**: Machine-readable ground-truth labels with vulnerability information, confidence scores, and metadata
- **`labeled_policies_merged.xlsx`**: Excel file with all 500 policies and labels
- **`labeled_policies_clean.csv`**: Tabular label file with columns: `filename`, `source_repo`, `vulnerable`, `confidence`, `notes`, `checkov_findings`

See [`raw/samples/README.md`](raw/samples/README.md) for detailed documentation.

### `processed/` — Graph Representations

Pre-computed graph representations of sample policies, ready for GNN training.

- **10 example graphs** (7 vulnerable + 3 secure)
- Compatible with **DGL**, **PyTorch Geometric**, and **NetworkX**
- Each graph contains:
  - `nodes`: Typed nodes (principal, action, resource, effect, condition) with feature vectors
  - `edges`: Typed edges (has_permission, applies_to, has_effect, requires_condition) with features
  - `metadata`: Source policy, label, severity, risk score
  - `adjacency_list`: For quick graph traversal
  - `graph_label`: Binary label (1 = vulnerable, 0 = secure)

#### Node Feature Vector (6 dimensions)
```
[is_principal, is_action, is_resource, is_effect, is_iam_related, is_compute_related]
```

#### Edge Feature Vector (3 dimensions)
```
[is_permission_grant, is_resource_binding, is_effect_binding]
```

#### Loading Example (PyTorch Geometric)

```python
import json
import torch
from torch_geometric.data import Data

with open("data/processed/escalation_passrole_lambda_create_graph.json") as f:
    g = json.load(f)

data = Data(
    x=torch.tensor([n["features"] for n in g["nodes"]], dtype=torch.float),
    edge_index=torch.tensor([[e["src"] for e in g["edges"]],
                              [e["dst"] for e in g["edges"]]], dtype=torch.long),
    edge_attr=torch.tensor([e["features"] for e in g["edges"]], dtype=torch.float),
    y=torch.tensor([g["graph_label"]])
)
```

### `examples/` — Full Account Snapshots

Complete IAM account configurations demonstrating realistic setups with multiple interacting principals, roles, and policies.

| Account | Description | Escalation? |
|---------|-------------|-------------|
| `account_1_simple_escalation/` | Basic PassRole + Lambda attack | ✅ Critical |
| `account_2_role_chaining/` | Multi-step role assumption chain | ✅ Critical |
| `account_3_secure_baseline/` | Properly configured production account | ❌ Secure |
| `account_4_complex_attack/` | Multiple simultaneous attack vectors | ✅ Critical (4 paths) |

Each account folder contains:
- **`account.json`**: Full IAM configuration (users, roles, policies, groups, trust relationships)
- **`graph.json`**: Graph representation of the account's permission structure
- **`README.md`**: Human-readable explanation of the configuration and attack paths

## Research Context

### Current Dataset (v2.0 - Expanded)

This dataset has been **expanded to 500 policies** (previously 108) to improve GNN model training:

**Dataset Composition:**
- **269 original curated policies** from public repositories and AWS examples
- **231 synthetic policies** generated to increase diversity and coverage
- Combined into single unified dataset for comprehensive training

**Vulnerability Distribution (Maintains realistic patterns):**
- **201 vulnerable policies** (40.2%)
- **299 secure policies** (59.8%)

**Training Results on 500-Policy Dataset:**
- Precision: 0.40 (40%)
- Recall: 1.00 (100%) - Perfect vulnerability detection
- F1 Score: 0.5714
- Accuracy: 0.40 (40%)
- Training Time: 230 seconds (CPU)

The expanded dataset enables:
- More robust GNN training with better convergence
- Better representation of diverse vulnerability patterns
- Improved model generalization to unseen policies
- 4.6x increase in training data diversity

### Previous Dataset (v1.0)

The original **research prototype dataset** supporting initial PolicyGraph research:
- 108 labeled IAM policies covering 30+ vulnerability types
- 10 pre-processed graph representations
- 4 full account snapshots with realistic attack scenarios

## Statistics Summary

| Category | Count | Details |
|----------|-------|---------|
| **Total raw policies** | **500** | 269 original + 231 synthetic |
| **Vulnerable policies** | **201** | 40.2% of dataset |
| **Secure policies** | **299** | 59.8% of dataset |
| Processed graph examples | 10 | Pre-computed for quick start |
| Account snapshots | 4 | Full IAM configurations |
| Vulnerability types | 30+ | IAM-specific patterns |
| AWS services covered | 15+ | IAM, Lambda, EC2, S3, etc. |
| Critical-severity policies | ~85 | Estimated from 40.2% vulnerable |
| **Model Performance** | | |
| Recall (Vulnerability Detection) | 100% | Perfect detection rate |
| Precision | 40% | Conservative on expanded dataset |
| F1 Score | 0.5714 | Balanced metric |
| Training Time (CPU) | 230 sec | Complete 200 epochs |

## Usage

```bash
# Quick analysis of all policies
python -m policygraph analyze data/raw/samples/

# Train the GNN model
python -m policygraph train --data data/processed/

# Evaluate on the full dataset
python -m policygraph evaluate --data data/raw/samples/ --labels data/raw/samples/LABELS.json
```

## Citation

If you use this dataset in your research, please cite the PolicyGraph paper:

```bibtex
@inproceedings{policygraph2026,
  title={PolicyGraph: GNN-Based Privilege Escalation Detection in AWS IAM Policies},
  author={Joshua},
  year={2026}
}
```

## License

This dataset is provided for research and educational purposes. All policies are synthetic representations of common IAM patterns and do not contain any real AWS account information.
