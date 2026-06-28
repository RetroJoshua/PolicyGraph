import json
from pathlib import Path

output_dir = Path('data/raw/samples')
policy_files = list(output_dir.glob('policy_*.json'))

vulnerable_count = 0
secure_count = 0
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

print("="*70)
print("EXTRACTION SUMMARY")
print("="*70)
print(f"\nTotal policies extracted: {len(policy_files)}")
print(f"Output directory: {output_dir.absolute()}")
print(f"\nVulnerability Distribution:")
print(f"  Vulnerable: {vulnerable_count} ({vulnerable_count/len(policy_files)*100:.1f}%)")
print(f"  Secure: {secure_count} ({secure_count/len(policy_files)*100:.1f}%)")
print(f"\nConfidence Distribution:")
print(f"  High: {high_conf} ({high_conf/len(policy_files)*100:.1f}%)")
print(f"  Medium: {medium_conf} ({medium_conf/len(policy_files)*100:.1f}%)")
print(f"\nAll policies successfully extracted as individual JSON files!")
print("="*70)
