#!/usr/bin/env python3
"""
Interactive labeling tool for scraped IAM policies.

Workflow:
  1. Auto-score policies using PolicyGraph's trained GAT model
  2. Present each policy in a terminal UI for human review
  3. Accept/reject/edit labels with keyboard shortcuts
  4. Save progress for resume across multiple sessions

Usage:
    # Score-only mode (batch overnight)
    python scripts/label_scraped_policies.py \
        --scraped data/scraped_policies \
        --out data/labeled_policies \
        --model checkpoints/long/best_model.pt \
        --score-only

    # Interactive review (resume from saved progress)
    python scripts/label_scraped_policies.py \
        --scraped data/scraped_policies \
        --out data/labeled_policies \
        --review-only

    # Full pipeline: score + review
    python scripts/label_scraped_policies.py \
        --scraped data/scraped_policies \
        --out data/labeled_policies \
        --model checkpoints/long/best_model.pt

Keyboard shortcuts during interactive review:
    a = accept model prediction
    r = reject (flip label)
    e = edit severity (cycle: critical → high → medium → low)
    s = skip (do not label this policy)
    q = quit (progress is saved automatically)
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import hashlib
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ── HCL-to-JSON Policy Extraction ──────────────────────────────────────────

# Dangerous IAM patterns (for heuristic labeling when model unavailable)
VULN_PATTERNS = {
    "passrole_lambda": re.compile(r"iam:PassRole.*lambda:CreateFunction|lambda:CreateFunction.*iam:PassRole", re.I | re.S),
    "passrole_ec2": re.compile(r"iam:PassRole.*ec2:RunInstances|ec2:RunInstances.*iam:PassRole", re.I | re.S),
    "passrole_ecs": re.compile(r"iam:PassRole.*ecs:RunTask|ecs:RunTask.*iam:PassRole", re.I | re.S),
    "passrole_glue": re.compile(r"iam:PassRole.*glue:CreateDevEndpoint|glue:CreateDevEndpoint.*iam:PassRole", re.I | re.S),
    "passrole_datapipeline": re.compile(r"iam:PassRole.*datapipeline:CreatePipeline|datapipeline:CreatePipeline.*iam:PassRole", re.I | re.S),
    "passrole_sagemaker": re.compile(r"iam:PassRole.*sagemaker:CreateNotebookInstance|sagemaker:CreateNotebookInstance.*iam:PassRole", re.I | re.S),
    "passrole_generic": re.compile(r"iam:PassRole", re.I),
    "iam_wildcard": re.compile(r'"iam:\*"', re.I),
    "admin_wildcard": re.compile(r'Action\s*[=:]\s*"\*"', re.I),
    "attach_policy": re.compile(r"iam:Attach(User|Role|Group)Policy", re.I),
    "put_policy": re.compile(r"iam:Put(User|Role)Policy", re.I),
    "create_policy_version": re.compile(r"iam:CreatePolicyVersion", re.I),
    "update_assume_role": re.compile(r"iam:UpdateAssumeRolePolicy", re.I),
    "create_access_key": re.compile(r"iam:CreateAccessKey", re.I),
    "wildcard_assume_role": re.compile(r'sts:AssumeRole.*Resource.*"\*"', re.I | re.S),
}

SEVERITY_MAP = {
    "passrole_lambda": "critical",
    "passrole_ec2": "critical",
    "passrole_ecs": "critical",
    "passrole_glue": "critical",
    "passrole_datapipeline": "critical",
    "passrole_sagemaker": "critical",
    "passrole_generic": "high",
    "iam_wildcard": "critical",
    "admin_wildcard": "critical",
    "attach_policy": "critical",
    "put_policy": "high",
    "create_policy_version": "critical",
    "update_assume_role": "critical",
    "create_access_key": "high",
    "wildcard_assume_role": "high",
}


def extract_policy_json_from_tf(tf_content: str) -> Optional[Dict[str, Any]]:
    """
    Best-effort extraction of an IAM policy JSON dict from a Terraform HCL block.

    Tries multiple strategies:
    1. Find jsonencode({...}) blocks and parse
    2. Extract HCL statement blocks and convert to IAM JSON
    3. Look for inline JSON strings in 'policy = <<EOF ... EOF' heredocs
    """
    # Strategy 1: jsonencode(...) blocks
    json_match = re.search(r'jsonencode\(\s*\{([\s\S]*?)\}\s*\)', tf_content)
    if json_match:
        try:
            raw = "{" + json_match.group(1) + "}"
            # Rough HCL -> JSON conversion
            raw = re.sub(r'(\w+)\s*=\s*', r'"\1": ', raw)
            raw = raw.replace("'", '"')
            # Remove trailing commas
            raw = re.sub(r',\s*([}\]])', r'\1', raw)
            return json.loads(raw)
        except (json.JSONDecodeError, Exception):
            pass

    # Strategy 2: heredoc inline JSON
    heredoc_match = re.search(r'policy\s*=\s*<<-?\s*(\w+)\s*\n([\s\S]*?)\n\s*\1', tf_content)
    if heredoc_match:
        try:
            return json.loads(heredoc_match.group(2))
        except (json.JSONDecodeError, Exception):
            pass

    # Strategy 3: Extract HCL statement blocks
    statements = []
    stmt_blocks = re.finditer(r'statement\s*\{([\s\S]*?)\n\s*\}', tf_content)
    for match in stmt_blocks:
        block = match.group(1)
        stmt: Dict[str, Any] = {}

        effect = re.search(r'effect\s*=\s*"(\w+)"', block)
        stmt["Effect"] = effect.group(1) if effect else "Allow"

        # actions = [...]
        actions_match = re.search(r'actions\s*=\s*\[([\s\S]*?)\]', block)
        if actions_match:
            stmt["Action"] = re.findall(r'"([^"]+)"', actions_match.group(1))

        # Single action = "..."
        if "Action" not in stmt:
            single_action = re.search(r'(?<!act)actions?\s*=\s*"([^"]+)"', block)
            if single_action:
                stmt["Action"] = [single_action.group(1)]

        # resources = [...]
        resources_match = re.search(r'resources\s*=\s*\[([\s\S]*?)\]', block)
        if resources_match:
            stmt["Resource"] = re.findall(r'"([^"]+)"', resources_match.group(1))

        if not resources_match:
            single_resource = re.search(r'resource\s*=\s*"([^"]+)"', block)
            if single_resource:
                stmt["Resource"] = [single_resource.group(1)]

        # condition
        cond_match = re.search(r'condition\s*\{([\s\S]*?)\}', block)
        if cond_match:
            cond_text = cond_match.group(1)
            test_val = re.search(r'test\s*=\s*"([^"]+)"', cond_text)
            variable_val = re.search(r'variable\s*=\s*"([^"]+)"', cond_text)
            values_val = re.findall(r'"([^"]+)"', cond_text)
            if test_val and variable_val:
                stmt["Condition"] = {
                    test_val.group(1): {variable_val.group(1): values_val}
                }

        if stmt.get("Action") or stmt.get("Resource"):
            statements.append(stmt)

    if statements:
        return {"Version": "2012-10-17", "Statement": statements}

    # Strategy 4: If we see inline policy JSON in the tf text
    json_match2 = re.search(r'policy\s*=\s*"((?:\\"|[^"])*)"', tf_content)
    if json_match2:
        try:
            raw = json_match2.group(1).replace('\\"', '"')
            return json.loads(raw)
        except (json.JSONDecodeError, Exception):
            pass

    return None


def detect_vulnerability_type(tf_content: str) -> Tuple[str, str, str]:
    """
    Detect vulnerability type from TF content using pattern matching.
    Returns (label, vulnerability_type, severity).
    """
    for vuln_type, pattern in VULN_PATTERNS.items():
        if pattern.search(tf_content):
            # For passrole_generic, only flag if there's also a resource wildcard or compute service
            if vuln_type == "passrole_generic":
                has_compute = any(svc in tf_content.lower() for svc in
                    ["lambda", "ec2", "ecs", "glue", "datapipeline", "sagemaker",
                     "cloudformation", "codebuild"])
                has_wildcard_resource = re.search(r'resource[s]?\s*=\s*.*\*', tf_content, re.I)
                if not (has_compute or has_wildcard_resource):
                    continue
            return ("vulnerable", vuln_type, SEVERITY_MAP.get(vuln_type, "medium"))

    # Check for broad permissions without specific escalation pattern
    has_condition = re.search(r'[Cc]ondition', tf_content)
    has_deny = re.search(r'[Ee]ffect\s*=\s*"Deny"', tf_content)
    has_mfa = re.search(r'[Mm][Ff][Aa]', tf_content)

    secure_indicators = sum([bool(has_condition), bool(has_deny), bool(has_mfa)])

    if secure_indicators >= 2:
        return ("secure", "none", "low")

    return ("unknown", "needs_review", "unknown")


def policy_fingerprint(content: str) -> str:
    """Create a stable fingerprint for deduplication."""
    return hashlib.sha256(content.encode()).hexdigest()


# ── Progress State ──────────────────────────────────────────────────────────

class LabelingState:
    """Manages persistent state across labeling sessions."""

    def __init__(self, out_dir: Path):
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = out_dir / "labeling_state.json"
        self.scores_file = out_dir / "model_scores.json"
        self.labels_json = out_dir / "LABELS.json"
        self.labels_csv = out_dir / "policies_labeled.csv"
        self.policies_dir = out_dir / "policies"
        self.policies_dir.mkdir(parents=True, exist_ok=True)

        # Load existing state
        self.state = self._load_json(self.state_file, {
            "reviewed": {},      # filename -> {label, severity, vuln_type, ...}
            "skipped": [],       # filenames that were skipped
            "last_index": 0,     # resume index
            "total_scored": 0,
            "total_reviewed": 0,
            "session_history": [],
        })
        self.scores = self._load_json(self.scores_file, {})
        # Sync auto-labeled entries from LABELS.json into reviewed state
        if self.labels_json.exists():
            try:
                labels_data = json.loads(self.labels_json.read_text(encoding="utf-8"))
                entries = labels_data.get("labels", [])
                for entry in entries:
                    fname = entry.get("filename") or entry.get("output_filename")
                    if fname and fname not in self.state["reviewed"]:
                        self.state["reviewed"][fname] = {
                            "label": entry.get("label", "secure"),
                            "severity": entry.get("severity", "low"),
                            "source": entry.get("source", "auto_label"),
                        }
            except Exception:
                pass
    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            with path.open("r") as f:
                return json.load(f)
        return default

    def save(self):
        """Save current state to disk."""
        with self.state_file.open("w") as f:
            json.dump(self.state, f, indent=2)
        with self.scores_file.open("w") as f:
            json.dump(self.scores, f, indent=2)
        self._write_labels_json()
        self._write_labels_csv()

    def add_score(self, filename: str, score_data: Dict[str, Any]):
        """Record a model score."""
        self.scores[filename] = score_data
        self.state["total_scored"] = len(self.scores)

    def add_review(self, filename: str, review_data: Dict[str, Any]):
        """Record a human review."""
        self.state["reviewed"][filename] = review_data
        self.state["total_reviewed"] = len(self.state["reviewed"])
        if filename in self.state["skipped"]:
            self.state["skipped"].remove(filename)

    def skip(self, filename: str):
        """Mark a policy as skipped."""
        if filename not in self.state["skipped"]:
            self.state["skipped"].append(filename)

    def is_reviewed(self, filename: str) -> bool:
        return filename in self.state["reviewed"]

    def is_scored(self, filename: str) -> bool:
        return filename in self.scores

    def get_review_stats(self) -> Dict[str, int]:
        reviewed = self.state["reviewed"]
        stats = {"total": len(reviewed), "vulnerable": 0, "secure": 0}
        for info in reviewed.values():
            label = info.get("label", "unknown")
            if label in stats:
                stats[label] += 1
        return stats

    def _write_labels_json(self):
        """Write LABELS.json in PolicyGraph format."""
        reviewed = self.state["reviewed"]
        if not reviewed:
            return

        labels_list = []
        vuln_count = sum(1 for v in reviewed.values() if v.get("label") == "vulnerable")
        secure_count = sum(1 for v in reviewed.values() if v.get("label") == "secure")

        severity_dist = {}
        for info in reviewed.values():
            sev = info.get("severity", "unknown")
            severity_dist[sev] = severity_dist.get(sev, 0) + 1

        for filename, info in reviewed.items():
            labels_list.append({
                "filename": info.get("output_filename", filename),
                "label": info.get("label", "unknown"),
                "severity": info.get("severity", "unknown"),
                "vulnerability_type": info.get("vulnerability_type", "none"),
                "risk_score": info.get("risk_score", 0),
                "attack_path": info.get("attack_paths", []),
                "remediation": info.get("remediation", ""),
                "affected_services": info.get("affected_services", []),
                "risk_patterns": info.get("risk_patterns", ""),
                "secure_alternative": None,
            })

        output = {
            "description": "Labels for scraped IAM policies (labeled via label_scraped_policies.py)",
            "version": "1.0.0",
            "total_policies": len(reviewed),
            "vulnerable_count": vuln_count,
            "secure_count": secure_count,
            "severity_distribution": severity_dist,
            "labels": labels_list,
        }

        with self.labels_json.open("w") as f:
            json.dump(output, f, indent=2)

    def _write_labels_csv(self):
        """Write policies_labeled.csv in PolicyGraph format."""
        reviewed = self.state["reviewed"]
        if not reviewed:
            return

        fieldnames = [
            "filename", "label", "vulnerability_type", "severity",
            "risk_patterns", "escalation_path", "attack_path",
            "risk_score", "remediation", "affected_services", "secure_alternative",
        ]

        with self.labels_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for filename, info in reviewed.items():
                attack_paths = info.get("attack_paths", [])
                writer.writerow({
                    "filename": info.get("output_filename", filename),
                    "label": info.get("label", "unknown"),
                    "vulnerability_type": info.get("vulnerability_type", "none"),
                    "severity": info.get("severity", "unknown"),
                    "risk_patterns": info.get("risk_patterns", ""),
                    "escalation_path": info.get("escalation_path", "none"),
                    "attack_path": json.dumps(attack_paths) if attack_paths else "[]",
                    "risk_score": info.get("risk_score", 0),
                    "remediation": info.get("remediation", ""),
                    "affected_services": ",".join(info.get("affected_services", [])),
                    "secure_alternative": "none",
                })


# ── Scoring Engine ──────────────────────────────────────────────────────────

class PolicyScorer:
    """Score policies using the trained PolicyGraph model."""

    def __init__(self, model_path: Optional[str] = None):
        self.analyzer = None
        self.model_available = False

        if model_path and Path(model_path).exists():
            try:
                from policygraph.analyzer import PolicyAnalyzer
                self.analyzer = PolicyAnalyzer(model_path=model_path)
                self.model_available = True
                log.info("Model loaded from %s", model_path)
            except Exception as e:
                log.warning("Could not load model: %s. Using heuristic scoring only.", e)

    def score_policy(self, tf_content: str, filename: str) -> Dict[str, Any]:
        """
        Score a single policy from its TF content.

        Returns a dict with:
          - risk_score (0-1)
          - prediction_label ("vulnerable" / "secure")
          - vulnerability_type
          - severity
          - vulnerabilities_detected (list of strings)
          - method ("model" / "heuristic")
        """
        # Extract JSON policy from TF content
        policy_json = extract_policy_json_from_tf(tf_content)

        result: Dict[str, Any] = {
            "filename": filename,
            "has_json_policy": policy_json is not None,
        }

        # If we have a JSON policy and a model, use the model
        if policy_json and self.model_available and self.analyzer:
            try:
                analysis = self.analyzer.analyze_policy(policy_json)
                model_score = analysis.get("model_risk_score", 0)
                threshold = analysis.get("threshold", 0.3)
                result.update({
                    "risk_score": analysis["risk_score"],
                    "model_risk_score": model_score,
                    "heuristic_risk_score": analysis.get("heuristic_risk_score", 0),
                    "prediction_label": "vulnerable" if model_score >= threshold else "secure",
                    "vulnerabilities_detected": analysis.get("vulnerabilities_detected", []),
                    "attack_paths": [p["description"] for p in analysis.get("attack_paths", [])],
                    "method": "model",
                    "threshold": analysis.get("threshold", 0.3),
                    "num_nodes": analysis.get("explanation", {}).get("num_nodes", 0),
                    "num_edges": analysis.get("explanation", {}).get("num_edges", 0),
                })
                return result
            except Exception as e:
                log.debug("Model scoring failed for %s: %s", filename, e)

        # Fallback: heuristic scoring from raw TF content
        label, vuln_type, severity = detect_vulnerability_type(tf_content)

        # Compute a simple heuristic risk score
        risk_score = 0.0
        if label == "vulnerable":
            risk_score = {"critical": 0.9, "high": 0.7, "medium": 0.5}.get(severity, 0.4)
        elif label == "secure":
            risk_score = 0.1
        else:
            # unknown — mid-range
            risk_score = 0.35

        result.update({
            "risk_score": risk_score,
            "model_risk_score": None,
            "heuristic_risk_score": risk_score,
            "prediction_label": label if label != "unknown" else "secure",
            "vulnerabilities_detected": [vuln_type] if label == "vulnerable" else [],
            "attack_paths": [],
            "method": "heuristic",
            "vulnerability_type_detected": vuln_type,
            "severity_detected": severity,
        })
        return result


# ── Interactive Review UI ───────────────────────────────────────────────────

SEVERITY_CYCLE = ["critical", "high", "medium", "low"]


def _clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def _get_keypress() -> str:
    """Read a single keypress (cross-platform)."""
    try:
        if os.name == "nt":
            import msvcrt
            return msvcrt.getch().decode("utf-8", errors="ignore").lower()
        else:
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1).lower()
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch
    except Exception:
        return input("Enter command (a/r/e/s/q): ").strip().lower()[:1]


def format_tf_preview(content: str, max_lines: int = 30) -> str:
    """Format TF content for display with line limit."""
    lines = content.strip().split("\n")
    if len(lines) > max_lines:
        shown = lines[:max_lines]
        shown.append(f"  ... ({len(lines) - max_lines} more lines)")
        return "\n".join(shown)
    return "\n".join(lines)


def _detect_services(content: str) -> List[str]:
    """Detect AWS services mentioned in the TF content."""
    service_patterns = {
        "IAM": r"iam:",
        "STS": r"sts:",
        "S3": r"s3:",
        "EC2": r"ec2:",
        "Lambda": r"lambda:",
        "ECS": r"ecs:",
        "CloudFormation": r"cloudformation:",
        "Glue": r"glue:",
        "DynamoDB": r"dynamodb:",
        "SNS": r"sns:",
        "SQS": r"sqs:",
        "CloudWatch": r"cloudwatch:|logs:",
        "CodeBuild": r"codebuild:",
        "CodeDeploy": r"codedeploy:",
        "KMS": r"kms:",
        "SSM": r"ssm:",
        "SageMaker": r"sagemaker:",
        "RDS": r"rds:",
        "ElasticLoadBalancing": r"elasticloadbalancing:",
    }
    found = []
    for service, pattern in service_patterns.items():
        if re.search(pattern, content, re.I):
            found.append(service)
    return found or ["Unknown"]


def _infer_escalation_path(vuln_type: str) -> str:
    """Generate a human-readable escalation path description."""
    paths = {
        "passrole_lambda": "PassRole to Lambda execution role → Create function with admin role → Invoke for admin access",
        "passrole_ec2": "PassRole to EC2 instance profile → Launch instance with privileged role → Access from instance",
        "passrole_ecs": "PassRole to ECS task role → Run task with privileged role → Access from container",
        "passrole_glue": "PassRole to Glue role → Create dev endpoint with admin role → SSH for admin access",
        "passrole_datapipeline": "PassRole to pipeline role → Create pipeline with admin role → Execute for admin access",
        "passrole_sagemaker": "PassRole to SageMaker role → Create notebook with admin role → Execute for admin access",
        "passrole_generic": "PassRole to service role → Create resource with privileged role → Gain elevated access",
        "iam_wildcard": "Full IAM access → Create admin user/role → Complete account takeover",
        "admin_wildcard": "Wildcard action on all resources → Unrestricted access to all AWS services",
        "attach_policy": "Attach any policy to self/others → Attach AdministratorAccess → Full admin",
        "put_policy": "Put inline policy on role/user → Grant self any permission → Escalate privileges",
        "create_policy_version": "Create new policy version → Set as default → Grant self any permission",
        "update_assume_role": "Update role trust policy → Allow self to assume admin role → Full access",
        "create_access_key": "Create access key for other users → Impersonate privileged users",
        "wildcard_assume_role": "Assume any role → Find admin role → Assume for full access",
    }
    return paths.get(vuln_type, "none")


def _infer_remediation(vuln_type: str) -> str:
    """Generate remediation advice."""
    remediations = {
        "passrole_lambda": "Restrict iam:PassRole to specific role ARNs. Add iam:PassedToService condition for lambda.amazonaws.com.",
        "passrole_ec2": "Restrict iam:PassRole to specific instance profile ARNs. Limit ec2:RunInstances to specific AMIs.",
        "passrole_ecs": "Restrict iam:PassRole to specific task role ARNs. Limit ecs:RunTask to specific task definitions.",
        "passrole_glue": "Restrict iam:PassRole to specific Glue role ARNs. Limit glue:CreateDevEndpoint permissions.",
        "passrole_generic": "Scope iam:PassRole resource to specific role ARNs. Add iam:PassedToService condition.",
        "iam_wildcard": "Replace iam:* with specific required IAM actions. Scope resources to specific ARNs.",
        "admin_wildcard": "Replace wildcard actions with specific required actions. Scope resources to specific ARNs.",
        "attach_policy": "Restrict to specific policy ARNs. Add permission boundary. Use aws:PrincipalTag conditions.",
        "put_policy": "Remove PutUserPolicy/PutRolePolicy. Use managed policies with approval workflow instead.",
        "create_policy_version": "Remove iam:CreatePolicyVersion. Use CI/CD pipeline for policy changes.",
        "update_assume_role": "Remove iam:UpdateAssumeRolePolicy. Use separate admin account for trust policy changes.",
        "create_access_key": "Restrict iam:CreateAccessKey to self only (${aws:username}). Require MFA.",
        "wildcard_assume_role": "Restrict sts:AssumeRole to specific role ARNs instead of wildcard.",
    }
    return remediations.get(vuln_type,
        "Review and restrict permissions following least-privilege principle.")


def interactive_review(
    files: List[Tuple[str, str]],  # (filename, content)
    state: LabelingState,
    start_index: int = 0,
):
    """
    Interactive terminal UI for reviewing and labeling policies.

    Args:
        files: List of (filename, tf_content) tuples
        state: LabelingState for persistence
        start_index: Index to resume from
    """
    total = len(files)
    reviewed_this_session = 0
    session_start = time.time()

    i = start_index
    while i < total:
        filename, content = files[i]

        # Skip already reviewed
        if state.is_reviewed(filename):
            i += 1
            continue

        # Get score data
        score_data = state.scores.get(filename, {})

        # Auto-skip reference-only files (no extractable JSON policy, heuristic only)
        if not score_data.get("has_json_policy", True) and score_data.get("method") == "heuristic":
            i += 1
            continue
        risk_score = score_data.get("risk_score", 0.5)
        predicted_label = score_data.get("prediction_label", "unknown")
        vulns = score_data.get("vulnerabilities_detected", [])
        method = score_data.get("method", "unknown")
        vuln_type = score_data.get("vulnerability_type_detected", "needs_review")
        severity = score_data.get("severity_detected", "medium")

        # Auto-determine severity from risk score if not set
        if severity == "unknown":
            if risk_score >= 0.8:
                severity = "critical"
            elif risk_score >= 0.6:
                severity = "high"
            elif risk_score >= 0.4:
                severity = "medium"
            else:
                severity = "low"

        # Display
        _clear_screen()
        stats = state.get_review_stats()
        remaining = total - i - stats["total"]
        elapsed = time.time() - session_start
        rate = reviewed_this_session / elapsed * 3600 if elapsed > 0 and reviewed_this_session > 0 else 0

        print("=" * 78)
        print(f"  PolicyGraph Interactive Labeling — [{i + 1}/{total}]")
        print(f"  Reviewed: {stats['total']} (V:{stats['vulnerable']} S:{stats['secure']}) "
              f"| Skipped: {len(state.state['skipped'])} | Remaining: ~{remaining}")
        if rate > 0:
            print(f"  Rate: {rate:.0f}/hr | ETA: {remaining / rate * 60:.0f} min")
        print("=" * 78)
        print()

        # Score summary
        score_color = "\033[91m" if risk_score >= 0.5 else "\033[93m" if risk_score >= 0.3 else "\033[92m"
        print(f"  File: {filename}")
        print(f"  Score: {score_color}{risk_score:.3f}\033[0m ({method})")
        print(f"  Prediction: {'🔴 VULNERABLE' if predicted_label == 'vulnerable' else '🟢 SECURE'}")
        if vuln_type and vuln_type != "needs_review":
            print(f"  Vulnerability: {vuln_type} ({severity})")
        if vulns:
            print(f"  Patterns: {', '.join(vulns[:3])}")
        print()

        # Policy preview
        print("─" * 78)
        print(format_tf_preview(content, max_lines=25))
        print("─" * 78)
        print()

        # Controls
        print("  \033[1m[a]\033[0m Accept  "
              "\033[1m[r]\033[0m Reject  "
              "\033[1m[e]\033[0m Edit severity  "
              "\033[1m[s]\033[0m Skip  "
              "\033[1m[q]\033[0m Quit & save")
        print()

        key = _get_keypress()

        if key == "a":
            # Accept model prediction
            label = predicted_label if predicted_label in ("vulnerable", "secure") else "secure"
            services = _detect_services(content)
            state.add_review(filename, {
                "label": label,
                "severity": severity if label == "vulnerable" else "low",
                "vulnerability_type": vuln_type if label == "vulnerable" else "none",
                "risk_score": int(risk_score * 10),
                "risk_patterns": vuln_type if label == "vulnerable" else "none",
                "escalation_path": _infer_escalation_path(vuln_type) if label == "vulnerable" else "none",
                "attack_paths": [_infer_escalation_path(vuln_type)] if label == "vulnerable" else [],
                "remediation": _infer_remediation(vuln_type) if label == "vulnerable" else "N/A — this policy follows security best practices.",
                "affected_services": services,
                "output_filename": _make_output_filename(filename, label, vuln_type),
            })
            # Copy policy file
            _save_policy_file(state.policies_dir, filename, content, label, vuln_type)
            reviewed_this_session += 1
            i += 1

        elif key == "r":
            # Reject (flip label)
            label = "secure" if predicted_label == "vulnerable" else "vulnerable"
            services = _detect_services(content)

            if label == "vulnerable" and vuln_type == "needs_review":
                print("\n  Enter vulnerability type (or press Enter for 'manual_review'):", end=" ")
                try:
                    vt = input().strip()
                except EOFError:
                    vt = ""
                vuln_type = vt if vt else "manual_review"
                print("  Enter severity (critical/high/medium/low):", end=" ")
                try:
                    sev = input().strip()
                except EOFError:
                    sev = ""
                severity = sev if sev in SEVERITY_CYCLE else "medium"

            state.add_review(filename, {
                "label": label,
                "severity": severity if label == "vulnerable" else "low",
                "vulnerability_type": vuln_type if label == "vulnerable" else "none",
                "risk_score": int(risk_score * 10),
                "risk_patterns": vuln_type if label == "vulnerable" else "none",
                "escalation_path": _infer_escalation_path(vuln_type) if label == "vulnerable" else "none",
                "attack_paths": [_infer_escalation_path(vuln_type)] if label == "vulnerable" else [],
                "remediation": _infer_remediation(vuln_type) if label == "vulnerable" else "N/A — this policy follows security best practices.",
                "affected_services": services,
                "output_filename": _make_output_filename(filename, label, vuln_type),
            })
            _save_policy_file(state.policies_dir, filename, content, label, vuln_type)
            reviewed_this_session += 1
            i += 1

        elif key == "e":
            # Edit severity — cycle through options
            current_idx = SEVERITY_CYCLE.index(severity) if severity in SEVERITY_CYCLE else 0
            severity = SEVERITY_CYCLE[(current_idx + 1) % len(SEVERITY_CYCLE)]
            print(f"\n  Severity changed to: {severity}")
            time.sleep(0.5)
            # Don't advance — re-display with new severity

        elif key == "s":
            state.skip(filename)
            i += 1

        elif key == "q":
            state.state["last_index"] = i
            state.state["session_history"].append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "reviewed": reviewed_this_session,
                "elapsed_seconds": int(time.time() - session_start),
            })
            state.save()
            print(f"\n  Progress saved. Reviewed {reviewed_this_session} this session.")
            print(f"  Resume with --review-only to continue from policy #{i + 1}.")
            return

        # Auto-save every 10 reviews
        if reviewed_this_session > 0 and reviewed_this_session % 10 == 0:
            state.state["last_index"] = i
            state.save()
            log.info("Auto-saved progress at review #%d", reviewed_this_session)

    # All done
    state.state["last_index"] = total
    state.state["session_history"].append({
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reviewed": reviewed_this_session,
        "elapsed_seconds": int(time.time() - session_start),
    })
    state.save()
    print(f"\n  All policies reviewed! Total: {state.get_review_stats()['total']}")


def _make_output_filename(original: str, label: str, vuln_type: str) -> str:
    """Generate output filename in PolicyGraph naming convention."""
    fp = hashlib.sha256(original.encode()).hexdigest()[:8]
    if label == "vulnerable":
        prefix = "escalation" if vuln_type not in ("manual_review", "needs_review") else "vulnerable"
        return f"scraped_{prefix}_{vuln_type}_{fp}.json"
    else:
        return f"scraped_secure_{fp}.json"


def _save_policy_file(policies_dir: Path, filename: str, tf_content: str, label: str, vuln_type: str):
    """Save the extracted policy JSON to the policies directory."""
    policy_json = extract_policy_json_from_tf(tf_content)
    if policy_json is None:
        # Can't extract JSON — save minimal policy with raw content reference
        policy_json = {
            "Version": "2012-10-17",
            "Statement": [],
            "_source": "terraform_hcl",
            "_note": "Could not fully parse HCL to JSON. Original file preserved.",
            "_original_filename": filename,
        }

    out_name = _make_output_filename(filename, label, vuln_type)
    out_path = policies_dir / out_name
    with out_path.open("w") as f:
        json.dump(policy_json, f, indent=2)


# ── Main Pipeline ───────────────────────────────────────────────────────────

def load_scraped_files(scraped_dir: Path) -> List[Tuple[str, str]]:
    """Load all scraped .tf and .json files from the scraped directory."""
    files = []
    for ext in ("*.tf", "*.json"):
        for f in sorted(scraped_dir.glob(ext)):
            if f.name in ("manual_labels.csv", "model_scores.json", "labeling_state.json"):
                continue
            content = f.read_text(errors="replace")
            if content.strip():
                files.append((f.name, content))
    log.info("Loaded %d scraped policy files", len(files))
    return files


def run_batch_scoring(files: List[Tuple[str, str]], state: LabelingState, model_path: Optional[str]):
    """Score all policies in batch mode (no interaction)."""
    scorer = PolicyScorer(model_path=model_path)
    total = len(files)
    scored = 0
    skipped = 0

    log.info("Scoring %d policies...", total)
    start = time.time()

    for idx, (filename, content) in enumerate(files):
        if state.is_scored(filename):
            skipped += 1
            continue

        try:
            score_data = scorer.score_policy(content, filename)
            state.add_score(filename, score_data)
            scored += 1
        except Exception as e:
            log.warning("Failed to score %s: %s", filename, e)

        if (idx + 1) % 50 == 0:
            elapsed = time.time() - start
            rate = scored / elapsed if elapsed > 0 else 0
            log.info("  Progress: %d/%d (%.1f/sec), %d skipped (already scored)",
                     idx + 1, total, rate, skipped)
            state.save()  # periodic save

    elapsed = time.time() - start
    state.save()
    log.info("Scoring complete: %d scored, %d skipped, %.1f seconds", scored, skipped, elapsed)

    # Print distribution summary
    labels = {"vulnerable": 0, "secure": 0, "unknown": 0}
    for score_data in state.scores.values():
        pred = score_data.get("prediction_label", "unknown")
        labels[pred] = labels.get(pred, 0) + 1

    log.info("Score distribution: vulnerable=%d, secure=%d, unknown=%d",
             labels["vulnerable"], labels["secure"], labels["unknown"])


def main():
    parser = argparse.ArgumentParser(
        description="Interactive labeling tool for scraped IAM policies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Score all policies with model (batch overnight)
  python scripts/label_scraped_policies.py \\
      --scraped data/scraped_policies --out data/labeled_policies \\
      --model checkpoints/long/best_model.pt --score-only

  # Interactive review (resume from saved progress)
  python scripts/label_scraped_policies.py \\
      --scraped data/scraped_policies --out data/labeled_policies \\
      --review-only

  # Full pipeline (score + review)
  python scripts/label_scraped_policies.py \\
      --scraped data/scraped_policies --out data/labeled_policies \\
      --model checkpoints/long/best_model.pt

  # Limit to first N policies
  python scripts/label_scraped_policies.py \\
      --scraped data/scraped_policies --out data/labeled_policies \\
      --model checkpoints/long/best_model.pt --limit 5
        """,
    )
    parser.add_argument("--scraped", type=str, default="data/scraped_policies",
                        help="Directory containing scraped policy files")
    parser.add_argument("--out", type=str, default="data/labeled_policies",
                        help="Output directory for labeled data")
    parser.add_argument("--model", type=str, default=None,
                        help="Path to trained model checkpoint (.pt)")
    parser.add_argument("--score-only", action="store_true",
                        help="Only score policies (no interactive review)")
    parser.add_argument("--review-only", action="store_true",
                        help="Only review (skip scoring, use existing scores)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Limit to first N policies (for testing)")
    parser.add_argument("--resume", action="store_true", default=True,
                        help="Resume from last saved position (default: True)")
    args = parser.parse_args()

    # Resolve paths relative to project root
    scraped_dir = PROJECT_ROOT / args.scraped
    out_dir = PROJECT_ROOT / args.out

    if not scraped_dir.exists():
        log.error("Scraped directory not found: %s", scraped_dir)
        sys.exit(1)

    # Load files
    files = load_scraped_files(scraped_dir)
    if args.limit:
        files = files[:args.limit]
        log.info("Limited to %d files", args.limit)

    # Initialize state
    state = LabelingState(out_dir)

    # Scoring phase
    if not args.review_only:
        model_path = args.model
        if model_path:
            model_path = str(PROJECT_ROOT / model_path) if not Path(model_path).is_absolute() else model_path
        run_batch_scoring(files, state, model_path)

    # Review phase
    if not args.score_only:
        start_idx = state.state.get("last_index", 0) if args.resume else 0
        log.info("Starting interactive review at index %d", start_idx)
        interactive_review(files, state, start_index=start_idx)

    # Final summary
    stats = state.get_review_stats()
    print(f"\nFinal stats: {stats['total']} reviewed "
          f"({stats['vulnerable']} vulnerable, {stats['secure']} secure)")
    print(f"Output: {out_dir}")
    if stats["total"] > 0:
        print(f"  LABELS.json: {state.labels_json}")
        print(f"  policies_labeled.csv: {state.labels_csv}")
        print(f"  Policy files: {state.policies_dir}/")


if __name__ == "__main__":
    main()
