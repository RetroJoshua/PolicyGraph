#!/usr/bin/env python3
"""
Merge original and newly labeled IAM policy datasets.

Takes:
  - Original 108 policies from data/raw/samples/
  - Newly labeled policies from data/labeled_policies/
Produces:
  - Combined dataset in data/raw/samples_expanded/
  - Merged LABELS.json
  - Merged policies_labeled.csv
  - Deduplication by policy content hash
  - Statistics report

Usage:
    python scripts/merge_labeled_datasets.py \
        --original data/raw/samples \
        --new data/labeled_policies \
        --output data/raw/samples_expanded

    # Dry run (show stats without writing)
    python scripts/merge_labeled_datasets.py \
        --original data/raw/samples --new data/labeled_policies \
        --output data/raw/samples_expanded --dry-run
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import argparse
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def policy_content_hash(filepath: Path) -> str:
    """Hash the normalized JSON content of a policy file for deduplication."""
    try:
        with filepath.open("r") as f:
            data = json.load(f)
        # Remove metadata keys that aren't part of the actual policy
        for key in ("_source", "_note", "_original_filename", "_raw_source", "_parse_note"):
            data.pop(key, None)
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()
    except (json.JSONDecodeError, Exception):
        # If can't parse as JSON, hash the raw content
        content = filepath.read_text(errors="replace")
        return hashlib.sha256(content.encode()).hexdigest()


def load_labels_json(labels_path: Path) -> Dict[str, Any]:
    """Load a LABELS.json file."""
    if not labels_path.exists():
        return {"labels": []}
    with labels_path.open("r") as f:
        return json.load(f)


def load_labels_csv(csv_path: Path) -> List[Dict[str, str]]:
    """Load a policies_labeled.csv file."""
    if not csv_path.exists():
        return []
    rows = []
    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def merge_datasets(
    original_dir: Path,
    new_dir: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Merge original and new labeled datasets.

    Returns a statistics dict.
    """
    stats = {
        "original_count": 0,
        "new_count": 0,
        "duplicates_removed": 0,
        "total_merged": 0,
        "original_vulnerable": 0,
        "original_secure": 0,
        "new_vulnerable": 0,
        "new_secure": 0,
        "merged_vulnerable": 0,
        "merged_secure": 0,
    }

    # ── Load original dataset ──────────────────────────────────────────────

    original_labels_json = load_labels_json(original_dir / "LABELS.json")
    original_labels_csv = load_labels_csv(original_dir.parent / "policies_labeled.csv")

    # Build lookup by filename
    original_label_map: Dict[str, Dict[str, Any]] = {}
    for entry in original_labels_json.get("labels", []):
        original_label_map[entry["filename"]] = entry
    for row in original_labels_csv:
        if row["filename"] not in original_label_map:
            original_label_map[row["filename"]] = row

    # Collect original policy files and hashes
    seen_hashes: Set[str] = set()
    original_files: List[Path] = []

    for f in sorted(original_dir.glob("*.json")):
        if f.name in ("LABELS.json", "README.md"):
            continue
        h = policy_content_hash(f)
        seen_hashes.add(h)
        original_files.append(f)
        label = original_label_map.get(f.name, {}).get("label", "unknown")
        if label == "vulnerable":
            stats["original_vulnerable"] += 1
        elif label == "secure":
            stats["original_secure"] += 1

    stats["original_count"] = len(original_files)
    log.info("Original dataset: %d policies (%d vulnerable, %d secure)",
             stats["original_count"], stats["original_vulnerable"], stats["original_secure"])

    # ── Load new labeled dataset ───────────────────────────────────────────

    new_policies_dir = new_dir / "policies"
    if not new_policies_dir.exists():
        new_policies_dir = new_dir  # Fallback

    new_labels_json = load_labels_json(new_dir / "LABELS.json")
    new_labels_csv = load_labels_csv(new_dir / "policies_labeled.csv")

    new_label_map: Dict[str, Dict[str, Any]] = {}
    for entry in new_labels_json.get("labels", []):
        new_label_map[entry["filename"]] = entry
    for row in new_labels_csv:
        if row["filename"] not in new_label_map:
            new_label_map[row["filename"]] = row

    new_files: List[Path] = []
    duplicates: List[str] = []

    for f in sorted(new_policies_dir.glob("*.json")):
        if f.name in ("LABELS.json", "README.md", "model_scores.json", "labeling_state.json"):
            continue
        h = policy_content_hash(f)
        if h in seen_hashes:
            duplicates.append(f.name)
            stats["duplicates_removed"] += 1
            continue
        seen_hashes.add(h)
        new_files.append(f)
        label = new_label_map.get(f.name, {}).get("label", "unknown")
        if label == "vulnerable":
            stats["new_vulnerable"] += 1
        elif label == "secure":
            stats["new_secure"] += 1

    stats["new_count"] = len(new_files) + len(duplicates)
    log.info("New dataset: %d policies (%d vulnerable, %d secure, %d duplicates)",
             stats["new_count"], stats["new_vulnerable"], stats["new_secure"],
             stats["duplicates_removed"])

    # ── Merge ──────────────────────────────────────────────────────────────

    total = len(original_files) + len(new_files)
    stats["total_merged"] = total
    stats["merged_vulnerable"] = stats["original_vulnerable"] + stats["new_vulnerable"]
    stats["merged_secure"] = stats["original_secure"] + stats["new_secure"]

    log.info("Merged dataset: %d policies (%d vulnerable, %d secure)",
             total, stats["merged_vulnerable"], stats["merged_secure"])

    if duplicates:
        log.info("Duplicates removed: %s", ", ".join(duplicates[:5]))
        if len(duplicates) > 5:
            log.info("  ... and %d more", len(duplicates) - 5)

    if dry_run:
        log.info("Dry run — no files written.")
        return stats

    # ── Write merged dataset ───────────────────────────────────────────────

    output_dir.mkdir(parents=True, exist_ok=True)

    # Copy original files
    for f in original_files:
        shutil.copy2(f, output_dir / f.name)

    # Copy README if exists
    readme = original_dir / "README.md"
    if readme.exists():
        shutil.copy2(readme, output_dir / "README.md")

    # Copy new files
    for f in new_files:
        shutil.copy2(f, output_dir / f.name)

    # ── Merge LABELS.json ──────────────────────────────────────────────────

    merged_labels = original_labels_json.get("labels", []).copy()

    # Add new labels (for non-duplicate files only)
    new_file_names = {f.name for f in new_files}
    for entry in new_labels_json.get("labels", []):
        if entry["filename"] in new_file_names:
            merged_labels.append(entry)

    # Compute severity distribution
    severity_dist: Dict[str, int] = {}
    for entry in merged_labels:
        sev = entry.get("severity", "unknown")
        severity_dist[sev] = severity_dist.get(sev, 0) + 1

    merged_labels_json = {
        "description": "Ground-truth labels for PolicyGraph IAM policy samples (expanded dataset)",
        "version": "2.0.0",
        "total_policies": total,
        "vulnerable_count": stats["merged_vulnerable"],
        "secure_count": stats["merged_secure"],
        "severity_distribution": severity_dist,
        "original_count": stats["original_count"],
        "new_count": len(new_files),
        "duplicates_removed": stats["duplicates_removed"],
        "labels": merged_labels,
    }

    with (output_dir / "LABELS.json").open("w") as f:
        json.dump(merged_labels_json, f, indent=2)

    # ── Merge policies_labeled.csv ─────────────────────────────────────────

    all_csv_rows = original_labels_csv.copy()
    for row in new_labels_csv:
        if row.get("filename") in new_file_names:
            all_csv_rows.append(row)

    if all_csv_rows:
        fieldnames = all_csv_rows[0].keys()
        csv_path = output_dir.parent / "policies_labeled_expanded.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_csv_rows)
        log.info("Wrote %s (%d rows)", csv_path, len(all_csv_rows))

    log.info("Merged dataset written to %s", output_dir)

    # ── Print summary ──────────────────────────────────────────────────────

    print("\n" + "=" * 60)
    print("  Dataset Merge Summary")
    print("=" * 60)
    print(f"  Original:           {stats['original_count']:>6} policies")
    print(f"    Vulnerable:       {stats['original_vulnerable']:>6}")
    print(f"    Secure:           {stats['original_secure']:>6}")
    print(f"  New (labeled):      {stats['new_count']:>6} policies")
    print(f"    Vulnerable:       {stats['new_vulnerable']:>6}")
    print(f"    Secure:           {stats['new_secure']:>6}")
    print(f"    Duplicates:       {stats['duplicates_removed']:>6} (removed)")
    print(f"  ─────────────────────────────────")
    print(f"  Total merged:       {stats['total_merged']:>6} policies")
    print(f"    Vulnerable:       {stats['merged_vulnerable']:>6}")
    print(f"    Secure:           {stats['merged_secure']:>6}")
    print("=" * 60)
    print(f"  Output: {output_dir}")
    print()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Merge original and newly labeled IAM policy datasets"
    )
    parser.add_argument("--original", type=str, default="data/raw/samples",
                        help="Original dataset directory")
    parser.add_argument("--new", type=str, default="data/labeled_policies",
                        help="Newly labeled dataset directory")
    parser.add_argument("--output", type=str, default="data/raw/samples_expanded",
                        help="Output directory for merged dataset")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show stats without writing files")
    args = parser.parse_args()

    original = PROJECT_ROOT / args.original
    new = PROJECT_ROOT / args.new
    output = PROJECT_ROOT / args.output

    if not original.exists():
        log.error("Original dataset not found: %s", original)
        sys.exit(1)
    if not new.exists():
        log.error("New dataset not found: %s", new)
        log.info("Run the labeling tool first:")
        log.info("  python scripts/label_scraped_policies.py --scraped data/scraped_policies --out data/labeled_policies --model checkpoints/long/best_model.pt")
        sys.exit(1)

    merge_datasets(original, new, output, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
