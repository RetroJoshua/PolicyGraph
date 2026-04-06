# Processed Graph Representations

This directory contains pre-computed graph representations of IAM policies, formatted for direct use with Graph Neural Network frameworks.

## Format

Each `*_graph.json` file contains:

- **nodes**: Typed graph nodes with 6-dimensional feature vectors
- **edges**: Typed edges with 3-dimensional feature vectors
- **metadata**: Source policy info, labels, and compatibility notes
- **adjacency_list**: Dictionary for quick graph traversal
- **graph_label**: Binary classification target (1 = vulnerable, 0 = secure)

## Files

| File | Label | Severity | Risk Score |
|------|-------|----------|------------|
| `escalation_passrole_lambda_create_graph.json` | Vulnerable | Critical | 10 |
| `escalation_attach_user_policy_graph.json` | Vulnerable | Critical | 10 |
| `escalation_create_policy_version_graph.json` | Vulnerable | Critical | 10 |
| `escalation_passrole_ec2_run_graph.json` | Vulnerable | Critical | 10 |
| `cloudformation_create_with_passrole_graph.json` | Vulnerable | Critical | 9 |
| `sts_assume_role_wildcard_graph.json` | Vulnerable | High | 8 |
| `sts_assume_role_chaining_graph.json` | Vulnerable | High | 8 |
| `secure_s3_least_privilege_graph.json` | Secure | Low | 0 |
| `secure_mfa_required_graph.json` | Secure | Low | 0 |
| `secure_ec2_read_only_graph.json` | Secure | Low | 0 |

## Framework Compatibility

All graphs are compatible with:
- **DGL** (Deep Graph Library)
- **PyTorch Geometric**
- **NetworkX**

See the main [`data/README.md`](../README.md) for loading examples.
