# PolicyGraph — Data Directory

## Overview

This directory contains the complete dataset for PolicyGraph, organized into three main subdirectories representing different stages of the data pipeline: raw policy samples, processed graph representations, and full account examples.

```
data/
├── README.md                  ← This file
├── raw/                       ← Raw IAM policy JSON files and labels
│   ├── policies_labeled.csv   ← Master label file (CSV format)
│   └── samples/               ← 108 individual IAM policy files
│       ├── README.md          ← Detailed sample documentation
│       ├── LABELS.json        ← Ground-truth labels (JSON format)
│       ├── escalation_*.json  ← Privilege escalation patterns
│       ├── secure_*.json      ← Secure baseline policies
│       ├── lambda_*.json      ← Lambda policies
│       ├── cloudformation_*.json
│       ├── sts_*.json
│       ├── iam_*.json
│       ├── ec2_*.json
│       ├── s3_*.json
│       ├── dynamodb_*.json
│       ├── aws_*.json
│       └── rds_*.json
├── processed/                 ← Graph representations (GNN-ready)
│   ├── *_graph.json           ← 10 example graph files
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
│  (108 JSON)  │     │  (node/edge   │     │  Training &      │
│              │     │   features)   │     │  Inference        │
└──────────────┘     └───────────────┘     └──────────────────┘
       │                                           │
       ▼                                           ▼
┌──────────────┐                          ┌──────────────────┐
│ LABELS.json  │                          │  Predictions:    │
│ labels.csv   │                          │  vulnerable /    │
│ (ground      │                          │  secure +        │
│  truth)      │                          │  attack paths    │
└──────────────┘                          └──────────────────┘
```

## Directory Details

### `raw/` — Raw IAM Policies

Contains the original IAM policy JSON files exactly as they would appear in an AWS account.

- **108 policies** total (41 vulnerable, 67 secure)
- **`samples/`**: Individual policy files organized by service category
- **`samples/LABELS.json`**: Machine-readable ground-truth labels with attack paths, risk scores, remediation guidance, and severity ratings
- **`policies_labeled.csv`**: Tabular label file with columns: `filename`, `label`, `vulnerability_type`, `severity`, `risk_patterns`, `escalation_path`, `attack_path`, `risk_score`, `remediation`, `affected_services`, `secure_alternative`

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

### Current Dataset (v1.0)

This is the **research prototype dataset** supporting the PolicyGraph paper. It demonstrates the feasibility of GNN-based IAM security analysis with:
- 108 labeled IAM policies covering 30+ vulnerability types
- 10 pre-processed graph representations
- 4 full account snapshots with realistic attack scenarios

### Planned: IAMVuln-500 (Future Work)

The expanded dataset (planned for future release) will include:
- 500+ policies with more diverse vulnerability patterns
- Multi-policy interaction analysis
- Cross-account and organization-level policies
- Service-linked role abuse patterns
- Real-world anonymized configurations (with permission)

## Statistics Summary

| Category | Count |
|----------|-------|
| Total raw policies | 108 |
| Vulnerable policies | 41 (38.0%) |
| Secure policies | 67 (62.0%) |
| Processed graph examples | 10 |
| Account snapshots | 4 |
| Vulnerability types | 30+ |
| AWS services covered | 15+ |
| Critical-severity policies | 18 |
| High-severity policies | 13 |

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
