"""
Scrape anonymized IAM policies from public Terraform configs on GitHub.

Requirements:
    pip install requests python-hcl2 tqdm

Usage:
    export GITHUB_TOKEN=your_token_here   # optional but strongly recommended
    python scrape_iam_terraform.py --pages 10 --out ./scraped_policies
"""

import os
import re
import json
import time
import hashlib
import argparse
import logging
from pathlib import Path

import requests
try:
    import hcl2
except ImportError:
    hcl2 = None

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── GitHub API ──────────────────────────────────────────────────────────────

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    **({"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}

SEARCH_QUERIES = [
    "aws_iam_policy_document extension:tf",
    "aws_iam_role_policy extension:tf",
    "iam:PassRole extension:tf",
    "aws_iam_policy extension:tf resource",
]


def search_github(query: str, page: int = 1) -> list[dict]:
    """Return a page of code search results."""
    url = "https://api.github.com/search/code"
    params = {"q": query, "per_page": 30, "page": page}
    resp = requests.get(url, headers=HEADERS, params=params, timeout=15)
    if resp.status_code == 403:
        reset = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
        wait = max(reset - int(time.time()), 5)
        log.warning("Rate limited — waiting %ds", wait)
        time.sleep(wait)
        return search_github(query, page)
    resp.raise_for_status()
    return resp.json().get("items", [])


def fetch_raw(item: dict) -> str | None:
    """Download raw file content for a search result item."""
    raw_url = (
        item["html_url"]
        .replace("github.com", "raw.githubusercontent.com")
        .replace("/blob/", "/")
    )
    try:
        resp = requests.get(raw_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        log.debug("Failed to fetch %s: %s", raw_url, e)
        return None


# ── Anonymization ────────────────────────────────────────────────────────────

# Patterns to redact
_PATTERNS = [
    # AWS Account IDs (12-digit numbers)
    (r"\b\d{12}\b", "ACCOUNT_ID"),
    # ARNs — preserve the service/resource type, redact the identity parts
    (r"arn:aws:[a-z0-9\-]+:[a-z0-9\-]*:\d{12}:([^\"'\s,]+)", r"arn:aws:\1:REDACTED"),
    # Typical domain names / emails
    (r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", "EMAIL_REDACTED"),
    # Generic hostnames that look like org-specific endpoints
    (r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s\"']*", "URL_REDACTED"),
]

_COMPILED = [(re.compile(p), r) for p, r in _PATTERNS]


def anonymize(text: str) -> str:
    for pattern, replacement in _COMPILED:
        text = pattern.sub(replacement, text)
    return text


# ── IAM Block Extraction ─────────────────────────────────────────────────────

IAM_RESOURCE_TYPES = {
    "aws_iam_policy",
    "aws_iam_policy_document",
    "aws_iam_role",
    "aws_iam_role_policy",
    "aws_iam_user_policy",
    "aws_iam_group_policy",
}


def extract_iam_blocks_regex(tf_text: str) -> list[str]:
    """
    Regex-based fallback: pull out resource/data blocks for IAM types.
    Returns raw HCL text snippets.
    """
    blocks = []
    pattern = re.compile(
        r'(?:resource|data)\s+"(' + "|".join(IAM_RESOURCE_TYPES) + r')"\s+"[^"]+"\s+\{',
        re.MULTILINE,
    )
    for match in pattern.finditer(tf_text):
        start = match.start()
        depth = 0
        i = start
        for i, ch in enumerate(tf_text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    blocks.append(tf_text[start : i + 1])
                    break
    return blocks


def extract_iam_policies_hcl2(tf_text: str) -> list[dict]:
    """
    Parse with hcl2 and return IAM-related resource/data dicts.
    Falls back gracefully on parse errors.
    """
    if hcl2 is None:
        return []
    try:
        parsed = hcl2.loads(tf_text)
    except Exception:
        return []

    results = []
    for top_key in ("resource", "data"):
        for block in parsed.get(top_key, []):
            for rtype, instances in block.items():
                if rtype in IAM_RESOURCE_TYPES:
                    for name, config in instances.items():
                        results.append(
                            {"type": rtype, "name": name, "config": config}
                        )
    return results


def to_iam_policy_json(block: dict) -> dict | None:
    """
    Best-effort conversion of a parsed hcl2 block into an IAM policy JSON dict
    similar to what PolicyGraph already consumes.
    """
    rtype = block.get("type", "")
    cfg = block.get("config", {})

    # aws_iam_policy_document → reconstruct Statement list
    if rtype == "aws_iam_policy_document":
        statements = []
        for stmt in cfg.get("statement", []):
            entry = {
                "Effect": stmt.get("effect", "Allow"),
                "Action": stmt.get("actions", stmt.get("action", ["*"])),
                "Resource": stmt.get("resources", stmt.get("resource", ["*"])),
            }
            if "principals" in stmt:
                entry["Principal"] = stmt["principals"]
            if "condition" in stmt:
                entry["Condition"] = stmt["condition"]
            statements.append(entry)
        return {"Version": "2012-10-17", "Statement": statements}

    # aws_iam_policy / role_policy → inline JSON string
    for key in ("policy", "assume_role_policy"):
        raw = cfg.get(key, "")
        if isinstance(raw, str):
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                pass
        elif isinstance(raw, dict):
            return raw

    return None


# ── Deduplication ────────────────────────────────────────────────────────────

def policy_fingerprint(policy: dict) -> str:
    """Stable hash of sorted JSON — ignores whitespace differences."""
    canonical = json.dumps(policy, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def scrape(pages: int, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    total_saved = 0

    for query in SEARCH_QUERIES:
        log.info("Query: %s", query)
        for page in range(1, pages + 1):
            log.info("  Page %d/%d", page, pages)
            try:
                items = search_github(query, page)
            except Exception as e:
                log.error("Search failed: %s", e)
                break

            if not items:
                break

            for item in items:
                raw = fetch_raw(item)
                if not raw:
                    continue

                raw_anon = anonymize(raw)

                # Try hcl2 first, fall back to regex
                blocks = extract_iam_policies_hcl2(raw_anon)
                policies = []

                if blocks:
                    for block in blocks:
                        p = to_iam_policy_json(block)
                        if p and p.get("Statement"):
                            policies.append(
                                {
                                    "source": item["html_url"],
                                    "resource_type": block["type"],
                                    "resource_name": block["name"],
                                    "policy": p,
                                }
                            )
                else:
                    # Regex fallback — save raw HCL snippets
                    snippets = extract_iam_blocks_regex(raw_anon)
                    for snippet in snippets:
                        fp = hashlib.sha256(snippet.encode()).hexdigest()
                        if fp in seen:
                            continue
                        seen.add(fp)
                        out_file = out_dir / f"raw_{fp[:12]}.tf"
                        out_file.write_text(snippet, encoding='utf-8')
                        total_saved += 1

                for entry in policies:
                    fp = policy_fingerprint(entry["policy"])
                    if fp in seen:
                        continue
                    seen.add(fp)
                    out_file = out_dir / f"policy_{fp[:12]}.json"
                    out_file.write_text(json.dumps(entry, indent=2), encoding='utf-8')
                    total_saved += 1

            # Respect secondary rate limit
            time.sleep(2)

        log.info("Saved so far: %d", total_saved)

    log.info("Done. Total unique policies/blocks saved: %d", total_saved)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape anonymized IAM policies from GitHub Terraform configs")
    parser.add_argument("--pages", type=int, default=5, help="Pages per query (30 results/page)")
    parser.add_argument("--out", type=str, default="./scraped_policies", help="Output directory")
    args = parser.parse_args()

    scrape(pages=args.pages, out_dir=Path(args.out))
