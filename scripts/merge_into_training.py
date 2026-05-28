"""
merge_into_training.py — Merge labeled scraped policies into data/raw/samples/

Usage:
    python scripts/merge_into_training.py --dry-run
    python scripts/merge_into_training.py
"""

import json
import shutil
import argparse
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
SCRAPED_DIR   = PROJECT_ROOT / "data" / "scraped_policies"
LABELED_DIR   = PROJECT_ROOT / "data" / "labeled_policies"
SAMPLES_DIR   = PROJECT_ROOT / "data" / "raw" / "samples"
TRAIN_LABELS  = SAMPLES_DIR / "LABELS.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main(dry_run: bool) -> None:
    # ── Load existing training labels ────────────────────────────────────────
    if not TRAIN_LABELS.exists():
        log.error("Training LABELS.json not found: %s", TRAIN_LABELS)
        return

    train_data = load_json(TRAIN_LABELS)
    existing: dict[str, dict] = {
        e["filename"]: e for e in train_data.get("labels", [])
    }
    log.info("Existing training samples: %d", len(existing))

    # ── Load labeled scraped policies ────────────────────────────────────────
    labeled_labels_path = LABELED_DIR / "LABELS.json"
    if not labeled_labels_path.exists():
        log.error("Labeled LABELS.json not found: %s", labeled_labels_path)
        return

    labeled_data = load_json(labeled_labels_path)
    labeled_entries = labeled_data.get("labels", [])
    log.info("Labeled scraped entries: %d", len(labeled_entries))

    # ── Merge ────────────────────────────────────────────────────────────────
    added = skipped_dup = skipped_no_file = 0

    for entry in labeled_entries:
        src_filename = entry.get("filename", "")
        label        = entry.get("label", "")

        if label not in ("vulnerable", "safe", "secure"):
            continue

        # Normalize label
        if label == "secure":
            label = "safe"
            entry = {**entry, "label": "safe"}

        # Find the source policy JSON in labeled_policies/policies/
        src_path = LABELED_DIR / "policies" / src_filename
        if not src_path.exists():
            # Try scraped_policies directly
            src_path = SCRAPED_DIR / src_filename
        if not src_path.exists():
            log.debug("Source file not found: %s", src_filename)
            skipped_no_file += 1
            continue

        # Generate destination filename
        prefix  = "scraped_vuln" if label == "vulnerable" else "scraped_safe"
        dst_name = f"{prefix}_{src_filename}"
        dst_path = SAMPLES_DIR / dst_name

        # Skip duplicates
        if dst_name in existing:
            skipped_dup += 1
            continue

        # Read and validate policy JSON
        try:
            content = json.loads(src_path.read_text(encoding="utf-8"))
            # If it's wrapped (has "policy" key), unwrap it
            policy_json = content.get("policy", content)
            if not isinstance(policy_json, dict) or "Statement" not in policy_json:
                log.debug("No Statement in %s — skipping", src_filename)
                skipped_no_file += 1
                continue
        except Exception as e:
            log.debug("Could not read %s: %s", src_filename, e)
            skipped_no_file += 1
            continue

        if not dry_run:
            # Write policy JSON to samples dir
            dst_path.write_text(
                json.dumps(policy_json, indent=2), encoding="utf-8"
            )

        # Add to existing labels
        new_entry = {
            "filename": dst_name,
            "label": label,
            "severity": entry.get("severity", "low"),
            "vulnerability_type": entry.get("vulnerability_type",
                                  entry.get("vuln_type", "none")),
            "risk_score": entry.get("risk_score", 1 if label == "vulnerable" else 0),
            "source": "scraped_terraform",
            "attack_paths": entry.get("attack_paths", []),
            "remediation": entry.get("remediation", ""),
        }
        existing[dst_name] = new_entry
        added += 1

    # ── Write updated LABELS.json ────────────────────────────────────────────
    entries   = list(existing.values())
    vuln_count  = sum(1 for e in entries if e.get("label") == "vulnerable")
    safe_count  = sum(1 for e in entries if e.get("label") in ("safe", "secure"))

    print(f"\n{'═'*55}")
    print(f"  MERGE RESULTS {'(DRY RUN)' if dry_run else ''}")
    print(f"{'═'*55}")
    print(f"  Added        : {added}")
    print(f"  Skipped (dup): {skipped_dup}")
    print(f"  Skipped (missing file): {skipped_no_file}")
    print(f"{'─'*55}")
    print(f"  Total after merge : {len(entries)}")
    print(f"    vulnerable       : {vuln_count}")
    print(f"    safe             : {safe_count}")
    print(f"    imbalance ratio  : {vuln_count/len(entries):.1%} vulnerable")
    print(f"{'═'*55}\n")

    if dry_run:
        log.info("Dry run — nothing written.")
        return

    if added == 0:
        log.info("Nothing new to add.")
        return

    output = {"total_policies": len(entries), "labels": entries}
    TRAIN_LABELS.write_text(json.dumps(output, indent=2), encoding="utf-8")
    log.info("Updated %s", TRAIN_LABELS)
    log.info("Next step: policygraph train")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge labeled scraped policies into training data")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
