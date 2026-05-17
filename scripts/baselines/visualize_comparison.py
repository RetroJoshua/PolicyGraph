#!/usr/bin/env python3
"""
Generate publication-ready visualizations comparing baseline tools.

Creates:
  - Bar charts comparing metrics across tools
  - Confusion matrix heatmaps for each tool
  - Radar chart for multi-dimensional comparison
  - Detection rate comparison by vulnerability type

All plots saved to results/figures/.
"""

import json
import os
import sys
import numpy as np
from datetime import datetime, timezone

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
FIGURES_DIR = os.path.join(RESULTS_DIR, 'figures')
ALL_METRICS_FILE = os.path.join(RESULTS_DIR, 'all_baseline_metrics.json')

# Publication-quality settings
FIGSIZE_WIDE = (12, 6)
FIGSIZE_SQUARE = (8, 8)
FIGSIZE_SMALL = (8, 6)
DPI = 300
FONT_SIZE = 12

# Color scheme
COLORS = {
    'policygraph': '#2196F3',    # Blue
    'checkov': '#FF9800',        # Orange
    'tfsec': '#4CAF50',          # Green
    'iam_access_analyzer': '#9C27B0',  # Purple
}

TOOL_DISPLAY = {
    'policygraph': 'PolicyGraph\n(Ours)',
    'checkov': 'Checkov',
    'tfsec': 'tfsec',
    'iam_access_analyzer': 'IAM Access\nAnalyzer',
}


def load_metrics() -> dict:
    """Load all metrics."""
    if not os.path.exists(ALL_METRICS_FILE):
        # Try individual files
        metrics = {}
        for tool in ['checkov', 'tfsec', 'iam_access_analyzer']:
            fp = os.path.join(RESULTS_DIR, f'{tool}_metrics.json')
            if os.path.exists(fp):
                with open(fp, 'r') as f:
                    metrics[tool] = json.load(f)

        pg_file = os.path.join(RESULTS_DIR, 'evaluation_report.json')
        if os.path.exists(pg_file):
            with open(pg_file, 'r') as f:
                pg = json.load(f)
            pg_m = pg.get('metrics', {})
            metrics['policygraph'] = {
                'tool': 'policygraph',
                'metrics': {
                    'precision': pg_m.get('precision', 0),
                    'recall': pg_m.get('recall', 0),
                    'f1_score': pg_m.get('f1', 0),
                    'accuracy': pg_m.get('accuracy', 0),
                },
                'confusion_matrix': {
                    'true_positives': pg.get('confusion_matrix', [[0,0],[0,0]])[1][1] if pg.get('confusion_matrix') else 0,
                    'false_positives': pg.get('confusion_matrix', [[0,0],[0,0]])[0][1] if pg.get('confusion_matrix') else 0,
                    'true_negatives': pg.get('confusion_matrix', [[0,0],[0,0]])[0][0] if pg.get('confusion_matrix') else 0,
                    'false_negatives': pg.get('confusion_matrix', [[0,0],[0,0]])[1][0] if pg.get('confusion_matrix') else 0,
                },
            }
        return metrics

    with open(ALL_METRICS_FILE, 'r') as f:
        return json.load(f)


