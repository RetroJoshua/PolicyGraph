"""Shared utilities for configuration, logging, metrics, and visualization."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import yaml
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score


def setup_logging(name: str = "policygraph", level: int = logging.INFO) -> logging.Logger:
    """Create or reuse a configured logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Load YAML config file and return dict."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError("Config file must define a YAML dictionary")
    return config


def calculate_classification_metrics(y_true: Iterable[int], y_prob: Iterable[float]) -> Dict[str, float]:
    """Compute standard binary classification metrics."""
    y_true_arr = np.asarray(list(y_true), dtype=np.int64)
    y_prob_arr = np.asarray(list(y_prob), dtype=np.float32)
    y_pred = (y_prob_arr >= 0.5).astype(np.int64)

    metrics = {
        "accuracy": float(accuracy_score(y_true_arr, y_pred)),
        "precision": float(precision_score(y_true_arr, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true_arr, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true_arr, y_pred, zero_division=0)),
    }
    try:
        metrics["roc_auc"] = float(roc_auc_score(y_true_arr, y_prob_arr))
    except ValueError:
        metrics["roc_auc"] = 0.0
    return metrics


def save_json(data: Dict[str, Any], path: str) -> None:
    """Save dictionary to JSON with pretty formatting."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)


def plot_confusion_matrix(cm: List[List[int]], output_path: str) -> None:
    """Save confusion matrix heatmap image."""
    array = np.asarray(cm)
    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(array, cmap="Blues")
    fig.colorbar(im)
    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["Secure", "Vulnerable"])
    ax.set_yticklabels(["Secure", "Vulnerable"])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    for i in range(array.shape[0]):
        for j in range(array.shape[1]):
            ax.text(j, i, str(array[i, j]), ha="center", va="center", color="black")
    fig.tight_layout()
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
