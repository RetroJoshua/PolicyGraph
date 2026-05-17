#!/usr/bin/env python3
"""
Wrap IAM policies in CloudFormation templates for Checkov scanning.

Reads all 108 policies from data/raw/samples/ and wraps each in an
AWS::IAM::ManagedPolicy CloudFormation resource, saving YAML files
to data/baseline_tests/checkov_input/.
"""

import json
import os
import re
import sys
import yaml
from datetime import datetime, timezone

# Project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAMPLES_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw', 'samples')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'baseline_tests', 'checkov_input')
LABELS_FILE = os.path.join(SAMPLES_DIR, 'LABELS.json')


def sanitize_name(filename: str) -> str:
    """Convert filename to a valid CloudFormation logical ID."""
    name = os.path.splitext(filename)[0]
    # Remove invalid characters, keep alphanumeric
    name = re.sub(r'[^a-zA-Z0-9]', '', name.title().replace('_', ' ').replace('-', ' ').replace('.', ' '))
    # Ensure it starts with a letter
    if name and not name[0].isalpha():
        name = 'Policy' + name
    return name[:128]  # CFN logical IDs max 128 chars


def wrap_policy_in_cfn(policy_doc: dict, filename: str, label_info: dict = None) -> dict:
    """Wrap an IAM policy document in a CloudFormation template."""
    logical_id = sanitize_name(filename)
    description = f"PolicyGraph baseline test - {filename}"
    if label_info:
        description += f" (label: {label_info.get('label', 'unknown')})"

    template = {
        'AWSTemplateFormatVersion': '2010-09-09',
        'Description': description,
        'Metadata': {
            'PolicyGraph': {
                'SourceFile': filename,
                'Label': label_info.get('label', 'unknown') if label_info else 'unknown',
                'VulnerabilityType': label_info.get('vulnerability_type', 'unknown') if label_info else 'unknown',
                'Severity': label_info.get('severity', 'unknown') if label_info else 'unknown',
                'GeneratedAt': datetime.now(timezone.utc).isoformat(),
            }
        },
        'Resources': {
            logical_id: {
                'Type': 'AWS::IAM::ManagedPolicy',
                'Properties': {
                    'ManagedPolicyName': os.path.splitext(filename)[0],
                    'Description': f'IAM Policy from {filename}',
                    'PolicyDocument': policy_doc,
                }
            }
        }
    }
    return template


def load_labels() -> dict:
    """Load ground truth labels keyed by filename."""
    if not os.path.exists(LABELS_FILE):
        print(f"[WARN] Labels file not found: {LABELS_FILE}")
        return {}
    with open(LABELS_FILE, 'r') as f:
        data = json.load(f)
    return {entry['filename']: entry for entry in data.get('labels', [])}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    labels = load_labels()

    # Collect all JSON policy files (exclude LABELS.json, README.md)
    policy_files = sorted([
        f for f in os.listdir(SAMPLES_DIR)
        if f.endswith('.json') and f != 'LABELS.json'
    ])

    print(f"[INFO] Found {len(policy_files)} policy files in {SAMPLES_DIR}")
    print(f"[INFO] Output directory: {OUTPUT_DIR}")

    success_count = 0
    error_count = 0
    errors = []

    for filename in policy_files:
        filepath = os.path.join(SAMPLES_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                policy_doc = json.load(f)

            label_info = labels.get(filename, None)
            cfn_template = wrap_policy_in_cfn(policy_doc, filename, label_info)

            output_name = os.path.splitext(filename)[0] + '.yaml'
            output_path = os.path.join(OUTPUT_DIR, output_name)

            with open(output_path, 'w') as f:
                # Add metadata comment
                f.write(f"# PolicyGraph Baseline Test - CloudFormation Wrapper\n")
                f.write(f"# Source: {filename}\n")
                if label_info:
                    f.write(f"# Label: {label_info.get('label', 'unknown')}\n")
                    f.write(f"# Vulnerability: {label_info.get('vulnerability_type', 'none')}\n")
                f.write(f"# Generated: {datetime.now(timezone.utc).isoformat()}\n")
                f.write(f"#\n")
                yaml.dump(cfn_template, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append((filename, str(e)))
            print(f"[ERROR] Failed to wrap {filename}: {e}")

    print(f"\n{'='*60}")
    print(f"CloudFormation Wrapping Complete")
    print(f"{'='*60}")
    print(f"  Total policies:  {len(policy_files)}")
    print(f"  Successfully wrapped: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Output: {OUTPUT_DIR}")

    if errors:
        print(f"\nErrors:")
        for fn, err in errors:
            print(f"  - {fn}: {err}")

    # Save manifest
    manifest = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'total_policies': len(policy_files),
        'success_count': success_count,
        'error_count': error_count,
        'output_dir': OUTPUT_DIR,
        'files': [os.path.splitext(f)[0] + '.yaml' for f in policy_files if f not in [e[0] for e in errors]]
    }
    manifest_path = os.path.join(OUTPUT_DIR, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest: {manifest_path}")

    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
