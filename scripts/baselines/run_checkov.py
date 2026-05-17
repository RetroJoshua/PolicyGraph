#!/usr/bin/env python3
"""
Run Checkov on all CloudFormation-wrapped IAM policies.

Executes checkov against each YAML template in data/baseline_tests/checkov_input/,
collects results, and saves them to results/checkov_results.json.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'baseline_tests', 'checkov_input')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
OUTPUT_FILE = os.path.join(RESULTS_DIR, 'checkov_results.json')


def check_checkov_installed() -> bool:
    """Check if checkov is installed."""
    try:
        result = subprocess.run(
            ['checkov', '--version'],
            capture_output=True, text=True, timeout=30
        )
        print(f"[INFO] Checkov version: {result.stdout.strip()}")
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def install_checkov():
    """Attempt to install checkov via pip."""
    print("[INFO] Installing checkov...")
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'checkov>=2.3.0'],
            check=True, capture_output=True, text=True, timeout=300
        )
        print("[INFO] Checkov installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install checkov: {e.stderr}")
        return False


def run_checkov_on_file(filepath: str) -> dict:
    """Run checkov on a single CloudFormation file and return results."""
    try:
        result = subprocess.run(
            [
                'checkov',
                '--file', filepath,
                '--framework', 'cloudformation',
                '--output', 'json',
                '--quiet',
                '--compact',
            ],
            capture_output=True, text=True, timeout=120
        )

        # Checkov returns exit code 1 if checks fail, which is expected
        output = result.stdout.strip()
        if output:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                # Sometimes checkov outputs multiple JSON objects
                # Try to parse the first one
                for line in output.split('\n'):
                    line = line.strip()
                    if line.startswith('{') or line.startswith('['):
                        try:
                            return json.loads(line)
                        except json.JSONDecodeError:
                            continue
                return {'raw_output': output, 'parse_error': True}
        else:
            return {
                'stderr': result.stderr.strip(),
                'returncode': result.returncode,
                'no_output': True
            }

    except subprocess.TimeoutExpired:
        return {'error': 'timeout', 'file': filepath}
    except Exception as e:
        return {'error': str(e), 'file': filepath}


def extract_findings(checkov_result: dict) -> dict:
    """Extract structured findings from checkov output."""
    findings = {
        'passed_checks': [],
        'failed_checks': [],
        'skipped_checks': [],
        'parsing_errors': [],
    }

    if isinstance(checkov_result, list):
        # Checkov can return a list of results per framework
        for item in checkov_result:
            _extract_from_item(item, findings)
    elif isinstance(checkov_result, dict):
        _extract_from_item(checkov_result, findings)

    findings['total_passed'] = len(findings['passed_checks'])
    findings['total_failed'] = len(findings['failed_checks'])
    findings['total_skipped'] = len(findings['skipped_checks'])
    findings['has_issues'] = findings['total_failed'] > 0

    return findings


def _extract_from_item(item: dict, findings: dict):
    """Extract findings from a single checkov result item."""
    if 'results' not in item:
        return

    results = item['results']

    for check in results.get('passed_checks', []):
        findings['passed_checks'].append({
            'check_id': check.get('check_id', ''),
            'check_name': check.get('check_result', {}).get('result', ''),
            'resource': check.get('resource', ''),
            'guideline': check.get('guideline', ''),
        })

    for check in results.get('failed_checks', []):
        findings['failed_checks'].append({
            'check_id': check.get('check_id', ''),
            'check_name': check.get('check_result', {}).get('result', ''),
            'resource': check.get('resource', ''),
            'guideline': check.get('guideline', ''),
            'severity': check.get('severity', 'UNKNOWN'),
        })

    for check in results.get('skipped_checks', []):
        findings['skipped_checks'].append({
            'check_id': check.get('check_id', ''),
            'resource': check.get('resource', ''),
        })


def run_checkov_batch(input_dir: str) -> dict:
    """Run checkov on entire directory at once for efficiency."""
    try:
        result = subprocess.run(
            [
                'checkov',
                '--directory', input_dir,
                '--framework', 'cloudformation',
                '--output', 'json',
                '--quiet',
                '--compact',
            ],
            capture_output=True, text=True, timeout=600
        )

        output = result.stdout.strip()
        if output:
            try:
                return {'batch_result': json.loads(output), 'success': True}
            except json.JSONDecodeError:
                return {'raw_output': output, 'parse_error': True, 'success': False}
        return {'stderr': result.stderr.strip(), 'success': False}

    except subprocess.TimeoutExpired:
        return {'error': 'timeout', 'success': False}
    except Exception as e:
        return {'error': str(e), 'success': False}


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    start_time = time.time()

    print(f"{'='*60}")
    print(f"Checkov Baseline Runner")
    print(f"{'='*60}")

    # Check/install checkov
    if not check_checkov_installed():
        print("[WARN] Checkov not found, attempting installation...")
        if not install_checkov():
            print("[ERROR] Could not install checkov. Please install manually:")
            print("  pip install checkov")
            sys.exit(1)

    # Get input files
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Input directory not found: {INPUT_DIR}")
        print("  Run scripts/wrappers/wrap_for_checkov.py first")
        sys.exit(1)

    yaml_files = sorted([
        f for f in os.listdir(INPUT_DIR)
        if f.endswith('.yaml') and f != 'manifest.json'
    ])

    if not yaml_files:
        print(f"[ERROR] No YAML files found in {INPUT_DIR}")
        sys.exit(1)

    print(f"[INFO] Found {len(yaml_files)} CloudFormation templates")
    print(f"[INFO] Running Checkov on each file...\n")

    # Run on each file individually for per-policy results
    all_results = {}
    for i, filename in enumerate(yaml_files, 1):
        filepath = os.path.join(INPUT_DIR, filename)
        policy_name = os.path.splitext(filename)[0]

        progress = f"[{i:3d}/{len(yaml_files)}]"
        print(f"  {progress} Scanning {filename}...", end='', flush=True)

        raw_result = run_checkov_on_file(filepath)
        findings = extract_findings(raw_result)

        all_results[policy_name] = {
            'filename': filename,
            'findings': findings,
            'raw_result_summary': {
                'passed': findings['total_passed'],
                'failed': findings['total_failed'],
                'skipped': findings['total_skipped'],
            }
        }

        status = "FAIL" if findings['has_issues'] else "PASS"
        print(f" {status} (passed={findings['total_passed']}, failed={findings['total_failed']})")

    # Also run batch for overall summary
    print(f"\n[INFO] Running batch Checkov scan...")
    batch_result = run_checkov_batch(INPUT_DIR)

    elapsed = time.time() - start_time

    # Summary statistics
    total_flagged = sum(1 for r in all_results.values() if r['findings']['has_issues'])
    total_clean = len(all_results) - total_flagged

    summary = {
        'tool': 'checkov',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds': round(elapsed, 2),
        'total_policies': len(yaml_files),
        'policies_flagged': total_flagged,
        'policies_clean': total_clean,
        'detection_rate': round(total_flagged / len(yaml_files), 4) if yaml_files else 0,
    }

    output = {
        'summary': summary,
        'per_policy_results': all_results,
        'batch_result': batch_result,
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"Checkov Results Summary")
    print(f"{'='*60}")
    print(f"  Total policies scanned: {len(yaml_files)}")
    print(f"  Policies flagged:       {total_flagged}")
    print(f"  Policies clean:         {total_clean}")
    print(f"  Detection rate:         {summary['detection_rate']:.2%}")
    print(f"  Time elapsed:           {elapsed:.1f}s")
    print(f"  Results saved to:       {OUTPUT_FILE}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
