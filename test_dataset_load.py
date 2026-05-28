from pathlib import Path
from policygraph.dataset import PolicyDataset

# Try loading
data_dir = Path('data/raw/samples')
labels_file = Path('data/raw/samples/LABELS.json')

print(f"Loading dataset from {data_dir}")
dataset = PolicyDataset(data_dir=data_dir, labels_file=labels_file)

print(f"Total samples: {len(dataset)}")

# Check what attributes PolicySample has
if len(dataset.samples) > 0:
    sample = dataset.samples[0]
    print(f"\nPolicySample attributes: {dir(sample)}")
    print(f"\nFirst sample:")
    print(f"  filename: {sample.filename}")
    print(f"  graph: {sample.graph}")
    print(f"  label: {sample.label}")
    
# Count labels
labels = [s.label for s in dataset.samples]
print(f"\nLabel distribution:")
print(f"  0 (secure): {labels.count(0)}")
print(f"  1 (vulnerable): {labels.count(1)}")

# Check train/val/test split
from sklearn.model_selection import train_test_split
import numpy as np

y = np.array(labels)
train_idx, temp_idx = train_test_split(range(len(y)), test_size=0.3, stratify=y, random_state=42)
val_idx, test_idx = train_test_split(temp_idx, test_size=0.5, stratify=y[temp_idx], random_state=42)

print(f"\nSplit distribution:")
print(f"  Train: {len(train_idx)} (vuln: {y[train_idx].sum()}, secure: {len(train_idx) - y[train_idx].sum()})")
print(f"  Val: {len(val_idx)} (vuln: {y[val_idx].sum()}, secure: {len(val_idx) - y[val_idx].sum()})")
print(f"  Test: {len(test_idx)} (vuln: {y[test_idx].sum()}, secure: {len(test_idx) - y[test_idx].sum()})")
