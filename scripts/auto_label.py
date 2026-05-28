"""
auto_label.py — Automatically label obviously secure or obviously vulnerable policies.

Leaves genuinely ambiguous cases unlabeled for manual review.

Usage:
    python scripts/auto_label.py --scraped data/scraped_policies \
                                  --out data/labeled_policies \
                                  --dry-run   # preview without writing
    python scripts/auto_label.py --scraped data/scraped_policies \
                                  --out data/labeled_policies
    
    Then resume manual review for remaining ambiguous cases:
    python scripts/label_scraped_policies.py --scraped data/scraped_policies \
                                              --out data/labeled_policies \
                                              --model checkpoints/best_model.pt \
                                              --review-only
"""

import json
import re
import csv
import shutil
import logging
import argparse
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Rule definitions ──────────────────────────────────────────────────────────

# Actions that are always read-only / harmless
READONLY_PREFIXES = {
    "get", "list", "describe", "view", "head",
    "check", "validate", "preview", "query", "scan",
    "search", "lookup", "fetch", "read",
}

READONLY_ACTIONS = {
    "s3:getobject", "s3:listbucket", "s3:getbucketlocation",
    "s3:getobjectversion", "s3:listbucketmultipartuploads",
    "ec2:describeinstances", "ec2:describesecuritygroups",
    "ec2:describevpcs", "ec2:describesubnets",
    "cloudwatch:getmetricdata", "cloudwatch:listmetrics",
    "logs:createloggroup", "logs:createlogstream", "logs:putlogevents",
    "logs:describeloggroups", "logs:describelogstreams", "logs:getlogevents",
    "ce:getrightsizingrecommendation",
    "sts:assumerole",  # trust policies — only dangerous with wildcard principal
    "xray:gettracesummaries", "xray:batchgettraces",
    "tag:getresources",
    "states:describestatemachine", "states:liststatemachines",
    "autoscaling:describeautoscalinggroups",
    "autoscaling:describeautoscalinginstances",
    "autoscaling:describelaunchconfigurations",
    "autoscaling:describetags",
    "autoscaling:setdesiredcapacity",
    "autoscaling:terminateinstanceinautoscalinggroup",
    "autoscaling:updateautoscalinggroup",
    "ecr:getdownloadurlforlayer", "ecr:batchgetimage",
    "ecr:getauthorizationtoken", "ecr:batchchecklayeravailability",
}

# Service trust principal patterns — safe by themselves
SERVICE_PRINCIPALS = {
    "lambda.amazonaws.com", "ec2.amazonaws.com", "ecs.amazonaws.com",
    "ecs-tasks.amazonaws.com", "eks.amazonaws.com", "glue.amazonaws.com",
    "codebuild.amazonaws.com", "codepipeline.amazonaws.com",
    "cloudformation.amazonaws.com", "states.amazonaws.com",
    "firehose.amazonaws.com", "apigateway.amazonaws.com",
    "s3.amazonaws.com", "sns.amazonaws.com", "sqs.amazonaws.com",
    "events.amazonaws.com", "scheduler.amazonaws.com",
    "delivery.logs.amazonaws.com", "cloudfront.amazonaws.com",
    "dlm.amazonaws.com", "backup.amazonaws.com",
    "monitoring.rds.amazonaws.com", "rds.amazonaws.com",
    "elasticmapreduce.amazonaws.com",
}

# Actions that enable privilege escalation
ESCALATION_ACTIONS = {
    "iam:passrole",
    "iam:createpolicy", "iam:createpolicyversion", "iam:setdefaultpolicyversion",
    "iam:attachrolepolicy", "iam:attachuserpolicy", "iam:attachgrouppolicy",
    "iam:putrolepolicy", "iam:putuserpolicy", "iam:putgrouppolicy",
    "iam:createrole", "iam:createuser",
    "iam:addusertogroup",
    "sts:assumerole",  # dangerous when resource is "*" and principal is not a service
}

PRIVILEGED_SERVICES = {
    "lambda:createfunction", "lambda:updatefunctioncode", "lambda:invokefunction",
    "ec2:runinstances",
    "cloudformation:createstack", "cloudformation:updatestack",
    "glue:createdevendpoint",
    "datapipeline:createpipeline",
    "sagemaker:createnotebookinstance", "sagemaker:createtrainingjob",
}


# ── Policy JSON extractor ─────────────────────────────────────────────────────