def plot_metrics_bar_chart(metrics: dict):
    """Generate bar chart comparing Precision, Recall, F1, Accuracy."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    tool_order = ['checkov', 'tfsec', 'iam_access_analyzer', 'policygraph']
    tools = [t for t in tool_order if t in metrics]

    if not tools:
        print("[WARN] No tools with metrics to plot")
        return

    metric_names = ['Precision', 'Recall', 'F1-Score', 'Accuracy']
    metric_keys = ['precision', 'recall', 'f1_score', 'accuracy']

    x = np.arange(len(metric_names))
    width = 0.8 / len(tools)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    for i, tool in enumerate(tools):
        m = metrics[tool].get('metrics', {})
        values = [m.get(k, 0) for k in metric_keys]
        color = COLORS.get(tool, '#999999')
        label = TOOL_DISPLAY.get(tool, tool).replace('\n', ' ')
        bars = ax.bar(x + i * width - (len(tools)-1)*width/2, values, width,
                      label=label, color=color, edgecolor='white', linewidth=0.5)

        # Add value labels
        for bar, val in zip(bars, values):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                       f'{val:.2f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_xlabel('Metric', fontsize=FONT_SIZE)
    ax.set_ylabel('Score', fontsize=FONT_SIZE)
    ax.set_title('Baseline Tool Comparison: Classification Metrics', fontsize=FONT_SIZE + 2, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names, fontsize=FONT_SIZE)
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=10, loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    filepath = os.path.join(FIGURES_DIR, 'metrics_comparison_bar.png')
    plt.savefig(filepath, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def plot_confusion_matrices(metrics: dict):
    """Generate confusion matrix heatmaps for each tool."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    tools_with_cm = [t for t in metrics if 'confusion_matrix' in metrics[t]
                     and isinstance(metrics[t]['confusion_matrix'], dict)]

    if not tools_with_cm:
        print("[WARN] No tools with confusion matrix data")
        return

    n_tools = len(tools_with_cm)
    fig, axes = plt.subplots(1, n_tools, figsize=(5 * n_tools, 4))
    if n_tools == 1:
        axes = [axes]

    for ax, tool in zip(axes, tools_with_cm):
        cm = metrics[tool]['confusion_matrix']
        matrix = np.array([
            [cm.get('true_negatives', 0), cm.get('false_positives', 0)],
            [cm.get('false_negatives', 0), cm.get('true_positives', 0)]
        ])

        im = ax.imshow(matrix, cmap='Blues', aspect='auto')

        # Add text annotations
        for i in range(2):
            for j in range(2):
                color = 'white' if matrix[i, j] > matrix.max() / 2 else 'black'
                ax.text(j, i, str(int(matrix[i, j])),
                       ha='center', va='center', fontsize=14, fontweight='bold', color=color)

        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(['Predicted\nSecure', 'Predicted\nVulnerable'], fontsize=10)
        ax.set_yticklabels(['Actually\nSecure', 'Actually\nVulnerable'], fontsize=10)
        display_name = TOOL_DISPLAY.get(tool, tool).replace('\n', ' ')
        ax.set_title(display_name, fontsize=FONT_SIZE, fontweight='bold')

    plt.suptitle('Confusion Matrices', fontsize=FONT_SIZE + 2, fontweight='bold', y=1.05)
    plt.tight_layout()
    filepath = os.path.join(FIGURES_DIR, 'confusion_matrices.png')
    plt.savefig(filepath, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def plot_radar_chart(metrics: dict):
    """Generate radar/spider chart for multi-dimensional comparison."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    tool_order = ['checkov', 'tfsec', 'iam_access_analyzer', 'policygraph']
    tools = [t for t in tool_order if t in metrics]

    if len(tools) < 2:
        print("[WARN] Need at least 2 tools for radar chart")
        return

    categories = ['Precision', 'Recall', 'F1-Score', 'Accuracy']
    keys = ['precision', 'recall', 'f1_score', 'accuracy']
    N = len(categories)

    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the plot

    fig, ax = plt.subplots(figsize=FIGSIZE_SQUARE, subplot_kw=dict(polar=True))

    for tool in tools:
        m = metrics[tool].get('metrics', {})
        values = [m.get(k, 0) for k in keys]
        values += values[:1]  # Close the plot

        color = COLORS.get(tool, '#999999')
        label = TOOL_DISPLAY.get(tool, tool).replace('\n', ' ')
        ax.plot(angles, values, 'o-', linewidth=2, label=label, color=color)
        ax.fill(angles, values, alpha=0.1, color=color)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=FONT_SIZE)
    ax.set_ylim(0, 1.0)
    ax.set_title('Multi-Dimensional Tool Comparison', fontsize=FONT_SIZE + 2,
                 fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1), fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = os.path.join(FIGURES_DIR, 'radar_comparison.png')
    plt.savefig(filepath, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def plot_detection_by_severity(metrics: dict):
    """Generate detection rate by severity level."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    # Extract per-policy classifications and compute severity-based detection
    tool_order = ['checkov', 'tfsec', 'iam_access_analyzer', 'policygraph']
    tools = [t for t in tool_order if t in metrics]

    if not tools:
        return

    severities = ['critical', 'high', 'medium']
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)

    x = np.arange(len(severities))
    width = 0.8 / len(tools)

    for i, tool in enumerate(tools):
        per_policy = metrics[tool].get('per_policy_classification', {})
        if not per_policy:
            continue

        rates = []
        for sev in severities:
            total = sum(1 for p in per_policy.values()
                       if p.get('severity') == sev and p.get('ground_truth') == 'vulnerable')
            detected = sum(1 for p in per_policy.values()
                          if p.get('severity') == sev and p.get('classification') == 'TP')
            rates.append(detected / total if total > 0 else 0)

        color = COLORS.get(tool, '#999999')
        label = TOOL_DISPLAY.get(tool, tool).replace('\n', ' ')
        bars = ax.bar(x + i * width - (len(tools)-1)*width/2, rates, width,
                      label=label, color=color, edgecolor='white', linewidth=0.5)

        for bar, val in zip(bars, rates):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                       f'{val:.0%}', ha='center', va='bottom', fontsize=9)

    ax.set_xlabel('Severity Level', fontsize=FONT_SIZE)
    ax.set_ylabel('Detection Rate', fontsize=FONT_SIZE)
    ax.set_title('Detection Rate by Vulnerability Severity', fontsize=FONT_SIZE + 2, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.capitalize() for s in severities], fontsize=FONT_SIZE)
    ax.set_ylim(0, 1.15)
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    filepath = os.path.join(FIGURES_DIR, 'detection_by_severity.png')
    plt.savefig(filepath, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def plot_f1_comparison(metrics: dict):
    """Generate a horizontal bar chart focused on F1-Score."""
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')

    tool_order = ['policygraph', 'iam_access_analyzer', 'checkov', 'tfsec']
    tools = [t for t in tool_order if t in metrics]

    if not tools:
        return

    fig, ax = plt.subplots(figsize=FIGSIZE_SMALL)

    f1_scores = []
    labels = []
    colors = []

    for tool in tools:
        m = metrics[tool].get('metrics', {})
        f1 = m.get('f1_score', 0)
        f1_scores.append(f1)
        labels.append(TOOL_DISPLAY.get(tool, tool).replace('\n', ' '))
        colors.append(COLORS.get(tool, '#999999'))

    y = np.arange(len(tools))
    bars = ax.barh(y, f1_scores, color=colors, edgecolor='white', linewidth=0.5, height=0.6)

    for bar, val in zip(bars, f1_scores):
        ax.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2.,
               f'{val:.4f}', ha='left', va='center', fontsize=11, fontweight='bold')

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=FONT_SIZE)
    ax.set_xlabel('F1-Score', fontsize=FONT_SIZE)
    ax.set_title('F1-Score Comparison', fontsize=FONT_SIZE + 2, fontweight='bold')
    ax.set_xlim(0, 1.15)
    ax.grid(axis='x', alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    filepath = os.path.join(FIGURES_DIR, 'f1_comparison.png')
    plt.savefig(filepath, dpi=DPI, bbox_inches='tight')
    plt.close()
    print(f"  Saved: {filepath}")


def main():
    os.makedirs(FIGURES_DIR, exist_ok=True)

    print(f"{'='*60}")
    print(f"Visualization Generator")
    print(f"{'='*60}")

    # Load metrics
    print("[INFO] Loading metrics...")
    metrics = load_metrics()
    print(f"  Tools: {list(metrics.keys())}")

    if not metrics:
        print("[ERROR] No metrics available. Run parse_baseline_results.py first.")
        sys.exit(1)

    # Generate each visualization
    print("\n[INFO] Generating visualizations...")

    print("\n  1. Metrics comparison bar chart...")
    try:
        plot_metrics_bar_chart(metrics)
    except Exception as e:
        print(f"    [ERROR] {e}")

    print("\n  2. Confusion matrix heatmaps...")
    try:
        plot_confusion_matrices(metrics)
    except Exception as e:
        print(f"    [ERROR] {e}")

    print("\n  3. Radar chart...")
    try:
        plot_radar_chart(metrics)
    except Exception as e:
        print(f"    [ERROR] {e}")

    print("\n  4. Detection by severity...")
    try:
        plot_detection_by_severity(metrics)
    except Exception as e:
        print(f"    [ERROR] {e}")

    print("\n  5. F1-Score comparison...")
    try:
        plot_f1_comparison(metrics)
    except Exception as e:
        print(f"    [ERROR] {e}")

    print(f"\n{'='*60}")
    print(f"Visualization Complete")
    print(f"{'='*60}")
    print(f"  Output directory: {FIGURES_DIR}")
    print(f"  Files generated: {len([f for f in os.listdir(FIGURES_DIR) if f.endswith('.png')])}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
