# Account 3: Secure Baseline

## Overview
This example demonstrates a properly configured production AWS account following security best practices. **PolicyGraph detects no privilege escalation paths in this configuration.**

## Security Controls
- **MFA Enforcement**: All users require multi-factor authentication
- **Permission Boundaries**: Lambda execution roles are bounded
- **Least Privilege**: Specific actions on specific resources (no wildcards)
- **Region Scoping**: Permissions restricted to `us-east-1`
- **Conditional PassRole**: `iam:PassRole` restricted to specific role ARN and service
- **Group-Based Access**: Permissions managed through groups, not direct user policies

## Account Structure
- **Users**: `prod-readonly` (read-only) and `prod-deployer` (deploy Lambda code)
- **Role**: `LambdaExecutionRole` — minimal permissions with boundary
- **Groups**: `ReadOnlyTeam` and `Deployers` — separation of duties

## Why This Is Secure
1. `iam:PassRole` is restricted to a single, non-admin role
2. PassRole requires the `iam:PassedToService` condition
3. Lambda updates require MFA
4. Lambda execution role has minimal permissions (logs + single DynamoDB table)
5. No wildcard resources anywhere
6. Permission boundary prevents the Lambda role from escalating

## Use as Reference
This account serves as a secure baseline for comparison with vulnerable configurations.
