## PolicyGraph Usage Examples

This guide demonstrates common usage patterns for PolicyGraph.

### 1. Analyzing a Single Policy

```python
from policygraph import PolicyAnalyzer

# Initialize analyzer with a trained model
analyzer = PolicyAnalyzer(model_path="path/to/model.pt", threshold=0.3)

# Analyze a policy from file
result = analyzer.analyze_policy("path/to/policy.json")

# Or from a Python dictionary
policy_dict = {
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": "*"
        }
    ]
}
result = analyzer.analyze_policy(policy_dict)

# Access results
print(f"Risk Score: {result['risk_score']:.2%}")
print(f"Prediction: {result['prediction_label']}")
print(f"Vulnerabilities: {result['vulnerabilities_detected']}")
for path in result['attack_paths']:
    print(f"  - {path['description']}")
```

### 2. Batch Analysis of Multiple Policies

```python
from policygraph import PolicyAnalyzer
from pathlib import Path

analyzer = PolicyAnalyzer(model_path="path/to/model.pt")
policy_dir = Path("data/raw/samples")

# Analyze all JSON files in a directory
results = analyzer.analyze_batch(policy_dir.glob("*.json"))

# Process results
for result in results:
    if result['prediction'] == 1:  # Vulnerable
        print(f"Found vulnerability in {result['policy_file']}")
        print(f"  Risk Score: {result['risk_score']:.3f}")
        print(f"  Severity: {result.get('severity', 'unknown')}")
```

### 3. Loading and Exploring the Dataset

```python
from policygraph import PolicyDataset

# Load the curated 108-policy dataset
dataset = PolicyDataset(data_dir="data/raw/samples")

# Access metadata
print(f"Total policies: {len(dataset.samples)}")
print(f"Vulnerable: {sum(s.label for s in dataset.samples)}")
print(f"Secure: {len(dataset.samples) - sum(s.label for s in dataset.samples)}")

# Get train/val/test splits
train_indices = dataset.train_indices
val_indices = dataset.val_indices
test_indices = dataset.test_indices

# Iterate over samples
for sample in dataset.samples[:5]:
    print(f"File: {sample.filename}")
    print(f"Label: {sample.label_text}")
    print(f"Risk Score: {sample.risk_score}")
    print(f"Vulnerability Type: {sample.vulnerability_type}")
    print()
```

### 4. Building Graphs from Policies

```python
from policygraph import IAMGraphBuilder

builder = IAMGraphBuilder()

policy = {
    "Statement": [
        {
            "Effect": "Allow",
            "Action": ["iam:PassRole", "lambda:CreateFunction"],
            "Resource": "*"
        }
    ]
}

# Build graph representation
graph_result = builder.build_graph_from_policy(policy)
graph = graph_result.graph

print(f"Nodes: {graph.num_nodes()}")
print(f"Edges: {graph.num_edges()}")
print(f"Node features shape: {graph_result.node_features.shape}")
```

### 5. Custom Model Inference

```python
import torch
from policygraph import GATPolicyRiskModel, IAMGraphBuilder

# Initialize model and builder
model = GATPolicyRiskModel(
    in_dim=6,
    hidden_dim=64,
    num_layers=3,
    num_heads=4
)
model.eval()

# Load checkpoint
checkpoint = torch.load("path/to/checkpoint.pt")
model.load_state_dict(checkpoint["model_state_dict"])

# Build graph and run inference
builder = IAMGraphBuilder()
policy = {...}
graph_result = builder.build_graph_from_policy(policy)
graph = graph_result.graph

with torch.no_grad():
    output = model(graph, return_attention=True)
    risk_score = output["risk_score"].item()
    
print(f"Risk Score: {risk_score:.3f}")
if "attentions" in output:
    print(f"Attention weights shape: {output['attentions'].shape}")
```

### 6. Using the CLI Interface

```bash
# Analyze a single policy
policygraph analyze data/raw/samples/policy_001.json

# Analyze all policies in a directory
policygraph batch data/raw/samples

# Train a new model
policygraph train --config config.yaml

# Evaluate a trained model
policygraph evaluate --config config.yaml --model checkpoints/best_model.pt
```

### 7. Error Handling with Custom Exceptions

```python
from policygraph import PolicyAnalyzer, PolicyParsingError, ModelLoadingError

analyzer = PolicyAnalyzer(threshold=0.3)

try:
    result = analyzer.analyze_policy("invalid_policy.json")
except PolicyParsingError as e:
    print(f"Failed to parse policy: {e}")
except ModelLoadingError as e:
    print(f"Failed to load model: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 8. Training a Custom Model

```python
from policygraph import PolicyDataset
from policygraph.pipeline import run_training
from policygraph.utils import load_config

# Load configuration
config = load_config("config.yaml")

# Train model with early stopping
best_model_path = run_training(config)
print(f"Best model saved to: {best_model_path}")

# Evaluate on test set
from policygraph.pipeline import run_evaluation
run_evaluation(config=config, model_path=best_model_path)
```

### 9. Analyzing Entire AWS Accounts

```python
from policygraph import PolicyAnalyzer

analyzer = PolicyAnalyzer(model_path="path/to/model.pt")

# Load all policies from an account structure
account_policies = [...]  # Load from boto3, CloudFormation, etc.

results = analyzer.analyze_batch(account_policies)

# Aggregate findings
vulnerabilities = [r for r in results if r['prediction'] == 1]
high_risk = [r for r in vulnerabilities if r['risk_score'] > 0.7]

print(f"Total vulnerabilities found: {len(vulnerabilities)}")
print(f"High risk (>0.7): {len(high_risk)}")

# Export report
import json
with open("account_analysis_report.json", "w") as f:
    json.dump({
        "summary": {
            "total_policies": len(results),
            "vulnerable": len(vulnerabilities),
            "high_risk": len(high_risk)
        },
        "findings": vulnerabilities
    }, f, indent=2)
```

### 10. Logging and Debugging

```python
import logging
from policygraph import PolicyAnalyzer

# Enable detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("policygraph")
logger.setLevel(logging.DEBUG)

# Run analysis with detailed output
analyzer = PolicyAnalyzer(model_path="path/to/model.pt")
result = analyzer.analyze_policy("policy.json")
# Logs will show detailed information about each step
```

### 11. Comparing Predictions

```python
from policygraph import PolicyAnalyzer

analyzer = PolicyAnalyzer(threshold=0.3)

policy = {...}
result = analyzer.analyze_policy(policy)

# Compare neural vs heuristic signals
neural_score = result['model_risk_score']
heuristic_score = result['heuristic_risk_score']
blended_score = result['risk_score']

print(f"Neural Score:      {neural_score:.3f}")
print(f"Heuristic Score:   {heuristic_score:.3f}")
print(f"Blended Score:     {blended_score:.3f}")

# Heuristic-heavy when neural signal is uncertain
```

### 12. Reproducible Results

```python
import random
import numpy as np
import torch
from policygraph import PolicyDataset

# Set seeds for reproducibility
seed = 42
random.seed(seed)
np.random.seed(seed)
torch.manual_seed(seed)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(seed)

# Load dataset with same seed
dataset = PolicyDataset(split_seed=seed)
# Results are now reproducible across runs
```
