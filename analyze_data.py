import json
from pathlib import Path
from collections import defaultdict

labels_path = Path('data/raw/samples/LABELS.json')
with open(labels_path) as f:
    labels_data = json.load(f)

labels = labels_data['labels']
print(f'Total policies: {len(labels)}')
print()

label_counts = defaultdict(int)
severity_counts = defaultdict(int)
vuln_type_counts = defaultdict(int)
risk_score_stats = []

for label in labels:
    label_counts[label.get('label', 'unknown')] += 1
    severity_counts[label.get('severity', 'unknown')] += 1
    vuln_type_counts[label.get('vulnerability_type', 'unknown')] += 1
    risk_score_stats.append(label.get('risk_score', 0))

print('=== LABEL DISTRIBUTION ===')
for label_type, count in sorted(label_counts.items()):
    pct = (count / len(labels)) * 100
    print(f'{label_type:15} {count:3d} ({pct:5.1f}%)')

print()
print('=== SEVERITY DISTRIBUTION ===')
for severity, count in sorted(severity_counts.items()):
    pct = (count / len(labels)) * 100
    print(f'{severity:15} {count:3d} ({pct:5.1f}%)')

print()
print('=== TOP 15 VULNERABILITY TYPES ===')
for vuln_type, count in sorted(vuln_type_counts.items(), key=lambda x: -x[1])[:15]:
    pct = (count / len(labels)) * 100
    print(f'{vuln_type:40} {count:3d} ({pct:5.1f}%)')

print()
print('=== RISK SCORE STATISTICS ===')
print(f'Min Risk Score: {min(risk_score_stats):.2f}')
print(f'Max Risk Score: {max(risk_score_stats):.2f}')
print(f'Avg Risk Score: {sum(risk_score_stats)/len(risk_score_stats):.2f}')

print()
print('=== POLICIES BY CATEGORY ===')
file_categories = defaultdict(int)
for label in labels:
    filename = label['filename']
    category = filename.split('_')[0]
    file_categories[category] += 1

for cat, count in sorted(file_categories.items(), key=lambda x: -x[1]):
    pct = (count / len(labels)) * 100
    print(f'{cat:20} {count:3d} ({pct:5.1f}%)')
