#!/usr/bin/env python3
"""
Run tfsec on all Terraform-wrapped IAM policies.

Executes tfsec against the Terraform files in data/baseline_tests/tfsec_input/,
collects results, and saves them to results/tfsec_results.json.

Note: tfsec has limited IAM policy analysis capabilities compared to
dedicated IAM tools; minimal findings are expected.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
INPUT_DIR = os.path.join(PROJECT_ROOT, 'data', 'baseline_tests', 'tfsec_input')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
OUTPUT_FILE = os.path.join(RESULTS_DIR, 'tfsec_results.json')


def check_tfsec_installed() -> tuple:
    """Check if tfsec (or trivy) is installed. Returns (binary_name, version)."""
    # tfsec has been integrated into trivy; check both
    for binary in ['tfsec', 'trivy']:
        try:
            result = subprocess.run(
                [binary, '--version'],
                capture_output=True, text=True, timeout=30
            )
            version = result.stdout.strip() or result.stderr.strip()
            print(f"[INFO] Found {binary}: {version}")
            return binary, version
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return None, None


def install_tfsec() -> str:
    """Attempt to install tfsec."""
    print("[INFO] Attempting to install tfsec...")

    # Try installing via Go
    try:
        subprocess.run(
            ['go', 'install', 'github.com/aquasecurity/tfsec/cmd/tfsec@latest'],
            capture_output=True, text=True, timeout=300
        )
        # Check if it's now available
        result = subprocess.run(['tfsec', '--version'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[INFO] tfsec installed via Go")
            return 'tfsec'
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # Try installing via binary download
    try:
        import platform
        arch = platform.machine()
        if arch == 'x86_64':
            arch = 'amd64'
        elif arch == 'aarch64':
            arch = 'arm64'

        url = f"https://github.com/aquasecurity/tfsec/releases/latest/download/tfsec-linux-{arch}"
        subprocess.run(
            ['curl', '-sL', '-o', '/usr/local/bin/tfsec', url],
            check=True, capture_output=True, timeout=120
        )
        subprocess.run(
            ['chmod', '+x', '/usr/local/bin/tfsec'],
            check=True, capture_output=True, timeout=10
        )
        result = subprocess.run(['tfsec', '--version'], capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("[INFO] tfsec installed via binary download")
            return 'tfsec'
    except Exception as e:
        print(f"[WARN] Binary install failed: {e}")

    # Try trivy as alternative (tfsec is now part of trivy)
    try:
        subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'trivy'],
            capture_output=True, text=True, timeout=300
        )
    except Exception:
        pass

    return None


def run_tfsec_on_directory(binary: str, input_dir: str) -> dict:
    """Run tfsec/trivy on the entire directory."""
    try:
        if binary == 'tfsec':
            cmd = [
                'tfsec', input_dir,
                '--format', 'json',
                '--no-color',
                '--soft-fail',
            ]
        else:
            # trivy config scan
            cmd = [
                'trivy', 'config', input_dir,
                '--format', 'json',
                '--severity', 'LOW,MEDIUM,HIGH,CRITICAL',
            ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )

        output = result.stdout.strip()
        if output:
            try:
                return {'result': json.loads(output), 'success': True}
            except json.JSONDecodeError:
                return {'raw_output': output, 'parse_error': True, 'success': False}
        return {
            'stderr': result.stderr.strip(),
            'returncode': result.returncode,
            'success': False
        }

    except subprocess.TimeoutExpired:
        return {'error': 'timeout', 'success': False}
    except Exception as e:
        return {'error': str(e), 'success': False}


def run_tfsec_per_file(binary: str, input_dir: str) -> dict:
    """Run tfsec on each .tf file individually for per-policy tracking."""
    tf_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.tf') and f != 'provider.tf'])
    results = {}

    for i, filename in enumerate(tf_files, 1):
        filepath = os.path.join(input_dir, filename)
        policy_name = os.path.splitext(filename)[0]

        progress = f"[{i:3d}/{len(tf_files)}]"
        print(f"  {progress} Scanning {filename}...", end='', flush=True)

        try:
            if binary == 'tfsec':
                cmd = [
                    'tfsec', input_dir,
                    '--format', 'json',
                    '--no-color',
                    '--soft-fail',
                    '--include-passed',
                ]
            else:
                cmd = [
                    'trivy', 'config', filepath,
                    '--format', 'json',
                ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=60
            )

            output = result.stdout.strip()
            if output:
                try:
                    parsed = json.loads(output)
                    # Count findings for this specific file
                    file_findings = _count_findings_for_file(parsed, filename, binary)
                    results[policy_name] = {
                        'filename': filename,
                        'findings': file_findings,
                    }
                    status = "FAIL" if file_findings.get('total_issues', 0) > 0 else "PASS"
                    print(f" {status} (issues={file_findings.get('total_issues', 0)})")
                except json.JSONDecodeError:
                    results[policy_name] = {
                        'filename': filename,
                        'findings': {'error': 'parse_error', 'total_issues': 0},
                    }
                    print(f" PARSE_ERROR")
            else:
                results[policy_name] = {
                    'filename': filename,
                    'findings': {'total_issues': 0, 'no_output': True},
                }
                print(f" NO_OUTPUT")

        except subprocess.TimeoutExpired:
            results[policy_name] = {
                'filename': filename,
                'findings': {'error': 'timeout', 'total_issues': 0},
            }
            print(f" TIMEOUT")
        except Exception as e:
            results[policy_name] = {
                'filename': filename,
                'findings': {'error': str(e), 'total_issues': 0},
            }
            print(f" ERROR")

    return results


def _count_findings_for_file(parsed: dict, filename: str, binary: str) -> dict:
    """Extract findings for a specific file from parsed tfsec/trivy output."""
    findings = {
        'total_issues': 0,
        'severity_counts': {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0},
        'issues': [],
    }

    if binary == 'tfsec':
        # tfsec format
        results_list = parsed.get('results', [])
        if results_list is None:
            results_list = []
        for result in results_list:
            loc = result.get('location', {}).get('filename', '')
            if filename in loc or not loc:
                severity = result.get('severity', 'UNKNOWN').upper()
                findings['total_issues'] += 1
                findings['severity_counts'][severity] = findings['severity_counts'].get(severity, 0) + 1
                findings['issues'].append({
                    'rule_id': result.get('rule_id', ''),
                    'description': result.get('description', ''),
                    'severity': severity,
                    'resource': result.get('resource', ''),
                })
    else:
        # trivy format
        for result_block in parsed.get('Results', []):
            for vuln in result_block.get('Misconfigurations', []):
                severity = vuln.get('Severity', 'UNKNOWN').upper()
                findings['total_issues'] += 1
                findings['severity_counts'][severity] = findings['severity_counts'].get(severity, 0) + 1
                findings['issues'].append({
                    'rule_id': vuln.get('ID', ''),
                    'description': vuln.get('Title', ''),
                    'severity': severity,
                })

    findings['has_issues'] = findings['total_issues'] > 0
    return findings


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    start_time = time.time()

    print(f"{'='*60}")
    print(f"tfsec Baseline Runner")
    print(f"{'='*60}")

    # Check/install tfsec
    binary, version = check_tfsec_installed()
    if not binary:
        print("[WARN] tfsec not found, attempting installation...")
        binary = install_tfsec()
        if not binary:
            print("[WARN] Could not install tfsec. Creating placeholder results.")
            print("  Install manually: https://aquasecurity.github.io/tfsec/")
            # Create placeholder results
            _create_placeholder_results()
            return 0

    # Check input directory
    if not os.path.exists(INPUT_DIR):
        print(f"[ERROR] Input directory not found: {INPUT_DIR}")
        print("  Run scripts/wrappers/wrap_for_tfsec.py first")
        sys.exit(1)

    tf_files = [f for f in os.listdir(INPUT_DIR) if f.endswith('.tf') and f != 'provider.tf']
    if not tf_files:
        print(f"[ERROR] No .tf files found in {INPUT_DIR}")
        sys.exit(1)

    print(f"[INFO] Found {len(tf_files)} Terraform files")
    print(f"[INFO] Using {binary} for scanning\n")

    # Run directory-level scan
    print("[INFO] Running directory-level scan...")
    dir_result = run_tfsec_on_directory(binary, INPUT_DIR)

    # Per-file scan for detailed tracking
    print(f"\n[INFO] Running per-file analysis...")
    per_file_results = run_tfsec_per_file(binary, INPUT_DIR)

    elapsed = time.time() - start_time

    # Summary
    total_flagged = sum(
        1 for r in per_file_results.values()
        if r.get('findings', {}).get('has_issues', False)
    )
    total_clean = len(per_file_results) - total_flagged

    summary = {
        'tool': 'tfsec',
        'binary_used': binary,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds': round(elapsed, 2),
        'total_policies': len(tf_files),
        'policies_flagged': total_flagged,
        'policies_clean': total_clean,
        'detection_rate': round(total_flagged / len(tf_files), 4) if tf_files else 0,
        'note': 'tfsec has limited IAM policy analysis; minimal findings expected',
    }

    output = {
        'summary': summary,
        'per_policy_results': per_file_results,
        'directory_result': dir_result,
    }

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"tfsec Results Summary")
    print(f"{'='*60}")
    print(f"  Total policies scanned: {len(tf_files)}")
    print(f"  Policies flagged:       {total_flagged}")
    print(f"  Policies clean:         {total_clean}")
    print(f"  Detection rate:         {summary['detection_rate']:.2%}")
    print(f"  Time elapsed:           {elapsed:.1f}s")
    print(f"  Results saved to:       {OUTPUT_FILE}")
    print(f"\n  Note: tfsec is primarily a Terraform misconfiguration scanner")
    print(f"  and has limited support for IAM policy vulnerability detection.")

    return 0


def _create_placeholder_results():
    """Create placeholder results when tfsec is not available."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    output = {
        'summary': {
            'tool': 'tfsec',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'NOT_AVAILABLE',
            'note': 'tfsec was not installed. Install it and re-run.',
            'total_policies': 0,
            'policies_flagged': 0,
            'detection_rate': 0,
        },
        'per_policy_results': {},
    }
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"[INFO] Placeholder results saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    sys.exit(main())
