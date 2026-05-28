"""
convert_tf_to_json.py — Convert raw_*.tf files into policy_*.json for the labeler.

Usage:
    python scripts/convert_tf_to_json.py --scraped data/scraped_policies
    python scripts/convert_tf_to_json.py --scraped data/scraped_policies --force
"""

import re
import json
import hashlib
import argparse
import logging
from pathlib import Path

try:
    import hcl2
    HCL2_AVAILABLE = True
except ImportError:
    HCL2_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

IAM_RESOURCE_TYPES = {
    "aws_iam_policy", "aws_iam_policy_document", "aws_iam_role",
    "aws_iam_role_policy", "aws_iam_user_policy", "aws_iam_group_policy",
}


def policy_fingerprint(policy: dict) -> str:
    canonical = json.dumps(policy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── Strategy 1: Extract heredoc JSON directly ─────────────────────────────────

def extract_heredoc_policies(text: str) -> list[dict]:
    """Pull raw JSON from <<EOF ... EOF heredoc blocks."""
    results = []
    heredoc_re = re.compile(r'<<-?\s*(\w+)\s*\n(.*?)\n\s*\1', re.DOTALL)
    for m in heredoc_re.finditer(text):
        body = m.group(2).strip()
        try:
            policy = json.loads(body)
            if isinstance(policy, dict) and policy.get("Statement"):
                results.append({"resource_type": "heredoc", "resource_name": "unknown", "policy": policy})
        except json.JSONDecodeError:
            pass
    return results


# ── Strategy 2: Extract jsonencode blocks and parse as JSON or HCL ────────────

def _extract_jsonencode_body(text: str) -> list[str]:
    """Return the raw body strings inside every jsonencode({...}) call."""
    bodies = []
    pattern = re.compile(r'jsonencode\s*\(', re.DOTALL)
    for m in pattern.finditer(text):
        start = m.end()  # position just after the opening (
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == '(':
                depth += 1
            elif text[i] == ')':
                depth -= 1
            i += 1
        bodies.append(text[start:i - 1].strip())
    return bodies


def _hcl_obj_to_json_str(hcl_body: str) -> str:
    """
    Best-effort convert an HCL object body to a JSON string.
    Handles:
      - Unquoted keys:    Version = "2012-10-17"  →  "Version": "2012-10-17"
      - Colon-style keys: Effect : "Allow"         →  "Effect": "Allow"
      - HCL arrays and nested objects
      - Trailing commas
    """
    s = hcl_body
    # Remove single-line comments
    s = re.sub(r'#[^\n]*', '', s)
    s = re.sub(r'//[^\n]*', '', s)
    # Unquoted key = value  →  "key": value
    s = re.sub(r'(?<!["\w])([A-Za-z_][A-Za-z0-9_]*)\s*=\s*', r'"\1": ', s)
    # Unquoted key : value  (e.g. Sid : "x")  →  "key": value
    s = re.sub(r'(?<!["\w])([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(?![:/])', r'"\1": ', s)
    # Remove trailing commas before } or ]
    s = re.sub(r',\s*([}\]])', r'\1', s)
    return s


def extract_jsonencode_policies(text: str) -> list[dict]:
    results = []
    # Skip commented-out blocks
    active_text = re.sub(r'^\s*#.*$', '', text, flags=re.MULTILINE)

    for body in _extract_jsonencode_body(active_text):
        # Try 1: already valid JSON
        try:
            policy = json.loads(body)
            if isinstance(policy, dict) and policy.get("Statement"):
                results.append({"resource_type": "jsonencode", "resource_name": "unknown", "policy": policy})
                continue
        except json.JSONDecodeError:
            pass

        # Try 2: convert HCL-style keys to JSON
        try:
            json_str = _hcl_obj_to_json_str(body)
            policy = json.loads(json_str)
            if isinstance(policy, dict) and policy.get("Statement"):
                results.append({"resource_type": "jsonencode", "resource_name": "unknown", "policy": policy})
                continue
        except (json.JSONDecodeError, Exception):
            pass

    return results


# ── Strategy 3: hcl2 parse with sanitization ──────────────────────────────────

def sanitize_for_hcl2(text: str) -> str:
    # Remove commented-out lines
    text = re.sub(r'^\s*#.*$', '', text, flags=re.MULTILINE)
    # Remove heredocs entirely (handled by strategy 1)
    text = re.sub(r'=\s*<<-?\w+.*?^\w+', '= "HEREDOC"', text, flags=re.DOTALL | re.MULTILINE)
    # Remove jsonencode calls entirely (handled by strategy 2)
    # Replace with a placeholder string so hcl2 sees a valid assignment
    def replace_jsonencode(m):
        return m.group(0)[:m.start('body') - m.start(0)] + '"JSONENCODE_PLACEHOLDER"'

    # Remove jsonencode blocks by depth-counting
    result = []
    i = 0
    while i < len(text):
        m = re.search(r'jsonencode\s*\(', text[i:])
        if not m:
            result.append(text[i:])
            break
        result.append(text[i:i + m.start()])
        result.append('"PLACEHOLDER"')
        # skip past the matching closing paren
        start = i + m.end()
        depth = 1
        j = start
        while j < len(text) and depth > 0:
            if text[j] == '(':
                depth += 1
            elif text[j] == ')':
                depth -= 1
            j += 1
        i = j
    text = ''.join(result)

    # Standard substitutions
    text = re.sub(r'\$\{[^}]*\}', '"PLACEHOLDER"', text)
    text = re.sub(r'\b(?:tostring|tolist|toset|tonumber|tobool|join|format|lower|upper)\s*\([^)]*\)', '"PLACEHOLDER"', text)
    text = re.sub(r'\b(?:module|var|local|data|each|path|aws_iam_role|aws_iam_policy)\.[a-zA-Z0-9_.[\]]+', '"PLACEHOLDER"', text)
    text = re.sub(r'^\s*count\s*=.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*for_each\s*=.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*(?:lifecycle|depends_on|timeouts)\s*\{[^}]*\}', '', text, flags=re.DOTALL)
    text = re.sub(r'^\s*sid\s*=\s*"[^"]*"', '', text, flags=re.MULTILINE)
    text = re.sub(r'\btags\s*=\s*\{[^}]*\}', 'tags = {}', text, flags=re.DOTALL)
    text = re.sub(r'\btags\s*=\s*[A-Za-z0-9_.]+', 'tags = {}', text)
    return text


def to_policy_json(rtype: str, cfg: dict) -> dict | None:
    if rtype == "aws_iam_policy_document":
        statements = []
        for stmt in cfg.get("statement", []):
            if isinstance(stmt, list):
                stmt = stmt[0] if stmt else {}
            if not isinstance(stmt, dict):
                continue
            actions   = stmt.get("actions",   stmt.get("action",   ["*"]))
            resources = stmt.get("resources", stmt.get("resource", ["*"]))
            if isinstance(actions, str):   actions   = [actions]
            if isinstance(resources, str): resources = [resources]
            # Filter out placeholder resources
            resources = [r for r in resources if r != "PLACEHOLDER"] or ["*"]
            actions   = [a for a in actions   if a != "PLACEHOLDER"] or ["*"]
            entry: dict = {
                "Effect":   stmt.get("effect", "Allow"),
                "Action":   actions,
                "Resource": resources,
            }
            principals = stmt.get("principals", stmt.get("principal"))
            if principals:
                if isinstance(principals, list) and principals:
                    p = principals[0] if isinstance(principals[0], dict) else {}
                    entry["Principal"] = {p.get("type", "AWS"): p.get("identifiers", ["*"])}
                elif isinstance(principals, dict):
                    entry["Principal"] = principals
            statements.append(entry)
        if not statements:
            return None
        return {"Version": "2012-10-17", "Statement": statements}

    # aws_iam_policy / aws_iam_role / aws_iam_role_policy
    for key in ("policy", "assume_role_policy"):
        raw = cfg.get(key, "")
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw or raw in ("PLACEHOLDER", "JSONENCODE_PLACEHOLDER", "HEREDOC"):
                continue
            try:
                p = json.loads(raw)
                if p.get("Statement"):
                    return p
            except json.JSONDecodeError:
                pass
        elif isinstance(raw, dict):
            # hcl2 already parsed jsonencode-style into a dict
            if raw.get("Statement"):
                return raw
    return None


def extract_via_hcl2(tf_text: str) -> list[dict]:
    if not HCL2_AVAILABLE:
        return []
    clean = sanitize_for_hcl2(tf_text)
    try:
        parsed = hcl2.loads(clean)
    except Exception as e:
        log.debug("hcl2 parse error: %s", e)
        return []

    results = []
    for top_key in ("resource", "data"):
        for block in parsed.get(top_key, []):
            for rtype, instances in block.items():
                if rtype not in IAM_RESOURCE_TYPES:
                    continue
                for name, config in instances.items():
                    if isinstance(config, list):
                        config = config[0] if config else {}
                    if not isinstance(config, dict):
                        continue
                    policy = to_policy_json(rtype, config)
                    if policy and policy.get("Statement"):
                        results.append({
                            "resource_type": rtype,
                            "resource_name": name,
                            "policy": policy,
                        })
    return results


# ── Main pipeline ─────────────────────────────────────────────────────────────

def extract_all(text: str) -> list[dict]:
    """Try all extraction strategies, return combined unique results."""
    seen_fps: set[str] = set()
    results = []

    for strategy in [extract_via_hcl2, extract_heredoc_policies, extract_jsonencode_policies]:
        for block in strategy(text):
            fp = policy_fingerprint(block["policy"])
            if fp not in seen_fps:
                seen_fps.add(fp)
                results.append(block)

    return results


def convert(scraped_dir: Path, force: bool = False) -> None:
    tf_files = sorted(scraped_dir.glob("raw_*.tf"))
    log.info("Found %d .tf files to convert", len(tf_files))

    if not HCL2_AVAILABLE:
        log.warning("python-hcl2 not installed — using regex fallback only")

    existing_fps: set[str] = set()
    if not force:
        for p in scraped_dir.glob("policy_*.json"):
            existing_fps.add(p.stem.replace("policy_", ""))
        log.info("Found %d existing policy_*.json (use --force to reconvert)", len(existing_fps))

    seen: set[str] = set()
    converted = skipped = failed = 0

    for tf_file in tf_files:
        try:
            text = tf_file.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            log.debug("Read error %s: %s", tf_file.name, e)
            failed += 1
            continue

        blocks = extract_all(text)

        if not blocks:
            skipped += 1
            continue

        for block in blocks:
            fp = policy_fingerprint(block["policy"])
            short = fp[:12]
            if short in seen or short in existing_fps:
                continue
            seen.add(short)
            out = scraped_dir / f"policy_{short}.json"
            entry = {
                "source": tf_file.name,
                "resource_type": block["resource_type"],
                "resource_name": block["resource_name"],
                "policy": block["policy"],
            }
            out.write_text(json.dumps(entry, indent=2), encoding="utf-8")
            converted += 1

    total = len(list(scraped_dir.glob("policy_*.json")))
    log.info("Done — converted: %d, no IAM found: %d, errors: %d", converted, skipped, failed)
    log.info("Total policy_*.json files: %d", total)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert raw .tf files to policy JSON")
    parser.add_argument("--scraped", default="data/scraped_policies")
    parser.add_argument("--force", action="store_true", help="Reconvert all, ignoring existing output")
    args = parser.parse_args()
    convert(Path(args.scraped), force=args.force)
