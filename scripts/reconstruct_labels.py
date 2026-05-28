"""
reconstruct_labels.py — Restore data/train_policies/LABELS.json from policies.xls

Usage:
    python scripts/reconstruct_labels.py --xls policies.xls --policies data/train_policies
    python scripts/reconstruct_labels.py --xls policies.xls --policies data/train_policies --dry-run

What it does:
    1. Reads policies.xls, auto-detects column names
    2. Cross-references against actual .json files in data/train_policies/
    3. Writes a valid LABELS.json (string "label" format that PolicyDataset expects)
    4. Creates a timestamped backup of any existing LABELS.json first
    5. Prints a validation report so you can confirm before committing
"""

import os
import sys
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

# ── Column name candidates ────────────────────────────────────────────────────
# The Excel file might use any of these — we'll auto-detect

FILENAME_COLS  = ["filename", "file", "policy_file", "name", "policy", "policy_name"]
LABEL_COLS     = ["label", "vulnerable", "is_vulnerable", "vulnerability", "class", "target"]
SOURCE_COLS    = ["source", "origin", "description", "notes", "comment"]

TRUTHY  = {"vulnerable", "yes", "true", "1", "v", "vuln", "1.0"}
FALSY   = {"safe", "no", "false", "0", "s", "benign", "0.0"}


# ── Excel reader ──────────────────────────────────────────────────────────────

def load_excel(xls_path: Path) -> pd.DataFrame:
    """Load the first sheet, strip whitespace from headers."""
    log.info("Reading %s …", xls_path)
    df = pd.read_excel(xls_path, sheet_name=0, dtype=str)
    df.columns = [str(c).strip().lower() for c in df.columns]
    df = df.dropna(how="all")
    log.info("  Loaded %d rows, columns: %s", len(df), list(df.columns))
    return df


# ── Column detection ──────────────────────────────────────────────────────────

def detect_column(df: pd.DataFrame, candidates: list[str], role: str) -> str | None:
    for c in candidates:
        if c in df.columns:
            log.info("  Detected %s column: '%s'", role, c)
            return c
    # Fuzzy fallback — substring match
    for col in df.columns:
        for c in candidates:
            if c in col or col in c:
                log.info("  Detected %s column (fuzzy): '%s'", role, col)
                return col
    return None


# ── Label normalisation ───────────────────────────────────────────────────────

def normalise_label(raw: str) -> str | None:
    """Return 'vulnerable' or 'safe', or None if unrecognisable."""
    val = str(raw).strip().lower()
    if val in TRUTHY:
        return "vulnerable"
    if val in FALSY:
        return "safe"
    # Boolean True/False from pandas
    if val == "true":
        return "vulnerable"
    if val == "false":
        return "safe"
    return None


# ── Cross-reference with actual files ────────────────────────────────────────

def existing_policy_files(policies_dir: Path) -> set[str]:
    return {p.name for p in policies_dir.glob("*.json")}


# ── Backup ────────────────────────────────────────────────────────────────────

def backup_existing(labels_path: Path) -> None:
    if labels_path.exists():
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        backup = labels_path.with_name(f"LABELS.backup_{ts}.json")
        shutil.copy2(labels_path, backup)
        log.info("  Backed up existing LABELS.json → %s", backup.name)


# ── Validation report ─────────────────────────────────────────────────────────

