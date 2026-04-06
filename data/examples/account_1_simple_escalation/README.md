# Account 1: Simple PassRole + Lambda Escalation

## Overview
This example demonstrates the most common IAM privilege escalation pattern: using `iam:PassRole` combined with `lambda:CreateFunction` to execute code with administrator privileges.

## Account Structure
- **User**: `dev-user` — a developer with Lambda deployment permissions
- **Role**: `AdminLambdaExecutionRole` — Lambda execution role with `AdministratorAccess`
- **Policy**: `DevLambdaPolicy` — allows PassRole (wildcard) + Lambda create/invoke

## Attack Path
1. `dev-user` creates a Lambda function with a malicious handler
2. Passes `AdminLambdaExecutionRole` as the execution role
3. Invokes the function
4. The function runs with **full admin privileges**
5. From within the Lambda, the attacker can create new admin users, exfiltrate data, or modify any resource

## Why This Is Dangerous
- `iam:PassRole` on `*` allows passing **any** role, including admin roles
- The Lambda service trusts the execution role, so the function inherits full admin permissions
- This is one of the most exploited IAM escalation vectors in real-world attacks

## Remediation
- Restrict `iam:PassRole` to specific, non-admin role ARNs
- Use `iam:PassedToService` condition to limit which services can receive roles
- Implement permission boundaries on the execution role
- Monitor Lambda function creation with CloudTrail

## Graph Representation
See `graph.json` for the full graph structure compatible with PolicyGraph's GNN pipeline.
