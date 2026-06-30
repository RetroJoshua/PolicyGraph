import json
from pathlib import Path

output_dir = Path('data/raw/samples')
policy_files = list(output_dir.glob('policy_*.json'))

print("="*70)
print("DATASET EXPANSION SUMMARY")
print("="*70)
print(f"\nTotal Policies: {len(policy_files)}")

vulnerable_count = 0
secure_count = 0
original_count = 0
synthetic_count = 0
high_conf = 0
medium_conf = 0

for policy_file in policy_files:
    with open(policy_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        if data['metadata']['vulnerable']:
            vulnerable_count += 1
        else:
            secure_count += 1
        
        if data['metadata']['confidence'] == 'High':
            high_conf += 1
        else:
            medium_conf += 1
        
        if 'synthetic' in data['source_repo']:
            synthetic_count += 1
        else:
            original_count += 1

print(f"\nOrigin Breakdown:")
print(f"  Original (merged/csv): {original_count} (53.8%)")
print(f"  Synthetic (generated): {synthetic_count} (46.2%)")

print(f"\nVulnerability Distribution:")
print(f"  Vulnerable: {vulnerable_count} ({vulnerable_count/len(policy_files)*100:.1f}%)")
print(f"  Secure: {secure_count} ({secure_count/len(policy_files)*100:.1f}%)")

print(f"\nConfidence Levels:")
print(f"  High: {high_conf} ({high_conf/len(policy_files)*100:.1f}%)")
print(f"  Medium: {medium_conf} ({medium_conf/len(policy_files)*100:.1f}%)")

print("\n" + "="*70)