def print_report(
    reconstructed: dict,
    on_disk: set[str],
    skipped_unrecognised: list[str],
    skipped_missing_file: list[str],
) -> None:
    labels = [v["label"] for v in reconstructed.values()]
    n_vuln = labels.count("vulnerable")
    n_safe = labels.count("safe")

    print("\n" + "═" * 55)
    print("  RECONSTRUCTION REPORT")
    print("═" * 55)
    print(f"  Policies on disk          : {len(on_disk)}")
    print(f"  Entries reconstructed     : {len(reconstructed)}")
    print(f"    vulnerable              : {n_vuln}")
    print(f"    safe                    : {n_safe}")
    if skipped_unrecognised:
        print(f"  Skipped (bad label value) : {len(skipped_unrecognised)}")
        for s in skipped_unrecognised[:5]:
            print(f"    {s}")
        if len(skipped_unrecognised) > 5:
            print(f"    … and {len(skipped_unrecognised)-5} more")
    if skipped_missing_file:
        print(f"  Skipped (file not on disk): {len(skipped_missing_file)}")
        for s in skipped_missing_file[:5]:
            print(f"    {s}")
        if len(skipped_missing_file) > 5:
            print(f"    … and {len(skipped_missing_file)-5} more")

    # Policies on disk with no Excel entry
    covered = set(reconstructed.keys())
    unlabelled = on_disk - covered
    if unlabelled:
        print(f"\n  ⚠  {len(unlabelled)} on-disk policies have NO entry in the Excel file:")
        for f in sorted(unlabelled)[:10]:
            print(f"    {f}")
        if len(unlabelled) > 10:
            print(f"    … and {len(unlabelled)-10} more")

    # Class balance warning
    if len(reconstructed) > 0:
        ratio = n_vuln / len(reconstructed)
        if ratio < 0.2 or ratio > 0.8:
            print(f"\n  ⚠  Class imbalance: {ratio:.0%} vulnerable. Consider oversampling.")

    print("═" * 55 + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def reconstruct(xls_path: Path, policies_dir: Path, dry_run: bool) -> dict:
    df = load_excel(xls_path)

    # Detect columns
    fname_col  = detect_column(df, FILENAME_COLS,  "filename")
    label_col  = detect_column(df, LABEL_COLS,     "label")
    source_col = detect_column(df, SOURCE_COLS,    "source")

    if fname_col is None:
        log.error(
            "Could not find a filename column. Available: %s\n"
            "Add --fname-col <name> to specify manually.",
            list(df.columns),
        )
        sys.exit(1)

    if label_col is None:
        log.error(
            "Could not find a label column. Available: %s\n"
            "Add --label-col <name> to specify manually.",
            list(df.columns),
        )
        sys.exit(1)

    on_disk = existing_policy_files(policies_dir)
    log.info("Found %d .json files in %s", len(on_disk), policies_dir)

    reconstructed: dict        = {}
    skipped_unrecognised: list = []
    skipped_missing_file: list = []

    for _, row in df.iterrows():
        raw_fname = str(row[fname_col]).strip()
        # Normalise filename: ensure it ends with .json
        if not raw_fname.lower().endswith(".json"):
            raw_fname += ".json"

        raw_label = str(row.get(label_col, "")).strip()
        label = normalise_label(raw_label)

        if label is None:
            skipped_unrecognised.append(f"{raw_fname}: unrecognised label '{raw_label}'")
            continue

        if raw_fname not in on_disk:
            skipped_missing_file.append(raw_fname)
            continue

        entry: dict = {
            "label": label,
            "source": str(row[source_col]).strip() if source_col and source_col in row else "policies.xls",
        }
        # Preserve any extra metadata columns
        extra_cols = [c for c in df.columns if c not in (fname_col, label_col, source_col or "")]
        for c in extra_cols:
            val = str(row.get(c, "")).strip()
            if val and val.lower() not in ("nan", "none", ""):
                entry[c] = val

        reconstructed[raw_fname] = entry

    print_report(reconstructed, on_disk, skipped_unrecognised, skipped_missing_file)
    return reconstructed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruct LABELS.json from policies.xls"
    )
    parser.add_argument("--xls",         required=True, help="Path to policies.xls")
    parser.add_argument("--policies",    default="data/train_policies",
                                         help="Directory containing policy .json files")
    parser.add_argument("--out",         default=None,
                                         help="Output LABELS.json path (default: <policies>/LABELS.json)")
    parser.add_argument("--fname-col",   default=None, help="Override filename column name")
    parser.add_argument("--label-col",   default=None, help="Override label column name")
    parser.add_argument("--dry-run",     action="store_true",
                                         help="Print report but do NOT write LABELS.json")
    args = parser.parse_args()

    xls_path     = Path(args.xls)
    policies_dir = Path(args.policies)
    out_path     = Path(args.out) if args.out else policies_dir / "LABELS.json"

    if not xls_path.exists():
        log.error("Excel file not found: %s", xls_path)
        sys.exit(1)
    if not policies_dir.exists():
        log.error("Policies directory not found: %s", policies_dir)
        sys.exit(1)

    # Allow manual column overrides
    if args.fname_col:
        FILENAME_COLS.insert(0, args.fname_col.lower())
    if args.label_col:
        LABEL_COLS.insert(0, args.label_col.lower())

    reconstructed = reconstruct(xls_path, policies_dir, args.dry_run)

    if args.dry_run:
        log.info("Dry run — nothing written.")
        return

    if not reconstructed:
        log.error("Nothing to write — check your Excel file and column names.")
        sys.exit(1)

    backup_existing(out_path)

    # Write in the format PolicyDataset._load_labels_payload expects:
    # {"total_policies": N, "labels": [{"filename": ..., "label": ..., ...}, ...]}
    entries = [{"filename": fname, **meta} for fname, meta in reconstructed.items()]
    output = {"total_policies": len(entries), "labels": entries}

    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    log.info("✓ Wrote %d entries to %s", len(entries), out_path)
    log.info("Next step: python scripts/train.py  (or however you invoke training)")


if __name__ == "__main__":
    main()
