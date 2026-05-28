import json
from pathlib import Path

labels_file = Path('data/raw/samples/LABELS.json')

# Load
data = json.loads(labels_file.read_text(encoding='utf-8'))

# Fix each entry: rename "file" to "filename"
for entry in data.get('labels', []):
    if 'file' in entry:
        entry['filename'] = entry.pop('file')

# Save
labels_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

# Verify
fixed_count = sum(1 for e in data['labels'] if 'filename' in e)
print(f"✓ Fixed {fixed_count}/{len(data['labels'])} entries")

# Show first entry
print("\nFirst entry after fix:")
print(json.dumps(data['labels'][0], indent=2))
