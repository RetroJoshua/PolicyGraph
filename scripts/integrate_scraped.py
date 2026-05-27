#!/usr/bin/env python3
"""
Integrate scraped IAM policies into the PolicyGraph training dataset.

This script:
1. Reads raw .tf blocks from data/scraped_policies/
2. Extracts IAM policy statements (best-effort HCL → JSON)
3. Applies labeling rules (or reads from a manual labels file)
4. Copies labeled policies into data/raw/samples/
5. Updates LABELS.json and policies_labeled.csv

Usage:
    # Step 1: Generate a labeling template (review and edit this!)
    python scripts/integrate_scraped.py --generate-labels

    # Step 2: After manual review, integrate labeled policies
    python scripts/integrate_scraped.py --integrate

    # Or auto-label with heuristics (no manual review, less accurate)
    python scripts/integrate_scraped.py --auto-label --integrate
"""

import csv
import json
import hashlib
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRAPED_DIR = PROJECT_ROOT / "data" / "scraped_policies"
SAMPLES_DIR = PROJECT_ROOT / "data" / "raw" / "samples"
LABELS_FILE = SCRAPED_DIR / "manual_labels.csv"
LABELS_JSON = SAMPLES_DIR / "LABELS.json"
LABELED_CSV = PROJECT_ROOT / "data" / "raw" / "policies_labeled.csv"

# ── Dangerous action patterns for auto-labeling ─────────────────────────────

CRITICAL_PATTERNS = {
    # PassRole + compute service = privilege escalation
    "passrole_lambda": (r"iam:PassRole.*lambda:CreateFunction|lambda:CreateFunction.*iam:PassRole", "critical"),
    "passrole_ec2": (r"iam:PassRole.*ec2:RunInstances|ec2:RunInstances.*iam:PassRole", "critical"),
    "passrole_ecs": (r"iam:PassRole.*ecs:RunTask|ecs:RunTask.*iam:PassRole", "critical"),
    "passrole_glue": (r"iam:PassRole.*glue:CreateDevEndpoint|glue:CreateDevEndpoint.*iam:PassRole", "critical"),
    # Direct IAM admin
    "iam_wildcard": (r'"iam:\*"', "critical"),
    "admin_wildcard": (r'"Action"\s*[=:]\s*"\*".*"Resource"\s*[=:]\s*"\*"', "critical"),
    # Policy manipulation
    "attach_policy": (r"iam:Attach(User|Role|Group)Policy", "high"),
    "put_policy": (r"iam:Put(User|Role)Policy", "high"),
    "create_policy_version": (r"iam:CreatePolicyVersion", "critical"),
    # Role assumption
    "wildcard_assume_role": (r"sts:AssumeRole.*Resource.*\*", "high"),
}

SECURE_INDICATORS = [
    r"Condition",           # Has conditions (usually more restrictive)
    r"iam:PassedToService", # Scoped PassRole
    r"Deny",                # Deny statements
    r"MFA",                 # MFA requirements
]


def auto_label_tf_block(content: str) -> tuple[str, str, str]:
    """
    Auto-label a .tf block based on pattern matching.
    Returns (label, vulnerability_type, severity).
    """
    for vuln_type, (pattern, severity) in CRITICAL_PATTERNS.items():
        if re.search(pattern, content, re.IGNORECASE | re.DOTALL):
            return ("vulnerable", vuln_type, severity)

    # Check for secure indicators
    secure_score = sum(1 for p in SECURE_INDICATORS if re.search(p, content))
    if secure_score >= 2:
        return ("secure", "none", "low")

    # Default: needs manual review
    return ("unknown", "needs_review", "unknown")


def extract_policy_from_tf(content: str) -> dict | None:
    """
    Best-effort extraction of IAM policy JSON from a .tf block.
    """
    # Try to find jsonencode(...) blocks
    json_match = re.search(r'jsonencode\(\s*(\{[\s\S]*?\})\s*\)', content)
    if json_match:
        try:
            # HCL-style JSON → standard JSON (rough conversion)
            raw = json_match.group(1)
            # Replace HCL-style = with :
            raw = re.sub(r'(\w+)\s*=\s*', r'"\1": ', raw)
            return json.loads(raw)
        except (json.JSONDecodeError, Exception):
            pass

    # Try to extract statement-level info from HCL
    statements = []
    stmt_blocks = re.finditer(
        r'statement\s*\{([\s\S]*?)\n\s*\}', content
    )
    for match in stmt_blocks:
        block = match.group(1)
        stmt = {}

        effect = re.search(r'effect\s*=\s*"(\w+)"', block)
        stmt["Effect"] = effect.group(1) if effect else "Allow"

        actions = re.findall(r'actions\s*=\s*\[([\s\S]*?)\]', block)
        if actions:
            stmt["Action"] = re.findall(r'"([^"]+)"', actions[0])

        resources = re.findall(r'resources\s*=\s*\[([\s\S]*?)\]', block)
        if resources:
            stmt["Resource"] = re.findall(r'"([^"]+)"', resources[0])

        if stmt.get("Action") or stmt.get("Resource"):
            statements.append(stmt)

    if statements:
        return {"Version": "2012-10-17", "Statement": statements}

    return None


