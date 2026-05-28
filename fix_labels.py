import json
import csv
from pathlib import Path

samples_dir = Path('data/raw/samples')
labels_file = samples_dir / 'LABELS.json'
csv_file = Path('data/raw/policies_labeled.csv')

# Get all policy JSON files (excluding LABELS.json and README.md)
all_policies = [f for f in samples_dir.glob('*.json') if f.name != 'LABELS.json']

print(f"Found {len(all_policies)} policy files")

# Load existing labels from CSV (the original 108)
old_labels = {}
if csv_file.exists():
    with csv_file.open('r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fname = row['file']
            old_labels[fname] = {
                "vulnerable": row['vulnerable'].lower() == 'true',
                "severity": row['severity'],
                "vulnerability_types": [row['category']] if row['category'] != 'Other' else [],
                "risk_score": 7.0 if row['vulnerable'].lower() == 'true' else 2.0,
                "description": f"Original labeled: {row['category']}",
                "attack_paths": [],
                "remediation": "Review and restrict permissions" if row['vulnerable'].lower() == 'true' else "",
                "source": "original_dataset"
            }
    print(f"Loaded {len(old_labels)} labels from CSV")

# Create new labels dict
new_labels = {}

for policy_file in all_policies:
    fname = policy_file.name
    
    # Use existing label if available
    if fname in old_labels:
        new_labels[fname] = old_labels[fname]
    else:
        # New scraped policy - infer from filename
        if fname.startswith('scraped_escalation_'):
            vuln_type = fname.replace('scraped_escalation_', '').rsplit('_', 1)[0]
            new_labels[fname] = {
                "vulnerable": True,
                "severity": "high",
                "vulnerability_types": [vuln_type],
                "risk_score": 7.0,
                "description": f"Auto-labeled: {vuln_type}",
                "attack_paths": [],
                "remediation": "Review and restrict permissions",
                "source": "scraped_terraform"
            }
        elif fname.startswith('scraped_secure_'):
            new_labels[fname] = {
                "vulnerable": False,
                "severity": "low",
                "vulnerability_types": [],
                "risk_score": 2.0,
                "description": "Auto-labeled: secure policy",
                "attack_paths": [],
                "remediation": "",
                "source": "scraped_terraform"
            }
        else:
            # Unknown policy - mark as unlabeled
            print(f"  ⚠️  Unknown policy: {fname}")

print(f"\nTotal labels: {len(new_labels)} (Original: {len(old_labels)}, New: {len(new_labels) - len(old_labels)})")

# Write updated LABELS.json
labels_file.write_text(json.dumps(new_labels, indent=2), encoding='utf-8')
print(f"✓ Updated LABELS.json with {len(new_labels)} entries")

# Write updated CSV
with csv_file.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['file', 'vulnerable', 'severity', 'category'])
    
    for fname, label in sorted(new_labels.items()):
        vuln_types = label.get('vulnerability_types', [])
        category = vuln_types[0] if vuln_types else 'Other'
        writer.writerow([
            fname,
            label.get('vulnerable', False),
            label.get('severity', 'low'),
            category
        ])

print(f"✓ Updated {csv_file} with {len(new_labels)} entries")
