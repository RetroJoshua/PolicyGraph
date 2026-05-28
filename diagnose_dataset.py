import json
from pathlib import Path
from collections import Counter

labels_file = Path('data/raw/samples/LABELS.json')
data = json.loads(labels_file.read_text(encoding='utf-8'))

# Check label distribution
vuln_values = [entry.get('vulnerable') for entry in data['labels']]
print("Vulnerable field types:", set(type(v).__name__ for v in vuln_values))
print("Vulnerable values:", Counter(vuln_values))

# Check if booleans or strings
bool_count = sum(1 for v in vuln_values if isinstance(v, bool))
str_count = sum(1 for v in vuln_values if isinstance(v, str))

print(f"\nBoolean: {bool_count}, String: {str_count}")

# Show samples
print("\nFirst 10 vulnerable values:")
for i, entry in enumerate(data['labels'][:10]):
    print(f"  {i}: {entry['filename'][:40]:40} -> vulnerable={entry['vulnerable']} (type: {type(entry['vulnerable']).__name__})")

# Check True/False distribution
if bool_count > 0:
    true_count = sum(1 for v in vuln_values if v is True)
    false_count = sum(1 for v in vuln_values if v is False)
    print(f"\nTrue: {true_count}, False: {false_count}")
