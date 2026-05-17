#!/usr/bin/env python3
"""
Run AWS IAM Access Analyzer on all IAM policies.

Uses the AWS CLI validate-policy API to check each policy for findings.
Requires valid AWS credentials. Handles rate limiting (1 req/sec).

Results saved to results/iam_analyzer_results.json.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SAMPLES_DIR = os.path.join(PROJECT_ROOT, 'data', 'raw', 'samples')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
OUTPUT_FILE = os.path.join(RESULTS_DIR, 'iam_analyzer_results.json')

# Rate limit: 1 request per second to avoid AWS throttling
RATE_LIMIT_SECONDS = 1.1


def check_aws_credentials() -> bool:
    """Verify AWS credentials are configured."""
    try:
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print(f"[INFO] AWS Identity: {identity.get('Arn', 'unknown')}")
            print(f"[INFO] Account: {identity.get('Account', 'unknown')}")
            return True
        else:
            print(f"[ERROR] AWS credentials check failed: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[ERROR] AWS CLI not found. Install it: pip install awscli")
        return False
    except subprocess.TimeoutExpired:
        print("[ERROR] AWS credentials check timed out")
        return False
    except Exception as e:
        print(f"[ERROR] AWS credentials check failed: {e}")
        return False


def validate_policy(policy_json: str) -> dict:
    """Call IAM Access Analyzer validate-policy API for a single policy."""
    try:
        result = subprocess.run(
            [
                'aws', 'accessanalyzer', 'validate-policy',
                '--policy-type', 'IDENTITY_POLICY',
                '--policy-document', policy_json,
                '--region', 'us-east-1',
                '--output', 'json',
            ],
            capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {
                'error': result.stderr.strip(),
                'returncode': result.returncode,
            }

    except subprocess.TimeoutExpired:
        return {'error': 'timeout'}
    except json.JSONDecodeError:
        return {'error': 'json_parse_error', 'raw': result.stdout}
    except Exception as e:
        return {'error': str(e)}


def classify_findings(findings: list) -> dict:
    """Classify IAM Access Analyzer findings by type and severity."""
    classification = {
        'errors': [],
        'warnings': [],
        'suggestions': [],
        'security_warnings': [],
        'total_findings': len(findings),
        'severity_counts': {},
        'finding_types': {},
    }

    for finding in findings:
        finding_type = finding.get('findingType', 'UNKNOWN')
        finding_details = finding.get('findingDetails', '')
        issue_code = finding.get('issueCode', '')
        learn_more_link = finding.get('learnMoreLink', '')

        entry = {
            'type': finding_type,
            'details': finding_details,
            'issue_code': issue_code,
            'learn_more': learn_more_link,
        }

        if finding_type == 'ERROR':
            classification['errors'].append(entry)
        elif finding_type == 'WARNING':
            classification['warnings'].append(entry)
        elif finding_type == 'SUGGESTION':
            classification['suggestions'].append(entry)
        elif finding_type == 'SECURITY_WARNING':
            classification['security_warnings'].append(entry)

        # Count by type
        classification['finding_types'][finding_type] = \
            classification['finding_types'].get(finding_type, 0) + 1

    classification['has_security_issues'] = (
        len(classification['errors']) > 0 or
        len(classification['security_warnings']) > 0 or
        len(classification['warnings']) > 0
    )

    return classification


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    start_time = time.time()

    print(f"{'='*60}")
    print(f"IAM Access Analyzer Baseline Runner")
    print(f"{'='*60}")

    # Check AWS credentials
    print("[INFO] Checking AWS credentials...")
    has_creds = check_aws_credentials()

    if not has_creds:
        print(f"\n{'='*60}")
        print("[WARN] AWS credentials not available.")
        print("  To use IAM Access Analyzer, configure AWS credentials:")
        print("  1. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
        print("  2. Or configure via 'aws configure'")
        print("  3. Or use an IAM role (EC2 instance profile, etc.)")
        print(f"\n  Creating placeholder results...")
        _create_placeholder_results()
        return 0

    # Get policy files
    policy_files = sorted([
        f for f in os.listdir(SAMPLES_DIR)
        if f.endswith('.json') and f != 'LABELS.json'
    ])

    print(f"[INFO] Found {len(policy_files)} policy files")
    print(f"[INFO] Rate limit: {RATE_LIMIT_SECONDS}s between requests")
    estimated_time = len(policy_files) * RATE_LIMIT_SECONDS
    print(f"[INFO] Estimated time: {estimated_time:.0f}s ({estimated_time/60:.1f}min)\n")

    all_results = {}
    throttle_count = 0

    for i, filename in enumerate(policy_files, 1):
        filepath = os.path.join(SAMPLES_DIR, filename)
        policy_name = os.path.splitext(filename)[0]

        progress = f"[{i:3d}/{len(policy_files)}]"
        print(f"  {progress} Validating {filename}...", end='', flush=True)

        try:
            with open(filepath, 'r') as f:
                policy_content = f.read()

            # Call validate-policy API
            result = validate_policy(policy_content)

            if 'error' in result:
                if 'Throttling' in str(result.get('error', '')):
                    throttle_count += 1
                    print(f" THROTTLED (waiting...)")
                    time.sleep(5)  # Extended wait on throttle
                    result = validate_policy(policy_content)
                elif 'error' in result:
                    print(f" ERROR: {result['error'][:50]}")
                    all_results[policy_name] = {
                        'filename': filename,
                        'error': result['error'],
                        'findings': {'total_findings': 0, 'has_security_issues': False}
                    }
                    time.sleep(RATE_LIMIT_SECONDS)
                    continue

            # Parse findings
            findings = result.get('findings', [])
            classification = classify_findings(findings)

            all_results[policy_name] = {
                'filename': filename,
                'findings': classification,
                'raw_findings_count': len(findings),
            }

            status = "FLAGGED" if classification['has_security_issues'] else "CLEAN"
            details = f"findings={len(findings)}"
            if classification['security_warnings']:
                details += f", security_warnings={len(classification['security_warnings'])}"
            print(f" {status} ({details})")

        except Exception as e:
            print(f" ERROR: {e}")
            all_results[policy_name] = {
                'filename': filename,
                'error': str(e),
                'findings': {'total_findings': 0, 'has_security_issues': False}
            }

        # Rate limiting
        time.sleep(RATE_LIMIT_SECONDS)

    elapsed = time.time() - start_time

    # Summary statistics
    total_flagged = sum(
        1 for r in all_results.values()
        if r.get('findings', {}).get('has_security_issues', False)
    )
    total_clean = len(all_results) - total_flagged

    summary = {
        'tool': 'iam_access_analyzer',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds': round(elapsed, 2),
        'total_policies': len(policy_files),
        'policies_flagged': total_flagged,
        'policies_clean': total_clean,
        'detection_rate': round(total_flagged / len(policy_files), 4) if policy_files else 0,
        'throttle_events': throttle_count,
    }

    output = {
        'summary': summary,
        'per_policy_results': all_results,
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"IAM Access Analyzer Results Summary")
    print(f"{'='*60}")
    print(f"  Total policies validated: {len(policy_files)}")
    print(f"  Policies flagged:         {total_flagged}")
    print(f"  Policies clean:           {total_clean}")
    print(f"  Detection rate:           {summary['detection_rate']:.2%}")
    print(f"  Throttle events:          {throttle_count}")
    print(f"  Time elapsed:             {elapsed:.1f}s")
    print(f"  Results saved to:         {OUTPUT_FILE}")

    return 0


def _create_placeholder_results():
    """Create placeholder results when AWS credentials are not available."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        'summary': {
            'tool': 'iam_access_analyzer',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'CREDENTIALS_REQUIRED',
            'note': 'AWS credentials not configured. Configure and re-run.',
            'total_policies': 0,
            'policies_flagged': 0,
            'detection_rate': 0,
            'setup_instructions': [
                'export AWS_ACCESS_KEY_ID=your_key',
                'export AWS_SECRET_ACCESS_KEY=your_secret',
                'export AWS_DEFAULT_REGION=us-east-1',
                'python scripts/baselines/run_iam_analyzer.py'
            ],
        },
        'per_policy_results': {},
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"[INFO] Placeholder results saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    sys.exit(main())
