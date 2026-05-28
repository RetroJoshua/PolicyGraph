import json
import pandas as pd
from pathlib import Path

# Try to find policies.xls
possible_paths = [
    Path('data/raw/samples/policies.xls'),
    Path('~/Uploads/policies.xls').expanduser(),
    Path('data/raw/policies.xls'),
]

policies_xls = None
for path in possible_paths:
    if path.exists():
        policies_xls = path
        print(f"✓ Found policies.xls at: {path}")
        break

if not policies_xls:
    print("❌ Could not find policies.xls!")
    print("Please provide the path to your original policies.xls file")
    exit(1)

# Read Excel
df = pd.read_excel(policies_xls)
print(f"\n📊 Columns in Excel: {list(df.columns)}")
print(f"📊 Total rows: {len(df)}")

# Show first few rows to understand structure
print("\n📋 First 5 rows:")
print(df.head())

# Reconstruct LABELS.json
labels = []
for _, row in df.iterrows():
    entry = {
        "filename": row.get('filename', row.get('policy_file', '')),
        "vulnerable": bool(row.get('vulnerable', False)),
        "severity": row.get('severity', 'unknown'),
        "vulnerability_type": row.get('vulnerability_type', row.get('type', 'Other')),
    }
    labels.append(entry)

# Save
output = {"labels": labels}
labels_file = Path('data/raw/samples/LABELS.json')
labels_file.write_text(json.dumps(output, indent=2), encoding='utf-8')

print(f"\n✓ Saved {len(labels)} labels to {labels_file}")
print(f"  Vulnerable: {sum(1 for e in labels if e['vulnerable'])}")
print(f"  Secure: {sum(1 for e in labels if not e['vulnerable'])}")
