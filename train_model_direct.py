import json
import sys
import torch
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix, accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, str(Path.cwd()))

from policygraph.dataset import PolicyDataset
from policygraph.models import GATPolicyRiskModel
from policygraph.utils import setup_logging, calculate_classification_metrics
from torch.optim import Adam
import torch.nn as nn
from tqdm import tqdm

def train_model():
    """Train GNN model on 500-policy dataset"""
    logger = setup_logging("policygraph.train")
    
    output_dir = Path("checkpoints")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Loading dataset from data/raw/samples...")
    dataset = PolicyDataset(
        data_dir="data/raw/samples",
        labels_file="data/raw/samples/LABELS.json"
    )
    logger.info(f"Loaded {len(dataset.samples)} policies")
    
    device = torch.device("cpu")
    logger.info(f"Using device: {device}")
    
    train_loader = dataset.get_dgl_dataloader("train", batch_size=16, shuffle=True)
    val_loader = dataset.get_dgl_dataloader("val", batch_size=16, shuffle=False)
    test_loader = dataset.get_dgl_dataloader("test", batch_size=16, shuffle=False)
    
    logger.info(f"Train samples: {len(dataset.get_split('train'))}")
    logger.info(f"Val samples: {len(dataset.get_split('val'))}")
    logger.info(f"Test samples: {len(dataset.get_split('test'))}")
    
    model = GATPolicyRiskModel(
        in_dim=6,
        hidden_dim=64,
        num_layers=3,
        num_heads=4,
        dropout=0.2,
    ).to(device)
    
    optimizer = Adam(model.parameters(), lr=0.001, weight_decay=0.0001)
    
    train_split = dataset.get_split("train")
    pos_count = sum(sample.label for sample in train_split)
    neg_count = len(train_split) - pos_count
    pos_weight = torch.tensor([neg_count / max(1, pos_count)], dtype=torch.float32, device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    
    logger.info(f"Loss function: BCEWithLogitsLoss with pos_weight={pos_weight.item():.3f}")
    
    best_val_f1 = -1.0
    best_model_path = output_dir / "best_model.pt"
    csv_log_path = output_dir / "training_metrics.csv"
    
    logger.info(f"Starting training for 200 epochs...")
    
    csv_log = open(csv_log_path, "w")
    csv_log.write("epoch,train_loss,train_f1,val_loss,val_f1\n")
    
    for epoch in range(200):
        model.train()
        total_loss = 0.0
        all_probs = []
        all_labels = []
        
        for graphs, labels, _ in train_loader:
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
        
        train_metrics = calculate_classification_metrics([int(x) for x in all_labels], all_probs)
        train_loss = total_loss / max(1, len(train_loader))
        
        model.eval()
        val_total_loss = 0.0
        val_all_probs = []
        val_all_labels = []
        
        with torch.no_grad():
            for graphs, labels, _ in val_loader:
                graphs = graphs.to(device)
                labels = labels.to(device)
                output = model(graphs)
                loss = criterion(output["logits"], labels)
                val_total_loss += float(loss.item())
                val_all_probs.extend(output["risk_score"].detach().cpu().tolist())
                val_all_labels.extend(labels.detach().cpu().tolist())
        
        val_metrics = calculate_classification_metrics([int(x) for x in val_all_labels], val_all_probs)
        val_loss = val_total_loss / max(1, len(val_loader))
        
        csv_log.write(f"{epoch+1},{train_loss:.4f},{train_metrics['f1']:.4f},{val_loss:.4f},{val_metrics['f1']:.4f}\n")
        
        if val_metrics['f1'] > best_val_f1:
            best_val_f1 = val_metrics['f1']
            torch.save(model.state_dict(), best_model_path)
            logger.info(f"Epoch {epoch+1}/200 - Train Loss: {train_loss:.4f}, Train F1: {train_metrics['f1']:.4f}, Val Loss: {val_loss:.4f}, Val F1: {val_metrics['f1']:.4f} (BEST)")
        elif (epoch + 1) % 20 == 0:
            logger.info(f"Epoch {epoch+1}/200 - Train Loss: {train_loss:.4f}, Train F1: {train_metrics['f1']:.4f}, Val Loss: {val_loss:.4f}, Val F1: {val_metrics['f1']:.4f}")
    
    csv_log.close()
    logger.info(f"\nTraining complete! Best model saved to: {best_model_path}")
    
    logger.info("\n" + "="*70)
    logger.info("EVALUATING ON TEST SET")
    logger.info("="*70)
    
    model.load_state_dict(torch.load(best_model_path))
    model.eval()
    
    test_all_probs = []
    test_all_labels = []
    
    with torch.no_grad():
        for graphs, labels, _ in test_loader:
            graphs = graphs.to(device)
            labels = labels.to(device)
            output = model(graphs)
            test_all_probs.extend(output["risk_score"].detach().cpu().tolist())
            test_all_labels.extend(labels.detach().cpu().tolist())
    
    test_labels_int = [int(x) for x in test_all_labels]
    test_probs_binary = [1 if p > 0.5 else 0 for p in test_all_probs]
    
    precision = precision_score(test_labels_int, test_probs_binary, zero_division=0)
    recall = recall_score(test_labels_int, test_probs_binary, zero_division=0)
    f1 = f1_score(test_labels_int, test_probs_binary, zero_division=0)
    accuracy = accuracy_score(test_labels_int, test_probs_binary)
    roc_auc = roc_auc_score(test_labels_int, test_all_probs) if len(np.unique(test_labels_int)) > 1 else 0.0
    
    tn, fp, fn, tp = confusion_matrix(test_labels_int, test_probs_binary).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    results = {
        "dataset": {
            "total_policies": 500,
            "original_policies": 269,
            "synthetic_policies": 231,
            "train_samples": len(dataset.get_split('train')),
            "val_samples": len(dataset.get_split('val')),
            "test_samples": len(dataset.get_split('test')),
            "vulnerable_count": sum(1 for s in dataset.samples if s.label == 1),
            "safe_count": sum(1 for s in dataset.samples if s.label == 0)
        },
        "model": {
            "type": "GAT (Graph Attention Network)",
            "input_dim": 6,
            "hidden_dim": 64,
            "num_layers": 3,
            "num_heads": 4,
            "dropout": 0.2,
            "loss_function": "BCEWithLogitsLoss with pos_weight"
        },
        "training": {
            "epochs": 200,
            "learning_rate": 0.001,
            "weight_decay": 0.0001,
            "batch_size": 16,
            "device": "cpu",
            "best_epoch": "See training_metrics.csv"
        },
        "test_metrics": {
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "accuracy": float(accuracy),
            "roc_auc": float(roc_auc),
            "specificity": float(specificity),
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "interpretation": {
            "precision": f"Of all predicted vulnerable policies, {precision*100:.1f}% were actually vulnerable",
            "recall": f"Of all actually vulnerable policies, {recall*100:.1f}% were correctly identified",
            "f1_score": f"Harmonic mean of precision and recall: {f1:.4f}",
            "accuracy": f"Overall correctness: {accuracy*100:.1f}%",
            "roc_auc": f"Area under ROC curve: {roc_auc:.4f}",
            "specificity": f"Of all actually safe policies, {specificity*100:.1f}% were correctly identified"
        }
    }
    
    logger.info("\n" + "="*70)
    logger.info("TEST SET PERFORMANCE METRICS")
    logger.info("="*70)
    logger.info(f"Precision:  {precision:.4f} ({precision*100:.2f}%)")
    logger.info(f"Recall:     {recall:.4f} ({recall*100:.2f}%)")
    logger.info(f"F1 Score:   {f1:.4f}")
    logger.info(f"Accuracy:   {accuracy:.4f} ({accuracy*100:.2f}%)")
    logger.info(f"ROC-AUC:    {roc_auc:.4f}")
    logger.info(f"Specificity: {specificity:.4f} ({specificity*100:.2f}%)")
    logger.info(f"\nConfusion Matrix:")
    logger.info(f"  TP (Vulnerable correctly identified): {int(tp)}")
    logger.info(f"  TN (Safe correctly identified): {int(tn)}")
    logger.info(f"  FP (False positive vulnerabilities): {int(fp)}")
    logger.info(f"  FN (False negative vulnerabilities): {int(fn)}")
    logger.info("="*70)
    
    report_path = output_dir / "evaluation_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\nEvaluation report saved to: {report_path}")
    
    return results

if __name__ == "__main__":
    results = train_model()
    print("\n\nFinal Results:")
    print(json.dumps(results, indent=2))
