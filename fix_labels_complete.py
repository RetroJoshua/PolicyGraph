import json
import csv
from pathlib import Path

samples_dir = Path('data/raw/samples')
labels_file = samples_dir / 'LABELS.json'
csv_file = Path('data/raw/policies_labeled.csv')

# Get all policy JSON files
all_policies = [f for f in samples_dir.glob('*.json') if f.name != 'LABELS.json']
print(f"Found {len(all_policies)} policy files")

# Create labels dict
labels = {}

for policy_file in all_policies:
    fname = policy_file.name
    
    # Scraped escalation policies
    if fname.startswith('scraped_escalation_'):
        vuln_type = fname.replace('scraped_escalation_', '').rsplit('_', 1)[0]
        labels[fname] = {
            "vulnerable": True,
            "severity": "high",
            "vulnerability_types": [vuln_type],
            "risk_score": 8.0,
            "description": f"Scraped escalation: {vuln_type}",
            "attack_paths": [],
            "remediation": "Review and restrict permissions",
            "source": "scraped_terraform"
        }
    
    # Scraped secure policies
    elif fname.startswith('scraped_secure_'):
        labels[fname] = {
            "vulnerable": False,
            "severity": "low",
            "vulnerability_types": [],
            "risk_score": 2.0,
            "description": "Scraped secure policy",
            "attack_paths": [],
            "remediation": "",
            "source": "scraped_terraform"
        }
    
    # Original escalation policies
    elif fname.startswith('escalation_'):
        vuln_type = fname.replace('escalation_', '').replace('.json', '')
        labels[fname] = {
            "vulnerable": True,
            "severity": "high",
            "vulnerability_types": [vuln_type],
            "risk_score": 9.0,
            "description": f"Privilege escalation: {vuln_type}",
            "attack_paths": [],
            "remediation": "Remove escalation vector",
            "source": "original_dataset"
        }
    
    # Original secure policies
    elif fname.startswith('secure_'):
        policy_type = fname.replace('secure_', '').replace('.json', '')
        labels[fname] = {
            "vulnerable": False,
            "severity": "low",
            "vulnerability_types": [],
            "risk_score": 1.0,
            "description": f"Secure policy: {policy_type}",
            "attack_paths": [],
            "remediation": "",
            "source": "original_dataset"
        }
    
    # CloudFormation policies (most have escalation potential)
    elif fname.startswith('cloudformation_'):
        if 'passrole' in fname or 'full_access' in fname:
            labels[fname] = {
                "vulnerable": True,
                "severity": "high",
                "vulnerability_types": ["cloudformation_escalation"],
                "risk_score": 7.5,
                "description": "CloudFormation with escalation risk",
                "attack_paths": [],
                "remediation": "Restrict CloudFormation permissions",
                "source": "original_dataset"
            }
        else:
            labels[fname] = {
                "vulnerable": False,
                "severity": "medium",
                "vulnerability_types": [],
                "risk_score": 3.0,
                "description": "CloudFormation with limited scope",
                "attack_paths": [],
                "remediation": "",
                "source": "original_dataset"
            }
    
    # Lambda policies
    elif fname.startswith('lambda_'):
        if 'passrole' in fname or 'full_access' in fname:
            labels[fname] = {
                "vulnerable": True,
                "severity": "high",
                "vulnerability_types": ["lambda_escalation"],
                "risk_score": 7.0,
                "description": "Lambda with escalation risk",
                "attack_paths": [],
                "remediation": "Restrict Lambda permissions",
                "source": "original_dataset"
            }
        else:
            labels[fname] = {
                "vulnerable": False,
                "severity": "low",
                "vulnerability_types": [],
                "risk_score": 2.0,
                "description": "Lambda with limited scope",
                "attack_paths": [],
                "remediation": "",
                "source": "original_dataset"
            }
    
    # IAM policies
    elif fname.startswith('iam_'):
        if 'write' in fname or 'admin' in fname or 'passrole' in fname:
            labels[fname] = {
                "vulnerable": True,
                "severity": "high",
                "vulnerability_types": ["iam_modification"],
                "risk_score": 8.5,
                "description": "IAM modification capability",
                "attack_paths": [],
                "remediation": "Restrict IAM permissions",
                "source": "original_dataset"
            }
        else:
            labels[fname] = {
                "vulnerable": False,
                "severity": "low",
                "vulnerability_types": [],
                "risk_score": 2.0,
                "description": "IAM read-only",
                "attack_paths": [],
                "remediation": "",
                "source": "original_dataset"
            }
    
    # AWS service policies (DynamoDB, EC2, S3, RDS, STS)
    elif fname.startswith(('dynamodb_', 'ec2_', 's3_', 'rds_', 'sts_')):
        service = fname.split('_')[0]
        if 'admin' in fname or 'full' in fname or 'wildcard' in fname or 'write' in fname:
            labels[fname] = {
                "vulnerable": True,
                "severity": "medium",
                "vulnerability_types": [f"{service}_overprivileged"],
                "risk_score": 6.0,
                "description": f"{service.upper()} overprivileged access",
                "attack_paths": [],
                "remediation": f"Restrict {service.upper()} permissions",
                "source": "original_dataset"
            }
        else:
            labels[fname] = {
                "vulnerable": False,
                "severity": "low",
                "vulnerability_types": [],
                "risk_score": 2.0,
                "description": f"{service.upper()} limited access",
                "attack_paths": [],
                "remediation": "",
                "source": "original_dataset"
            }
    
    # AWS managed/service policies
    elif fname.startswith('aws_'):
        if 'admin' in fname or 'full' in fname:
            labels[fname] = {
                "vulnerable": True,
                "severity": "high",
                "vulnerability_types": ["aws_managed_overprivileged"],
                "risk_score": 7.0,
                "description": "AWS managed policy with broad permissions",
                "attack_paths": [],
                "remediation": "Use more restrictive custom policies",
                "source": "original_dataset"
            }
        else:
            labels[fname] = {
                "vulnerable": False,
                "severity": "medium",
                "vulnerability_types": [],
                "risk_score": 3.0,
                "description": "AWS managed policy with specific purpose",
                "attack_paths": [],
                "remediation": "",
                "source": "original_dataset"
            }
    
    else:
        print(f"  ⚠️  Unmatched: {fname}")

# Count stats
vuln_count = sum(1 for l in labels.values() if l['vulnerable'])
secure_count = len(labels) - vuln_count

print(f"\n{'='*60}")
print(f"Total policies: {len(labels)}")
print(f"  Vulnerable: {vuln_count}")
print(f"  Secure: {secure_count}")
print(f"{'='*60}\n")

# Write LABELS.json
labels_file.write_text(json.dumps(labels, indent=2), encoding='utf-8')
print(f"✓ Updated LABELS.json with {len(labels)} entries")

# Write CSV
with csv_file.open('w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['file', 'vulnerable', 'severity', 'category'])
    
    for fname in sorted(labels.keys()):
        label = labels[fname]
        vuln_types = label.get('vulnerability_types', [])
        category = vuln_types[0] if vuln_types else 'Other'
        writer.writerow([
            fname,
            label['vulnerable'],
            label['severity'],
            category
        ])

print(f"✓ Updated {csv_file} with {len(labels)} entries")
