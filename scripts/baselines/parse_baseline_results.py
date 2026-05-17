#!/usr/bin/env python3
"""
Parse baseline tool results and compute classification metrics.

Loads ground truth labels from data/raw/samples/LABELS.json and results
from each baseline tool, computing TP, FP, TN, FN, Precision, Recall,
F1-Score, and Accuracy for each tool.

Saves individual tool metrics to results/<tool>_metrics.json.
"""

import json
import os
import sys
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LABELS_FILE = os.path.join(PROJECT_ROOT, 'data', 'raw', 'samples', 'LABELS.json')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')

# Result files from each tool
CHECKOV_RESULTS = os.path.join(RESULTS_DIR, 'checkov_results.json')
TFSEC_RESULTS = os.path.join(RESULTS_DIR, 'tfsec_results.json')
IAM_ANALYZER_RESULTS = os.path.join(RESULTS_DIR, 'iam_analyzer_results.json')
POLICYGRAPH_RESULTS = os.path.join(RESULTS_DIR, 'evaluation_report.json')


def load_ground_truth() -> dict:
    """Load ground truth labels. Returns dict: policy_name -> label ('vulnerable'/'secure')."""
    with open(LABELS_FILE, 'r') as f:
        data = json.load(f)

    labels = {}
    for entry in data.get('labels', []):
        name = os.path.splitext(entry['filename'])[0]
        labels[name] = {
            'label': entry['label'],
            'vulnerability_type': entry.get('vulnerability_type', 'none'),
            'severity': entry.get('severity', 'low'),
            'is_vulnerable': entry['label'] == 'vulnerable',
        }
    return labels


def load_checkov_results() -> dict:
    """Load Checkov results. Returns dict: policy_name -> flagged (bool)."""
    if not os.path.exists(CHECKOV_RESULTS):
        print(f"[WARN] Checkov results not found: {CHECKOV_RESULTS}")
        return None

    with open(CHECKOV_RESULTS, 'r') as f:
        data = json.load(f)

    predictions = {}
    for policy_name, result in data.get('per_policy_results', {}).items():
        findings = result.get('findings', {})
        predictions[policy_name] = findings.get('has_issues', False)

    return predictions


def load_tfsec_results() -> dict:
    """Load tfsec results. Returns dict: policy_name -> flagged (bool)."""
    if not os.path.exists(TFSEC_RESULTS):
        print(f"[WARN] tfsec results not found: {TFSEC_RESULTS}")
        return None

    with open(TFSEC_RESULTS, 'r') as f:
        data = json.load(f)

    if data.get('summary', {}).get('status') == 'NOT_AVAILABLE':
        print(f"[WARN] tfsec was not available when results were generated")
        return None

    predictions = {}
    for policy_name, result in data.get('per_policy_results', {}).items():
        findings = result.get('findings', {})
        predictions[policy_name] = findings.get('has_issues', False)

    return predictions


def load_iam_analyzer_results() -> dict:
    """Load IAM Access Analyzer results. Returns dict: policy_name -> flagged (bool)."""
    if not os.path.exists(IAM_ANALYZER_RESULTS):
        print(f"[WARN] IAM Analyzer results not found: {IAM_ANALYZER_RESULTS}")
        return None

    with open(IAM_ANALYZER_RESULTS, 'r') as f:
        data = json.load(f)

    if data.get('summary', {}).get('status') == 'CREDENTIALS_REQUIRED':
        print(f"[WARN] IAM Analyzer requires AWS credentials")
        return None

    predictions = {}
    for policy_name, result in data.get('per_policy_results', {}).items():
        findings = result.get('findings', {})
        predictions[policy_name] = findings.get('has_security_issues', False)

    return predictions


def load_policygraph_results() -> dict:
    """Load PolicyGraph evaluation results."""
    if not os.path.exists(POLICYGRAPH_RESULTS):
        print(f"[WARN] PolicyGraph results not found: {POLICYGRAPH_RESULTS}")
        return None

    with open(POLICYGRAPH_RESULTS, 'r') as f:
        data = json.load(f)

    return data


