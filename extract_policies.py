import pandas as pd
import json
import os
from pathlib import Path

excel_file = 'data/labeled_policies_merged.xlsx'
df = pd.read_excel(excel_file, sheet_name='IAM_Policies')

output_dir = Path('data/raw/samples')
output_dir.mkdir(parents=True, exist_ok=True)

print(f"Processing {len(df)} policies...")
print("="*70)

saved_count = 0
skipped_count = 0

for idx, row in df.iterrows():
    try:
        original_filename = row['filename'].replace('.', '_').replace('/', '_')
        policy_id = f"{idx+1:03d}"
        json_filename = f"policy_{policy_id}_{original_filename}.json"
        json_path = output_dir / json_filename
        
        policy_data = {
            "id": f"policy_{policy_id}",
            "filename": row['filename'],
            "source_repo": row['source_repo'],
            "source_path": row['source_path'],
            "content": row['content'],
            "metadata": {
                "vulnerable": bool(row['vulnerable']),
                "confidence": row['confidence'],
                "notes": row['notes'] if pd.notna(row['notes']) else None,
                "checkov_findings": row['checkov_findings'] if pd.notna(row['checkov_findings']) else None,
                "scraped_date": row['scraped_date'] if pd.notna(row['scraped_date']) else None
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(policy_data, f, indent=2, ensure_ascii=False)
        
        saved_count += 1
        if (idx + 1) % 50 == 0:
            print(f"[OK] Saved {saved_count} policies...")
            
    except Exception as e:
        print(f"[ERROR] Error processing row {idx}: {str(e)}")
        skipped_count += 1

print("="*70)
print(f"\nSummary:")
print(f"  Total policies processed: {len(df)}")
print(f"  Successfully saved: {saved_count}")
print(f"  Skipped: {skipped_count}")
print(f"  Output directory: {output_dir.absolute()}")

print(f"\nSample files created:")
files = sorted(list(output_dir.glob("policy_*.json")))
for i, file in enumerate(files[:5]):
    print(f"  - {file.name}")
if len(files) > 5:
    print(f"  ... and {len(files) - 5} more files")
