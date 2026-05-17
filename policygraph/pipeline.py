"""Reusable training and evaluation pipelines."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import confusion_matrix
from torch.optim import Adam
from tqdm import tqdm

from policygraph.analyzer import PolicyAnalyzer
from policygraph.dataset import PolicyDataset
from policygraph.models import GATPolicyRiskModel
from policygraph.utils import calculate_classification_metrics, plot_confusion_matrix, save_json, setup_logging


def _train_one_epoch(model, dataloader, optimizer, criterion, device):
    model.train()
    total_loss = 0.0
    all_probs = []
    all_labels = []

    for graphs, labels, _ in dataloader:
        graphs = graphs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        output = model(graphs)
        loss = criterion(output["logits"], labels)
        loss.backward()
        optimizer.step()

        total_loss += float(loss.item())
        all_probs.extend(output["risk_score"].detach().cpu().tolist())
        all_labels.extend(labels.detach().cpu().tolist())

    metrics = calculate_classification_metrics([int(x) for x in all_labels], all_probs)
    metrics["loss"] = total_loss / max(1, len(dataloader))
    return metrics


def _evaluate(model, dataloader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_probs = []
    all_labels = []

    with torch.no_grad():
        for graphs, labels, _ in dataloader:
            graphs = graphs.to(device)
            labels = labels.to(device)
            output = model(graphs)
            loss = criterion(output["logits"], labels)
            total_loss += float(loss.item())
            all_probs.extend(output["risk_score"].detach().cpu().tolist())
            all_labels.extend(labels.detach().cpu().tolist())

    metrics = calculate_classification_metrics([int(x) for x in all_labels], all_probs)
    metrics["loss"] = total_loss / max(1, len(dataloader))
    return metrics


def run_training(config: Dict[str, Any]) -> str:
    logger = setup_logging("policygraph.train")
    data_cfg = config["data"]
    model_cfg = config["model"]
    train_cfg = config["training"]

    dataset = PolicyDataset(data_dir=data_cfg["samples_dir"], labels_file=data_cfg["labels_file"])
    train_loader = dataset.get_dgl_dataloader("train", batch_size=train_cfg["batch_size"], shuffle=True)
    val_loader = dataset.get_dgl_dataloader("val", batch_size=train_cfg["batch_size"], shuffle=False)

    device = torch.device(train_cfg.get("device", "cuda" if torch.cuda.is_available() else "cpu"))
    model = GATPolicyRiskModel(
        in_dim=model_cfg["in_dim"],
        hidden_dim=model_cfg["hidden_dim"],
        num_layers=model_cfg["num_layers"],
        num_heads=model_cfg["num_heads"],
        dropout=model_cfg["dropout"],
    ).to(device)
    optimizer = Adam(model.parameters(), lr=train_cfg["learning_rate"], weight_decay=train_cfg["weight_decay"])

    train_split = dataset.get_split("train")
    pos_count = sum(sample.label for sample in train_split)
    neg_count = len(train_split) - pos_count
    pos_weight = torch.tensor([neg_count / max(1, pos_count)], dtype=torch.float32, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    output_dir = Path(train_cfg["checkpoint_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_log_path = output_dir / "training_metrics.csv"

    best_val_f1 = -1.0
    best_path = output_dir / "best_model.pt"
    patience = train_cfg["early_stopping_patience"]
    wait = 0

    with csv_log_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "epoch",
                "train_loss",
                "train_accuracy",
                "train_precision",
                "train_recall",
                "train_f1",
                "val_loss",
                "val_accuracy",
                "val_precision",
                "val_recall",
                "val_f1",
            ],
        )
        writer.writeheader()

        for epoch in tqdm(range(1, train_cfg["epochs"] + 1), desc="Training"):
            train_metrics = _train_one_epoch(model, train_loader, optimizer, criterion, device)
            val_metrics = _evaluate(model, val_loader, criterion, device)

            writer.writerow(
                {
                    "epoch": epoch,
                    "train_loss": train_metrics["loss"],
                    "train_accuracy": train_metrics["accuracy"],
                    "train_precision": train_metrics["precision"],
                    "train_recall": train_metrics["recall"],
                    "train_f1": train_metrics["f1"],
                    "val_loss": val_metrics["loss"],
                    "val_accuracy": val_metrics["accuracy"],
                    "val_precision": val_metrics["precision"],
                    "val_recall": val_metrics["recall"],
                    "val_f1": val_metrics["f1"],
                }
            )
            csv_file.flush()

            logger.info(
                "Epoch %s | train_f1=%.4f val_f1=%.4f val_loss=%.4f",
                epoch,
                train_metrics["f1"],
                val_metrics["f1"],
                val_metrics["loss"],
            )

            if val_metrics["f1"] > best_val_f1:
                best_val_f1 = val_metrics["f1"]
                wait = 0
                torch.save(
                    {
                        "epoch": epoch,
                        "model_state_dict": model.state_dict(),
                        "optimizer_state_dict": optimizer.state_dict(),
                        "val_metrics": val_metrics,
                        "config": config,
                    },
                    best_path,
                )
            else:
                wait += 1
                if wait >= patience:
                    logger.info("Early stopping triggered at epoch %s", epoch)
                    break

    logger.info("Training complete. Best checkpoint: %s", best_path)
    return str(best_path)


def _category_from_vuln_type(vulnerability_type: str) -> str:
    value = vulnerability_type.lower()
    if "sts" in value or "assume_role" in value or "role_chaining" in value:
        return "STS"
    if "cloudformation" in value:
        return "CloudFormation"
    if "passrole" in value:
        return "PassRole"
    if "attach" in value or "put_" in value or "policy" in value:
        return "PolicyManipulation"
    if "login" in value or "access_key" in value:
        return "CredentialEscalation"
    return "Other"


def run_evaluation(config: Dict[str, Any], model_path: str) -> Dict[str, Any]:
    logger = setup_logging("policygraph.evaluate")
    data_cfg = config["data"]
    eval_cfg = config["evaluation"]

    dataset = PolicyDataset(data_dir=data_cfg["samples_dir"], labels_file=data_cfg["labels_file"])
    test_samples = dataset.get_split("test")
    analyzer = PolicyAnalyzer(model_path=model_path, threshold=eval_cfg["threshold"])

    y_true: List[int] = []
    y_prob: List[float] = []
    by_category: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: {"y_true": [], "y_prob": []})

    for sample in test_samples:
        result = analyzer.analyze_policy(sample.policy)
        y_true.append(sample.label)
        y_prob.append(result["risk_score"])

        category = _category_from_vuln_type(sample.vulnerability_type)
        by_category[category]["y_true"].append(sample.label)
        by_category[category]["y_prob"].append(result["risk_score"])

    metrics = calculate_classification_metrics(y_true, y_prob)
    cm = confusion_matrix(np.asarray(y_true), (np.asarray(y_prob) >= eval_cfg["threshold"]).astype(int)).tolist()
    per_category = {
        category: calculate_classification_metrics(values["y_true"], values["y_prob"])
        for category, values in by_category.items()
    }

    output = {
        "metrics": metrics,
        "confusion_matrix": cm,
        "per_category": per_category,
        "num_test_samples": len(test_samples),
        "model_path": model_path,
    }

    report_path = Path(eval_cfg["report_path"])
    save_json(output, str(report_path))
    plot_confusion_matrix(cm, str(report_path.with_suffix(".png")))
    logger.info("Evaluation report written to %s", report_path)
    return output