def compute_metrics(ground_truth: dict, predictions: dict, tool_name: str) -> dict:
    """
    Compute classification metrics.

    ground_truth: policy_name -> {is_vulnerable: bool, ...}
    predictions: policy_name -> flagged (bool)

    A 'flagged' policy is predicted as vulnerable (positive).
    """
    tp = fp = tn = fn = 0
    per_policy = {}
    vulnerability_type_stats = {}

    for policy_name, truth in ground_truth.items():
        is_vulnerable = truth['is_vulnerable']
        predicted_vulnerable = predictions.get(policy_name, False)

        if is_vulnerable and predicted_vulnerable:
            tp += 1
            classification = 'TP'
        elif not is_vulnerable and predicted_vulnerable:
            fp += 1
            classification = 'FP'
        elif not is_vulnerable and not predicted_vulnerable:
            tn += 1
            classification = 'TN'
        else:  # is_vulnerable and not predicted_vulnerable
            fn += 1
            classification = 'FN'

        per_policy[policy_name] = {
            'ground_truth': truth['label'],
            'predicted_vulnerable': predicted_vulnerable,
            'classification': classification,
            'vulnerability_type': truth['vulnerability_type'],
            'severity': truth['severity'],
        }

        # Track per vulnerability type
        vtype = truth['vulnerability_type']
        if vtype not in vulnerability_type_stats:
            vulnerability_type_stats[vtype] = {'total': 0, 'detected': 0, 'missed': 0}
        if is_vulnerable:
            vulnerability_type_stats[vtype]['total'] += 1
            if predicted_vulnerable:
                vulnerability_type_stats[vtype]['detected'] += 1
            else:
                vulnerability_type_stats[vtype]['missed'] += 1

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 0.0

    # Detection rate per vulnerability type
    for vtype, stats in vulnerability_type_stats.items():
        stats['detection_rate'] = (
            stats['detected'] / stats['total'] if stats['total'] > 0 else 0.0
        )

    metrics = {
        'tool': tool_name,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'confusion_matrix': {
            'true_positives': tp,
            'false_positives': fp,
            'true_negatives': tn,
            'false_negatives': fn,
        },
        'metrics': {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'f1_score': round(f1, 4),
            'accuracy': round(accuracy, 4),
        },
        'summary': {
            'total_policies': total,
            'total_vulnerable': tp + fn,
            'total_secure': tn + fp,
            'correctly_classified': tp + tn,
            'misclassified': fp + fn,
        },
        'vulnerability_type_detection': vulnerability_type_stats,
        'per_policy_classification': per_policy,
    }

    return metrics


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    print(f"{'='*60}")
    print(f"Baseline Results Parser")
    print(f"{'='*60}")

    # Load ground truth
    print("[INFO] Loading ground truth labels...")
    ground_truth = load_ground_truth()
    vulnerable_count = sum(1 for v in ground_truth.values() if v['is_vulnerable'])
    secure_count = len(ground_truth) - vulnerable_count
    print(f"  Total: {len(ground_truth)}, Vulnerable: {vulnerable_count}, Secure: {secure_count}")

    # Load and process each tool's results
    tools = {
        'checkov': load_checkov_results,
        'tfsec': load_tfsec_results,
        'iam_access_analyzer': load_iam_analyzer_results,
    }

    all_metrics = {}

    for tool_name, loader in tools.items():
        print(f"\n[INFO] Processing {tool_name}...")
        predictions = loader()

        if predictions is None:
            print(f"  [SKIP] No results available for {tool_name}")
            continue

        print(f"  Loaded {len(predictions)} predictions")
        print(f"  Flagged: {sum(1 for v in predictions.values() if v)}")
        print(f"  Clean:   {sum(1 for v in predictions.values() if not v)}")

        metrics = compute_metrics(ground_truth, predictions, tool_name)
        all_metrics[tool_name] = metrics

        # Save individual metrics
        metrics_file = os.path.join(RESULTS_DIR, f'{tool_name}_metrics.json')
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"  Saved metrics to: {metrics_file}")

        # Print summary
        m = metrics['metrics']
        cm = metrics['confusion_matrix']
        print(f"\n  {tool_name} Metrics:")
        print(f"    Precision: {m['precision']:.4f}")
        print(f"    Recall:    {m['recall']:.4f}")
        print(f"    F1-Score:  {m['f1_score']:.4f}")
        print(f"    Accuracy:  {m['accuracy']:.4f}")
        print(f"    TP={cm['true_positives']} FP={cm['false_positives']} "
              f"TN={cm['true_negatives']} FN={cm['false_negatives']}")

    # Handle PolicyGraph results separately (different format)
    print(f"\n[INFO] Processing PolicyGraph...")
    pg_results = load_policygraph_results()
    if pg_results:
        pg_metrics = pg_results.get('metrics', {})
        all_metrics['policygraph'] = {
            'tool': 'policygraph',
            'metrics': {
                'precision': round(pg_metrics.get('precision', 0), 4),
                'recall': round(pg_metrics.get('recall', 0), 4),
                'f1_score': round(pg_metrics.get('f1', 0), 4),
                'accuracy': round(pg_metrics.get('accuracy', 0), 4),
            },
            'confusion_matrix_raw': pg_results.get('confusion_matrix', []),
            'per_category': pg_results.get('per_category', {}),
            'source': 'evaluation_report.json',
        }
        print(f"  PolicyGraph Metrics:")
        pm = all_metrics['policygraph']['metrics']
        print(f"    Precision: {pm['precision']:.4f}")
        print(f"    Recall:    {pm['recall']:.4f}")
        print(f"    F1-Score:  {pm['f1_score']:.4f}")
        print(f"    Accuracy:  {pm['accuracy']:.4f}")
    else:
        print(f"  [SKIP] PolicyGraph results not available")

    # Save combined metrics
    combined_file = os.path.join(RESULTS_DIR, 'all_baseline_metrics.json')
    with open(combined_file, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    print(f"\n[INFO] Combined metrics saved to: {combined_file}")

    print(f"\n{'='*60}")
    print(f"Parsing Complete")
    print(f"{'='*60}")
    print(f"  Tools processed: {len(all_metrics)}")
    print(f"  Results directory: {RESULTS_DIR}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
