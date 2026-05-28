import json
from pathlib import Path

labels_file = Path('data/raw/samples/LABELS.json')

# Load current dict structure
current = json.loads(labels_file.read_text(encoding='utf-8'))

# Convert to list structure
labels_list = []
for filename, label_data in current.items():
    label_entry = {
        "file": filename,
        "vulnerable": label_data.get("vulnerable", False),
        "severity": label_data.get("severity", "low"),
        "vulnerability_types": label_data.get("vulnerability_types", []),
        "risk_score": label_data.get("risk_score", 2.0),
        "description": label_data.get("description", ""),
        "attack_paths": label_data.get("attack_paths", []),
        "remediation": label_data.get("remediation", ""),
        "source": label_data.get("source", "unknown")
    }
    labels_list.append(label_entry)

# Wrap in expected structure
correct_structure = {"labels": labels_list}

# Write back
labels_file.write_text(json.dumps(correct_structure, indent=2), encoding='utf-8')

print(f"✓ Fixed LABELS.json structure: {len(labels_list)} entries")
print(f"  Vulnerable: {sum(1 for l in labels_list if l['vulnerable'])}")
print(f"  Secure: {sum(1 for l in labels_list if not l['vulnerable'])}")
