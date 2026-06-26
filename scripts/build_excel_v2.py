#!/usr/bin/env python3
"""
Build a maximally-compatible Excel file from the CSV backup using xlsxwriter.

The earlier openpyxl-generated workbook failed to open in Excel mobile
("file format or file extension is not valid"). This rebuilds the workbook with
the xlsxwriter engine, which produces a more standard OOXML package
(shared strings, explicit styles) that opens cleanly in Excel mobile, Excel
desktop, Excel Online, Google Sheets and LibreOffice.

Source of truth: the CSV backup (data/scraped_policies.csv), which is known good.

Usage:
    python scripts/build_excel_v2.py \
        --csv data/scraped_policies.csv \
        --xlsx-out data/scraped_policies_v2.xlsx
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

# Control characters illegal in OOXML / xlsx (all < 0x20 except TAB, LF, CR,
# plus DEL 0x7f). Their presence makes strict readers reject the file.
ILLEGAL_XML_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

EXCEL_CELL_LIMIT = 32767

EXPECTED_COLUMNS = [
    "filename",
    "source_repo",
    "source_path",
    "content",
    "content_length",
    "vulnerable",
    "confidence",
    "notes",
    "checkov_findings",
    "scraped_date",
]

COLUMN_WIDTHS = {
    "filename": 30,
    "source_repo": 35,
    "source_path": 40,
    "content": 80,
    "content_length": 15,
    "vulnerable": 12,
    "confidence": 12,
    "notes": 40,
    "checkov_findings": 50,
    "scraped_date": 20,
}

# Columns that hold long / free-form text and should be stored as text.
TEXT_COLUMNS = {"content", "notes", "checkov_findings", "source_path", "filename",
                "source_repo", "scraped_date"}


def clean_text(value):
    """Sanitize a single value for strict spreadsheet readers."""
    if value is None:
        return ""
    if not isinstance(value, str):
        return value
    cleaned = ILLEGAL_XML_CHARS.sub("", value)
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    if len(cleaned) > EXCEL_CELL_LIMIT:
        cleaned = cleaned[: EXCEL_CELL_LIMIT - 20] + "\n... [TRUNCATED]"
    return cleaned


def load_csv(csv_path: Path) -> pd.DataFrame:
    # keep_default_na=False so empty label cells stay as "" rather than NaN,
    # which keeps the written workbook free of stray "nan" text.
    df = pd.read_csv(csv_path, keep_default_na=False, dtype=str)
    # Ensure all expected columns are present and ordered.
    for col in EXPECTED_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    ordered = [c for c in EXPECTED_COLUMNS if c in df.columns]
    ordered += [c for c in df.columns if c not in EXPECTED_COLUMNS]
    df = df[ordered]

    # Sanitize every cell.
    for col in df.columns:
        df[col] = df[col].map(clean_text)

    # Recompute content_length as a real integer from sanitized content.
    if "content" in df.columns:
        df["content_length"] = df["content"].map(lambda v: len(v) if isinstance(v, str) else 0)
    return df


def write_xlsx(df: pd.DataFrame, out_path: Path):
    import xlsxwriter

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # constant_memory=False so column widths/format work; strings_to_* off so we
    # never let xlsxwriter reinterpret content as urls/numbers/formulas.
    workbook = xlsxwriter.Workbook(
        str(out_path),
        {
            "strings_to_urls": False,
            "strings_to_numbers": False,
            "strings_to_formulas": False,
            "in_memory": True,
        },
    )
    ws = workbook.add_worksheet("IAM_Policies")

    header_fmt = workbook.add_format({"bold": True, "bg_color": "#D9E1F2", "border": 1})
    text_fmt = workbook.add_format({"text_wrap": False})
    int_fmt = workbook.add_format({"num_format": "0"})

    # Header row.
    for col_idx, col_name in enumerate(df.columns):
        ws.write_string(0, col_idx, str(col_name), header_fmt)
        ws.set_column(col_idx, col_idx, COLUMN_WIDTHS.get(col_name, 20))

    # Data rows.
    for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
        for col_idx, col_name in enumerate(df.columns):
            value = row[col_name]
            if col_name == "content_length":
                try:
                    ws.write_number(row_idx, col_idx, int(value), int_fmt)
                except (ValueError, TypeError):
                    ws.write_string(row_idx, col_idx, str(value), text_fmt)
            else:
                # Force everything else to be written as an explicit string.
                ws.write_string(row_idx, col_idx, "" if value is None else str(value), text_fmt)

    ws.freeze_panes(1, 0)  # freeze header row
    workbook.close()


def validate_xlsx(path: Path, expected_rows: int) -> bool:
    """Read the workbook back and check the OOXML package structure."""
    import zipfile
    import xml.dom.minidom as minidom

    ok = True

    # 1. pandas read-back.
    try:
        df = pd.read_excel(path, sheet_name="IAM_Policies", engine="openpyxl")
        rows_ok = df.shape[0] == expected_rows
        print(f"   {'✓' if rows_ok else '✗'} pandas read-back: {df.shape[0]} rows "
              f"(expected {expected_rows}), {df.shape[1]} cols")
        ok = ok and rows_ok
    except Exception as e:  # noqa: BLE001
        print(f"   ✗ pandas read-back FAILED: {type(e).__name__}: {e}")
        ok = False

    # 2. Required OOXML package parts present.
    required = {
        "[Content_Types].xml",
        "_rels/.rels",
        "xl/workbook.xml",
        "xl/_rels/workbook.xml.rels",
        "xl/worksheets/sheet1.xml",
    }
    try:
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            missing = required - names
            if missing:
                print(f"   ✗ missing OOXML parts: {missing}")
                ok = False
            else:
                print(f"   ✓ all required OOXML parts present "
                      f"({len(names)} parts, sharedStrings={'xl/sharedStrings.xml' in names})")

            # 3. Every XML part is well-formed.
            bad = []
            for n in names:
                if n.endswith(".xml") or n.endswith(".rels"):
                    try:
                        minidom.parseString(z.read(n))
                    except Exception as e:  # noqa: BLE001
                        bad.append((n, str(e)[:60]))
            if bad:
                print(f"   ✗ malformed XML parts: {bad}")
                ok = False
            else:
                print("   ✓ all XML parts well-formed")
    except Exception as e:  # noqa: BLE001
        print(f"   ✗ zip inspection FAILED: {type(e).__name__}: {e}")
        ok = False

    return ok


def main():
    parser = argparse.ArgumentParser(description="Build Excel-compatible xlsx via xlsxwriter")
    parser.add_argument("--csv", default="data/scraped_policies.csv", help="Source CSV")
    parser.add_argument("--xlsx-out", default="data/scraped_policies_v2.xlsx",
                        help="Output xlsx path")
    parser.add_argument("--rewrite-csv", action="store_true",
                        help="Also rewrite a sanitized copy of the CSV next to the xlsx")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    xlsx_out = Path(args.xlsx_out)

    if not csv_path.exists():
        print(f"❌ CSV not found: {csv_path}")
        sys.exit(1)

    print("=" * 70)
    print("Build maximally-compatible Excel (xlsxwriter)")
    print("=" * 70)

    print(f"\n[1/4] Loading CSV: {csv_path} ({csv_path.stat().st_size:,} bytes)")
    df = load_csv(csv_path)
    print(f"   loaded {df.shape[0]} rows x {df.shape[1]} cols")

    print(f"\n[2/4] Writing xlsx via xlsxwriter: {xlsx_out}")
    write_xlsx(df, xlsx_out)
    size = xlsx_out.stat().st_size
    print(f"   wrote {size:,} bytes")
    if size < 5000:
        print("   ⚠️  file is suspiciously small")

    if args.rewrite_csv:
        print(f"\n[3/4] Rewriting sanitized CSV: {csv_path}")
        df.to_csv(csv_path, index=False, encoding="utf-8")
        print(f"   wrote {csv_path.stat().st_size:,} bytes")
    else:
        print("\n[3/4] Skipping CSV rewrite (use --rewrite-csv to enable)")

    print(f"\n[4/4] Validating {xlsx_out} ...")
    ok = validate_xlsx(xlsx_out, df.shape[0])

    print("\n" + "=" * 70)
    if ok:
        print("✓ SUCCESS — workbook is valid and standards-compliant.")
    else:
        print("⚠️  Validation reported issues (see above).")
        sys.exit(2)
    print("=" * 70)


if __name__ == "__main__":
    main()
