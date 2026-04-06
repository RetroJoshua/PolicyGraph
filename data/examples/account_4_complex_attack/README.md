# Account 4: Complex Multi-Vector Attack

## Overview
This example demonstrates a realistic enterprise account with **multiple simultaneous privilege escalation vectors** across different users and services. PolicyGraph's GNN pipeline is specifically designed to detect these complex, interconnected attack paths.

## Account Structure
- **User 1**: `analyst` — data team member with Glue and Data Pipeline access
- **User 2**: `developer` — dev team member with IAM and Lambda permissions
- **Roles**: `DataPipelineRole` (admin), `GlueRole`, `CrossAccountRole` (admin)

## Attack Vectors (4 Independent Paths)

### Vector 1: Analyst → Glue Dev Endpoint (High)
`analyst` → PassRole(*) → DataPipelineRole(admin) → Glue endpoint with admin execution

### Vector 2: Analyst → Data Pipeline (Critical)
`analyst` → PassRole(*) → DataPipelineRole(admin) → Pipeline activities with admin execution

### Vector 3: Developer → Policy Version (Critical)
`developer` → CreatePolicyVersion → Modify any policy to grant admin → Immediate escalation

### Vector 4: Developer → Attach Policy (Critical)
`developer` → AttachUserPolicy → Attach AdministratorAccess to self → Immediate admin

## Why This Is Important
- **Multiple attack surfaces**: Even if one vector is mitigated, others remain
- **Cross-team risk**: Different teams contribute different vulnerabilities
- **Transitive risk**: The CrossAccountRole creates risk of lateral movement to account 555555555555
- **Real-world pattern**: This mirrors common enterprise misconfigurations

## Remediation Priority
1. **Immediate**: Remove `iam:AttachUserPolicy` and `iam:CreatePolicyVersion` from developer
2. **High**: Restrict `iam:PassRole` to specific non-admin roles for analyst
3. **Medium**: Replace admin roles on DataPipelineRole with least-privilege
4. **Low**: Review CrossAccountRole trust and add ExternalId condition
