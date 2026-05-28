import json
from pathlib import Path

labels_file = Path('data/raw/samples/LABELS.json')
data = json.loads(labels_file.read_text(encoding='utf-8'))

# Keep only non-scraped policies
original = [e for e in data['labels'] if not e['filename'].startswith('scraped_')]

print(f"Original: {len(data['labels'])} → Keeping: {len(original)}")

data['labels'] = original
labels_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
print("✓ Reverted to original 108 high-quality labels")
