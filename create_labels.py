import json
from pathlib import Path

output_dir = Path('data/raw/samples')
policy_files = sorted(list(output_dir.glob('policy_*.json')))

labels = {}

for policy_file in policy_files:
    with open(policy_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        filename = policy_file.name
        vulnerable = data['metadata']['vulnerable']
        confidence = data['metadata']['confidence']
        severity = 'critical' if (vulnerable and confidence == 'High') else ('high' if vulnerable else 'low')
        
        labels[filename] = {
            'label': 'vulnerable' if vulnerable else 'safe',
            'vulnerable': vulnerable,
            'confidence': confidence,
            'severity': severity,
            'source': data.get('source_repo', 'unknown'),
            'notes': data['metadata'].get('notes', '')
        }

labels_payload = {
    'total_policies': len(labels),
    'labels': [{'filename': k, **v} for k, v in labels.items()]
}

output_file = output_dir / 'LABELS.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(labels_payload, f, indent=2, ensure_ascii=False)

print(f"Created LABELS.json with {len(labels)} policies")
print(f"  Vulnerable: {sum(1 for v in labels.values() if v['vulnerable'])}")
print(f"  Safe: {sum(1 for v in labels.values() if not v['vulnerable'])}")
print(f"File saved to: {output_file}")
