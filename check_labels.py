import json
from pathlib import Path

labels_file = Path('data/raw/samples/LABELS.json')
data = json.loads(labels_file.read_text(encoding='utf-8'))

print("Top-level keys:", list(data.keys()))
print("Number of labels:", len(data.get('labels', [])))

if data.get('labels'):
    first = data['labels'][0]
    print("\nFirst entry keys:", list(first.keys()))
    print("\nFirst entry:")
    print(json.dumps(first, indent=2))
    
    # Check if any entries are missing 'filename'
    missing = [i for i, l in enumerate(data['labels']) if 'filename' not in l]
    if missing:
        print(f"\n⚠️  Entries missing 'filename': {len(missing)}")
        print(f"   Indices: {missing[:10]}")
    else:
        print("\n✓ All entries have 'filename' field")