def generate_labels_template():
    """Generate a CSV template for manual labeling."""
    if not SCRAPED_DIR.exists():
        print(f"Error: {SCRAPED_DIR} does not exist. Run the scraper first.")
        sys.exit(1)

    rows = []
    for f in sorted(SCRAPED_DIR.glob("raw_*.tf")):
        content = f.read_text(encoding='utf-8')
        label, vuln_type, severity = auto_label_tf_block(content)

        # Extract a brief description
        type_match = re.search(r'"(aws_iam_\w+)"', content)
        resource_type = type_match.group(1) if type_match else "unknown"

        rows.append({
            "filename": f.name,
            "resource_type": resource_type,
            "auto_label": label,
            "auto_vulnerability_type": vuln_type,
            "auto_severity": severity,
            "manual_label": "",        # User fills this in
            "manual_severity": "",     # User fills this in
            "notes": "",               # User adds notes
        })

    LABELS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LABELS_FILE, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    # Print summary
    labels = {"vulnerable": 0, "secure": 0, "unknown": 0}
    for r in rows:
        labels[r["auto_label"]] = labels.get(r["auto_label"], 0) + 1

    print(f"Generated {LABELS_FILE}")
    print(f"Total files: {len(rows)}")
    print(f"Auto-labeled: vulnerable={labels.get('vulnerable',0)}, "
          f"secure={labels.get('secure',0)}, "
          f"unknown={labels.get('unknown',0)}")
    print(f"\nReview and fill in 'manual_label' and 'manual_severity' columns.")
    print(f"Then run: python scripts/integrate_scraped.py --integrate")


def integrate_policies(use_auto_labels: bool = False):
    """
    Integrate labeled scraped policies into the training dataset.
    """
    if not use_auto_labels and not LABELS_FILE.exists():
        print(f"Error: {LABELS_FILE} not found.")
        print("Run --generate-labels first, review the CSV, then --integrate.")
        sys.exit(1)

    # Load labels
    labels_map = {}
    if LABELS_FILE.exists() and not use_auto_labels:
        with open(LABELS_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                label = row.get("manual_label") or row.get("auto_label", "unknown")
                severity = row.get("manual_severity") or row.get("auto_severity", "unknown")
                vuln_type = row.get("auto_vulnerability_type", "needs_review")
                if label in ("vulnerable", "secure"):
                    labels_map[row["filename"]] = {
                        "label": label,
                        "severity": severity,
                        "vulnerability_type": vuln_type,
                    }

    integrated = 0
    skipped = 0

    for f in sorted(SCRAPED_DIR.glob("raw_*.tf")):
        content = f.read_text(encoding='utf-8')

        if use_auto_labels:
            label, vuln_type, severity = auto_label_tf_block(content)
            if label == "unknown":
                skipped += 1
                continue
            label_info = {"label": label, "severity": severity, "vulnerability_type": vuln_type}
        elif f.name in labels_map:
            label_info = labels_map[f.name]
        else:
            skipped += 1
            continue

        # Extract or create policy JSON
        policy = extract_policy_from_tf(content)
        if policy is None:
            # Save as-is with metadata wrapper
            fp = hashlib.sha256(content.encode()).hexdigest()[:12]
            policy = {
                "Version": "2012-10-17",
                "Statement": [{"Effect": "Allow", "Action": ["*"], "Resource": ["*"]}],
                "_raw_source": "terraform",
                "_parse_note": "Auto-extracted; original HCL could not be fully parsed",
            }

        # Generate filename
        prefix = "escalation" if label_info["label"] == "vulnerable" else "secure"
        vuln = label_info["vulnerability_type"].replace(" ", "_")
        fp = hashlib.sha256(content.encode()).hexdigest()[:8]
        out_name = f"scraped_{prefix}_{vuln}_{fp}.json"
        out_path = SAMPLES_DIR / out_name

        out_path.write_text(json.dumps(policy, indent=2))
        integrated += 1

    print(f"Integrated: {integrated} policies")
    print(f"Skipped: {skipped} (unlabeled or unknown)")
    print(f"Output: {SAMPLES_DIR}")

    if integrated > 0:
        print(f"\nRemember to update LABELS.json and policies_labeled.csv")
        print(f"by running: python generate_data_files.py")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrate scraped IAM policies into PolicyGraph dataset"
    )
    parser.add_argument(
        "--generate-labels", action="store_true",
        help="Generate a CSV template for manual labeling"
    )
    parser.add_argument(
        "--integrate", action="store_true",
        help="Integrate labeled policies into the dataset"
    )
    parser.add_argument(
        "--auto-label", action="store_true",
        help="Use auto-labeling heuristics (skip manual review)"
    )
    args = parser.parse_args()

    if args.generate_labels:
        generate_labels_template()
    elif args.integrate:
        integrate_policies(use_auto_labels=args.auto_label)
    else:
        parser.print_help()
