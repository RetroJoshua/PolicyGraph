#!/usr/bin/env python3
"""
Wrap IAM policies in Terraform format for tfsec scanning.

Reads all 108 policies from data/raw/samples/ and wraps each in an
aws_iam_policy Terraform resource, saving .tf files to
data/baseline_tests/tfsec_input/.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAMPLES_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw', 'samples')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'baseline_tests', 'tfsec_input')
LABELS_FILE = os.path.join(SAMPLES_DIR, 'LABELS.json')


def sanitize_tf_name(filename: str) -> str:
    """Convert filename to a valid Terraform resource name."""
    name = os.path.splitext(filename)[0]
    # Terraform resource names: letters, digits, underscores, hyphens
    name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
    # Must start with a letter or underscore
    if name and name[0].isdigit():
        name = 'policy_' + name
    return name[:128]


def policy_to_heredoc(policy_doc: dict) -> str:
    """Convert policy dict to a JSON string for Terraform heredoc."""
    return json.dumps(policy_doc, indent=2)


def generate_provider_block() -> str:
    """Generate the Terraform AWS provider block."""
    return '''# PolicyGraph Baseline Test - Terraform Provider Configuration
# Generated for tfsec scanning

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"

  # These are placeholder values for static analysis only
  # tfsec does not require actual AWS credentials
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}
'''


def generate_tf_resource(policy_doc: dict, filename: str, label_info: dict = None) -> str:
    """Generate a Terraform aws_iam_policy resource block."""
    resource_name = sanitize_tf_name(filename)
    policy_json = policy_to_heredoc(policy_doc)
    base_name = os.path.splitext(filename)[0]

    lines = []
    lines.append(f'# PolicyGraph Baseline Test - Terraform Wrapper')
    lines.append(f'# Source: {filename}')
    if label_info:
        lines.append(f'# Label: {label_info.get("label", "unknown")}')
        lines.append(f'# Vulnerability: {label_info.get("vulnerability_type", "none")}')
        lines.append(f'# Severity: {label_info.get("severity", "unknown")}')
    lines.append(f'# Generated: {datetime.now(timezone.utc).isoformat()}')
    lines.append(f'')
    lines.append(f'resource "aws_iam_policy" "{resource_name}" {{')
    lines.append(f'  name        = "{base_name}"')
    lines.append(f'  description = "IAM Policy from {filename}"')
    lines.append(f'  path        = "/"')
    lines.append(f'')
    lines.append(f'  policy = jsonencode({policy_json})')
    lines.append(f'}}')
    lines.append(f'')

    return '\n'.join(lines)


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

    policy_files = sorted([
        f for f in os.listdir(SAMPLES_DIR)
        if f.endswith('.json') and f != 'LABELS.json'
    ])

    print(f"[INFO] Found {len(policy_files)} policy files in {SAMPLES_DIR}")
    print(f"[INFO] Output directory: {OUTPUT_DIR}")

    # Write provider configuration
    provider_path = os.path.join(OUTPUT_DIR, 'provider.tf')
    with open(provider_path, 'w') as f:
        f.write(generate_provider_block())
    print(f"[INFO] Provider block written to {provider_path}")

    success_count = 0
    error_count = 0
    errors = []

    for filename in policy_files:
        filepath = os.path.join(SAMPLES_DIR, filename)
        try:
            with open(filepath, 'r') as f:
                policy_doc = json.load(f)

            label_info = labels.get(filename, None)
            tf_content = generate_tf_resource(policy_doc, filename, label_info)

            output_name = os.path.splitext(filename)[0] + '.tf'
            output_path = os.path.join(OUTPUT_DIR, output_name)

            with open(output_path, 'w') as f:
                f.write(tf_content)

            success_count += 1
        except Exception as e:
            error_count += 1
            errors.append((filename, str(e)))
            print(f"[ERROR] Failed to wrap {filename}: {e}")

    print(f"\n{'='*60}")
    print(f"Terraform Wrapping Complete")
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
        'files': [os.path.splitext(f)[0] + '.tf' for f in policy_files if f not in [e[0] for e in errors]]
    }
    manifest_path = os.path.join(OUTPUT_DIR, 'manifest.json')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print(f"  Manifest: {manifest_path}")

    return 0 if error_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
