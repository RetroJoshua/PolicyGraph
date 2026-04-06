# PolicyGraph — IAM Policy Sample Collection

## Overview

This directory contains **108 curated AWS IAM policy samples** used as the training and evaluation dataset for PolicyGraph, a GNN-based privilege escalation detection system. Each policy is a standalone JSON file representing a real-world IAM configuration pattern.

The dataset is designed to support research in automated IAM security analysis using Graph Neural Networks (specifically Graph Attention Networks). It covers the most common privilege escalation techniques documented by [Rhino Security Labs](https://rhinosecuritylabs.com/aws/aws-privilege-escalation-methods-mitigation/) and AWS security best practices.

## Dataset Statistics

| Metric | Count |
|--------|-------|
| **Total Policies** | 108 |
| **Vulnerable** | 41 (38.0%) |
| **Secure** | 67 (62.0%) |
| **Critical Severity** | 18 |
| **High Severity** | 13 |
| **Medium Severity** | 12 |
| **Low Severity** | 65 |

### Services Covered

| Service Category | Policy Count |
|-----------------|-------------|
| IAM Escalation (`escalation_*`) | 21 |
| AWS Managed/Service (`aws_*`) | 17 |
| Secure Baselines (`secure_*`) | 15 |
| Lambda | 12 |
| CloudFormation | 10 |
| STS | 10 |
| IAM General | 9 |
| EC2 | 6 |
| S3 | 4 |
| DynamoDB | 3 |
| RDS | 1 |

## File Naming Conventions

Policy files follow a structured naming pattern:

```
<category>_<specifics>.json
```

### Category Prefixes

| Prefix | Description | Example |
|--------|-------------|---------|
| `escalation_` | Known privilege escalation patterns | `escalation_passrole_lambda_create.json` |
| `secure_` | Security best-practice policies | `secure_mfa_required.json` |
| `lambda_` | AWS Lambda-related policies | `lambda_full_access.json` |
| `cloudformation_` | CloudFormation policies | `cloudformation_create_with_passrole.json` |
| `sts_` | STS/role assumption policies | `sts_assume_role_wildcard.json` |
| `iam_` | IAM management policies | `iam_read_only_access.json` |
| `ec2_` | EC2 compute policies | `ec2_write_subnet-launch.json` |
| `s3_` | S3 storage policies | `s3_readwrite_bucket-objects.json` |
| `dynamodb_` | DynamoDB policies | `dynamodb_readwrite_table-specific.json` |
| `aws_` | AWS managed/service policies | `aws_config_service_role_policy.json` |
| `rds_` | RDS database policies | `rds_admin_region-specific.json` |

### Access Level Indicators

- `_read_` / `_read_only` — Read-only permissions
- `_write_` / `_readwrite_` — Write or read-write permissions
- `_admin_` / `_full_access` — Administrative or full-service access
- `_passrole_` — Contains `iam:PassRole` (potential escalation vector)

## Vulnerability Categories

### Privilege Escalation Patterns (21 policies)

These represent the core IAM escalation techniques:

- **PassRole Escalation** (8): Combining `iam:PassRole` with service creation (Lambda, EC2, CloudFormation, CodeBuild, Glue, SageMaker, DataPipeline)
- **Policy Manipulation** (6): `AttachUserPolicy`, `AttachGroupPolicy`, `AttachRolePolicy`, `PutUserPolicy`, `PutGroupPolicy`, `PutRolePolicy`
- **Policy Version Control** (2): `CreatePolicyVersion`, `SetDefaultPolicyVersion`
- **Credential Theft** (2): `CreateAccessKey`, `CreateLoginProfile`
- **Trust Manipulation** (1): `UpdateAssumeRolePolicy`
- **Group Escalation** (1): `AddUserToGroup`
- **Login Hijacking** (1): `UpdateLoginProfile`

### Secure Baselines (15 policies)

Demonstrate proper IAM configurations:
- MFA enforcement, IP restrictions, time-based access
- Read-only patterns, resource-scoped permissions
- Encryption enforcement, tag-based access control (ABAC)
- SSL/TLS requirements, deny patterns

## Ground-Truth Labels

Each policy has corresponding ground-truth labels in `LABELS.json` (this directory) and `../policies_labeled.csv`. Labels include:

- **label**: `vulnerable` or `secure`
- **severity**: `critical`, `high`, `medium`, or `low`
- **vulnerability_type**: Specific escalation technique
- **risk_score**: 0–10 numerical score
- **attack_path**: Step-by-step exploitation description
- **remediation**: How to fix the vulnerability
- **affected_services**: AWS services involved
- **secure_alternative**: Reference to a secure version (if applicable)

## Using These Samples with PolicyGraph

### Quick Start

```python
import json
from pathlib import Path

# Load a policy
policy_path = Path("data/raw/samples/escalation_passrole_lambda_create.json")
policy = json.loads(policy_path.read_text())

# Load labels
labels = json.loads(Path("data/raw/samples/LABELS.json").read_text())

# Find label for this policy
policy_label = next(
    l for l in labels["labels"]
    if l["filename"] == policy_path.name
)

print(f"Label: {policy_label['label']}")
print(f"Severity: {policy_label['severity']}")
print(f"Risk Score: {policy_label['risk_score']}")
print(f"Attack Path: {policy_label['attack_path']}")
```

### With PolicyGraph Pipeline

```python
from policygraph import PolicyGraph

# Initialize PolicyGraph
pg = PolicyGraph()

# Analyze a single policy
result = pg.analyze("data/raw/samples/escalation_passrole_lambda_create.json")
print(f"Prediction: {result.label}")
print(f"Confidence: {result.confidence:.2%}")

# Batch analysis
results = pg.analyze_directory("data/raw/samples/")
for r in results:
    if r.label == "vulnerable":
        print(f"⚠️  {r.filename}: {r.vulnerability_type} ({r.severity})")
```

### Loading for GNN Training

```python
import json
import torch
from torch_geometric.data import Data

# Load a processed graph
with open("data/processed/escalation_passrole_lambda_create_graph.json") as f:
    graph = json.load(f)

# Convert to PyTorch Geometric format
node_features = torch.tensor([n["features"] for n in graph["nodes"]], dtype=torch.float)
edge_index = torch.tensor(
    [[e["src"] for e in graph["edges"]], [e["dst"] for e in graph["edges"]]],
    dtype=torch.long
)
edge_features = torch.tensor([e["features"] for e in graph["edges"]], dtype=torch.float)

data = Data(
    x=node_features,
    edge_index=edge_index,
    edge_attr=edge_features,
    y=torch.tensor([graph["graph_label"]])
)
```

## Connection to Research

This dataset supports the PolicyGraph research paper on GNN-based IAM privilege escalation detection. Key contributions:

1. **Novel Graph Representation**: IAM policies are modeled as heterogeneous graphs with principal, action, resource, condition, and effect nodes
2. **Graph Attention Networks**: GAT architecture learns to weight different permission relationships
3. **Attack Path Detection**: The model identifies multi-step escalation paths, not just individual policy violations
4. **Benchmark Dataset**: These 108 policies serve as the initial benchmark for future IAM security research

### Relationship to IAMVuln-500

This 108-policy dataset is the research prototype. The planned **IAMVuln-500** dataset (future work) will expand to 500+ policies with:
- Multi-policy interaction analysis
- Cross-account escalation patterns
- Service-linked role abuse
- Organization-level policy evaluation

## Directory Structure

```
data/raw/samples/
├── README.md              ← This file
├── LABELS.json            ← Ground-truth labels with attack paths
├── vulnerable/            ← Legacy subfolder (5 duplicate policies)
├── escalation_*.json      ← Privilege escalation patterns (21 files)
├── secure_*.json          ← Secure baseline policies (15 files)
├── lambda_*.json          ← Lambda service policies (12 files)
├── cloudformation_*.json  ← CloudFormation policies (10 files)
├── sts_*.json             ← STS/role assumption policies (10 files)
├── iam_*.json             ← IAM management policies (9 files)
├── ec2_*.json             ← EC2 compute policies (6 files)
├── s3_*.json              ← S3 storage policies (4 files)
├── dynamodb_*.json        ← DynamoDB policies (3 files)
├── aws_*.json             ← AWS managed/service policies (17 files)
└── rds_*.json             ← RDS database policies (1 file)
```

## License

This dataset is provided for research and educational purposes. All policies are synthetic representations of common IAM patterns and do not contain any real AWS account information.
