# Account Snapshot Examples

This directory contains complete AWS IAM account configurations demonstrating realistic permission setups with multiple interacting principals, roles, policies, and trust relationships.

## Accounts

| Account | Scenario | Escalation Paths |
|---------|----------|------------------|
| [`account_1_simple_escalation/`](account_1_simple_escalation/) | PassRole + Lambda | 1 (Critical) |
| [`account_2_role_chaining/`](account_2_role_chaining/) | Multi-hop role chain | 1 (Critical) |
| [`account_3_secure_baseline/`](account_3_secure_baseline/) | Properly configured prod | 0 (Secure) |
| [`account_4_complex_attack/`](account_4_complex_attack/) | Multiple attack vectors | 4 (Critical) |

## Structure

Each account folder contains:

- **`account.json`** — Full IAM configuration (users, roles, policies, groups, trust relationships, attack paths)
- **`graph.json`** — Graph representation compatible with PolicyGraph's GNN pipeline
- **`README.md`** — Human-readable explanation of the setup and any attack paths

## Purpose

These examples demonstrate how PolicyGraph analyzes **complete account configurations** rather than individual policies in isolation. This is crucial because:

1. Many escalation paths span multiple policies and roles
2. Trust relationships create transitive access paths
3. Group memberships compound permissions
4. The GNN model needs multi-entity graph structures for accurate detection

## Usage

```python
import json

# Load an account
with open("data/examples/account_1_simple_escalation/account.json") as f:
    account = json.load(f)

# Examine attack paths
for path in account["attack_paths"]:
    print(f"Attack: {path['name']} ({path['severity']})")
    for step in path['steps']:
        print(f"  → {step}")
```