def extract_policy_from_file(path: Path) -> dict | None:
    """Extract policy JSON from a policy_*.json file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            if "Statement" in data:
                return data
            if "policy" in data and isinstance(data["policy"], dict):
                return data["policy"]
    except Exception:
        pass
    return None


# ── Rule engine ───────────────────────────────────────────────────────────────

def is_readonly_action(action: str) -> bool:
    a = action.lower().strip()
    if a == "*":
        return False
    parts = a.split(":")
    if len(parts) == 2:
        op = parts[1]
        if any(op.startswith(p) for p in READONLY_PREFIXES):
            return True
    return a in READONLY_ACTIONS


def is_service_trust_only(policy: dict) -> bool:
    """True if this is purely a service assume-role trust policy."""
    statements = policy.get("Statement", [])
    if not statements:
        return False
    for stmt in statements:
        if not isinstance(stmt, dict):
            return False
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        actions_lower = [a.lower() for a in actions]
        # Must only contain sts:AssumeRole
        if not all(a == "sts:assumerole" for a in actions_lower):
            return False
        # Principal must be an AWS service
        principal = stmt.get("Principal", {})
        if isinstance(principal, str):
            if principal == "*":
                return False
        elif isinstance(principal, dict):
            services = principal.get("Service", [])
            if isinstance(services, str):
                services = [services]
            if not services:
                return False
            if not all(s.lower() in SERVICE_PRINCIPALS or
                      s.lower().endswith(".amazonaws.com") for s in services):
                return False
        else:
            return False
    return True


def classify_policy(policy: dict) -> tuple[str, str, str]:
    """
    Returns (label, severity, reason):
      label: "vulnerable" | "secure" | "ambiguous"
      severity: "critical" | "high" | "medium" | "low"
      reason: human-readable explanation
    """
    statements = policy.get("Statement", [])
    if not statements:
        return "secure", "low", "Empty policy"

    # Rule 1: pure service trust policy
    if is_service_trust_only(policy):
        return "secure", "low", "Service trust policy only"

    all_actions: list[str] = []
    has_wildcard_action = False
    has_wildcard_resource = False
    has_escalation_action = False
    has_privileged_service = False
    has_passrole = False
    passrole_resource_wildcard = False
    all_readonly = True

    for stmt in statements:
        if not isinstance(stmt, dict):
            continue
        effect = stmt.get("Effect", "Allow").lower()
        if effect != "allow":
            continue

        actions = stmt.get("Action", [])
        resources = stmt.get("Resource", [])
        if isinstance(actions, str):
            actions = [actions]
        if isinstance(resources, str):
            resources = [resources]

        actions_lower = [a.lower().strip() for a in actions]
        resources_lower = [r.lower().strip() for r in resources]

        all_actions.extend(actions_lower)

        if "*" in actions_lower or "iam:*" in actions_lower:
            has_wildcard_action = True
        if "*" in resources_lower:
            has_wildcard_resource = True

        for a in actions_lower:
            if not is_readonly_action(a) and a != "*":
                all_readonly = False
            if a in ESCALATION_ACTIONS:
                has_escalation_action = True
            if a in PRIVILEGED_SERVICES:
                has_privileged_service = True
            if a == "iam:passrole":
                has_passrole = True
                if "*" in resources_lower:
                    passrole_resource_wildcard = True

    # Rule 2: wildcard action + wildcard resource = critical
    if has_wildcard_action and has_wildcard_resource:
        return "vulnerable", "critical", "Action:* on Resource:* grants full admin"

    # Rule 3: wildcard action on any resource
    if has_wildcard_action:
        return "vulnerable", "high", "Wildcard action grants excessive privileges"

    # Rule 4: PassRole + privileged service creation = escalation
    if has_passrole and has_privileged_service:
        return "vulnerable", "high", "iam:PassRole + privileged service creation enables role abuse"

    # Rule 5: PassRole on wildcard resource
    if passrole_resource_wildcard:
        return "vulnerable", "medium", "iam:PassRole on Resource:* broadens escalation scope"

    # Rule 6: other escalation actions on wildcard
    if has_escalation_action and has_wildcard_resource:
        return "vulnerable", "medium", "IAM escalation action on wildcard resource"

    # Rule 7: purely read-only actions
    if all_readonly:
        return "secure", "low", "Read-only actions only"

    # Rule 8: only s3/logs/monitoring with scoped resources
    non_escalation = [a for a in all_actions if a not in ESCALATION_ACTIONS]
    if non_escalation and not has_escalation_action:
        services = {a.split(":")[0] for a in non_escalation if ":" in a}
        safe_services = {"s3", "logs", "cloudwatch", "ec2", "ecr", "ecs",
                        "autoscaling", "ce", "xray", "tag", "states",
                        "kinesis", "firehose", "sns", "sqs", "secretsmanager",
                        "ssm", "kms", "codecommit", "codebuild", "codepipeline"}
        if services.issubset(safe_services) and not has_wildcard_action:
            return "secure", "low", f"Non-escalation services only: {', '.join(sorted(services))}"

    return "ambiguous", "unknown", "Requires manual review"


# ── Output writers ────────────────────────────────────────────────────────────

def write_outputs(results: list[dict], out_dir: Path, existing_labels: dict) -> None:
    """Merge auto-labels with existing LABELS.json and policies_labeled.csv."""
    out_dir.mkdir(parents=True, exist_ok=True)
    policies_dir = out_dir / "policies"
    policies_dir.mkdir(exist_ok=True)

    # Merge into existing labels
    merged = dict(existing_labels)
    for r in results:
        if r["label"] == "ambiguous":
            continue
        merged[r["filename"]] = {
            "label": r["label"],
            "severity": r["severity"],
            "vulnerability_type": r["vuln_type"],
            "risk_score": 9 if r["severity"] == "critical" else
                          7 if r["severity"] == "high" else
                          5 if r["severity"] == "medium" else 1,
            "source": "auto_label",
            "reason": r["reason"],
            "attack_paths": [],
            "remediation": r["remediation"],
        }
        # Copy policy file
        src = r["source_path"]
        dst = policies_dir / r["filename"]
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)

    # Write LABELS.json in PolicyDataset format
    entries = [{"filename": k, **v} for k, v in merged.items()]
    labels_json = out_dir / "LABELS.json"
    labels_json.write_text(
        json.dumps({"total_policies": len(entries), "labels": entries}, indent=2),
        encoding="utf-8"
    )

    # Write CSV
    csv_path = out_dir / "policies_labeled.csv"
    fieldnames = ["filename", "label", "vulnerability_type", "severity",
                  "risk_score", "source", "reason", "remediation"]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for k, v in merged.items():
            writer.writerow({"filename": k, **v})

    log.info("Wrote %d entries to %s", len(merged), labels_json)
    log.info("Wrote CSV to %s", csv_path)


def infer_remediation(label: str, reason: str) -> str:
    if label == "secure":
        return "N/A — policy follows least-privilege principles."
    if "PassRole" in reason:
        return "Scope iam:PassRole to specific role ARNs. Add iam:PassedToService condition."
    if "wildcard action" in reason.lower() or "Action:*" in reason:
        return "Replace Action:* with explicit required actions."
    if "escalation action" in reason.lower():
        return "Scope IAM actions to specific resource ARNs instead of *."
    return "Review and restrict overly broad permissions."


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Auto-label obvious IAM policies")
    parser.add_argument("--scraped", default="data/scraped_policies")
    parser.add_argument("--out",     default="data/labeled_policies")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print results without writing files")
    args = parser.parse_args()

    scraped_dir = Path(args.scraped)
    out_dir     = Path(args.out)

    # Load existing labels to avoid overwriting manual work
    existing_labels = {}
    existing_labels_path = out_dir / "LABELS.json"
    if existing_labels_path.exists():
        data = json.loads(existing_labels_path.read_text(encoding="utf-8"))
        if "labels" in data:
            existing_labels = {e["filename"]: {k: v for k, v in e.items()
                               if k != "filename"} for e in data["labels"]}
        else:
            existing_labels = data
        log.info("Loaded %d existing labels", len(existing_labels))

    policy_files = sorted(scraped_dir.glob("policy_*.json"))
    log.info("Found %d policy_*.json files to classify", len(policy_files))

    results = []
    counts = {"vulnerable": 0, "secure": 0, "ambiguous": 0, "skipped": 0}

    for path in policy_files:
        # Derive output filename (matches how label_scraped_policies names them)
        out_filename = path.name

        # Skip already manually labeled
        if out_filename in existing_labels:
            source = existing_labels[out_filename].get("source", "")
            if source != "auto_label":
                counts["skipped"] += 1
                continue

        policy = extract_policy_from_file(path)
        if not policy:
            counts["ambiguous"] += 1
            continue

        label, severity, reason = classify_policy(policy)
        remediation = infer_remediation(label, reason)
        vuln_type = (
            "privilege_escalation" if label == "vulnerable" and "PassRole" in reason
            else "excessive_permissions" if label == "vulnerable"
            else "none"
        )

        results.append({
            "filename": out_filename,
            "label": label,
            "severity": severity,
            "reason": reason,
            "vuln_type": vuln_type,
            "remediation": remediation,
            "source_path": path,
        })
        counts[label] += 1

    # Print summary
    print(f"\n{'═'*55}")
    print(f"  AUTO-LABEL RESULTS")
    print(f"{'═'*55}")
    print(f"  Vulnerable  : {counts['vulnerable']}")
    print(f"  Secure      : {counts['secure']}")
    print(f"  Ambiguous   : {counts['ambiguous']} (needs manual review)")
    print(f"  Skipped     : {counts['skipped']} (already manually labeled)")
    print(f"{'═'*55}")

    # Show sample vulnerable findings
    vulns = [r for r in results if r["label"] == "vulnerable"][:5]
    if vulns:
        print("\n  Sample vulnerable findings:")
        for r in vulns:
            print(f"    {r['filename']}: {r['reason']}")

    if args.dry_run:
        print("\n  Dry run — nothing written.")
        return

    if not results:
        log.info("Nothing to write.")
        return

    write_outputs(results, out_dir, existing_labels)
    print(f"\n  Ready for manual review: {counts['ambiguous']} ambiguous policies")
    print(f"  Run: python scripts/label_scraped_policies.py "
          f"--scraped {args.scraped} --out {args.out} --review-only\n")


if __name__ == "__main__":
    main()
