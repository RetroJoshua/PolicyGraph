# PolicyGraph — Policy Addition Summary

**Date:** March 30, 2026  
**Repository:** https://github.com/RetroJoshua/PolicyGraph

---

### Overview

Added **66 new IAM policy JSON files** to the `data/raw/samples/` directory, bringing the total from **42 existing** (41 flat + 1 in vulnerable/) to **108 labeled policies**.

A new `data/raw/policies_labeled.csv` file was created with labels for all 108 policies.

---

### New Policies by Category

| Category | Count | Description |
|----------|-------|-------------|
| **A. STS Policies** | 10 | AssumeRole variants, session tokens, federation, role chaining |
| **B. CloudFormation Policies** | 10 | Full access, PassRole combos, read-only, stack-specific, StackSets |
| **C. Escalation Policies** | 21 | All 21 Rhino Security Labs privilege escalation methods |
| **D. Secure Baseline Policies** | 15 | Least-privilege, read-only, MFA, IP/time restrictions, encryption |
| **E. Lambda + PassRole Combos** | 10 | Lambda create/update with PassRole, execution roles, read-only |
| **Total New** | **66** | |

---

### Distribution by Label

| Label | Count | Percentage |
|-------|-------|------------|
| **Secure** | 67 | 62.0% |
| **Vulnerable** | 41 | 38.0% |
| **Total** | **108** | 100% |

---

### Distribution by Severity

| Severity | Count | Percentage |
|----------|-------|------------|
| **Critical** | 18 | 16.7% |
| **High** | 13 | 12.0% |
| **Medium** | 12 | 11.1% |
| **Low** | 65 | 60.2% |
| **Total** | **108** | 100% |

---

### Vulnerability Types Covered

- **IAM Policy Manipulation:** AttachUserPolicy, AttachGroupPolicy, AttachRolePolicy, PutUserPolicy, PutGroupPolicy, PutRolePolicy
- **Credential Theft:** CreateAccessKey, CreateLoginProfile, UpdateLoginProfile
- **Role Assumption:** AssumeRole wildcard, role chaining, cross-account
- **PassRole Exploitation:** Lambda, EC2, CloudFormation, Glue, DataPipeline, SageMaker, CodeBuild
- **Policy Version Manipulation:** CreatePolicyVersion, SetDefaultPolicyVersion
- **Group Membership:** AddUserToGroup
- **Trust Policy Modification:** UpdateAssumeRolePolicy
- **Full Service Access:** IAM, Lambda, CloudFormation

---

### Files Modified/Created

1. **66 new JSON files** in `data/raw/samples/`
2. **`data/raw/policies_labeled.csv`** — 108 entries with columns: filename, label, vulnerability_type, severity, risk_patterns, escalation_path
3. **`.gitignore`** — standard Python/project ignores

---

### How to Commit & Push

```bash
cd /home/ubuntu/github_repos/PolicyGraph

# Review changes
git status
git diff --stat

# Stage all new files
git add data/raw/samples/*.json
git add data/raw/policies_labeled.csv
git add .gitignore

# Commit
git commit -m "Add 66 new IAM policies (108 total) with labeled CSV

- 10 STS policies (AssumeRole variants, session tokens, role chaining)
- 10 CloudFormation policies (full access, PassRole, read-only)
- 21 Rhino Security Labs escalation policies (all known priv-esc vectors)
- 15 Secure baseline policies (least privilege, MFA, encryption, ABAC)
- 10 Lambda + PassRole combination policies
- Updated policies_labeled.csv with all 108 entries"

# Push
git push origin main
```

---

### Notes

- The `data/raw/samples/vulnerable/` subfolder still contains 5 legacy files that are now duplicated in the flat `samples/` directory. Consider removing the subfolder for consistency.
- All JSON files follow valid AWS IAM policy structure with `Version` and `Statement` fields.
- The CSV includes escalation paths for vulnerable policies, useful for GNN training labels.
