# Account 2: Role Chaining Escalation

## Overview
This example demonstrates a multi-step privilege escalation through role chaining — where an attacker assumes roles sequentially, each granting access to the next, until reaching administrator privileges.

## Account Structure
- **User**: `ci-deploy` — CI/CD service account
- **Role 1**: `DeployRole` — trusted by `ci-deploy`, can assume `OpsRole`
- **Role 2**: `OpsRole` — trusted by `DeployRole`, can assume `AdminRole`
- **Role 3**: `AdminRole` — trusted by `OpsRole`, has `AdministratorAccess`

## Attack Path (3-Hop Chain)
1. `ci-deploy` assumes `DeployRole` (direct trust relationship)
2. `DeployRole` assumes `OpsRole` (inline policy grants access)
3. `OpsRole` assumes `AdminRole` (inline policy grants access)
4. `AdminRole` has `AdministratorAccess` — full account compromise

## Why This Is Dangerous
- Each individual role appears limited in isolation
- The escalation path is only visible when analyzing the full trust chain
- Traditional static analysis tools miss multi-hop paths
- PolicyGraph's GNN approach can detect these transitive relationships

## Remediation
- Remove unnecessary role chaining permissions
- Add conditions (e.g., `aws:PrincipalTag`, MFA) on sensitive role trust policies
- Implement maximum session duration limits
- Use AWS IAM Access Analyzer to detect cross-role access paths
