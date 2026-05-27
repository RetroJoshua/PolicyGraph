"""Dataset loading and splitting utilities for PolicyGraph."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset

from policygraph.graph_builder import IAMGraphBuilder


@dataclass
class PolicySample:
    """Single policy sample and its metadata."""

    filename: str
    policy: Dict[str, Any]
    label_text: str
    label: int
    severity: str
    vulnerability_type: str
    risk_score: float
    graph: Any


class PolicyDataset(Dataset):
    """Load IAM policies, labels, graph encodings, and train/val/test splits."""

    def __init__(
        self,
        data_dir: str = "data/raw/samples",
        labels_file: Optional[str] = None,
        split_seed: int = 42,
        builder: Optional[IAMGraphBuilder] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.labels_file = Path(labels_file) if labels_file else self.data_dir / "LABELS.json"
        self.split_seed = split_seed
        self.builder = builder or IAMGraphBuilder()

        if not self.data_dir.exists():
            raise FileNotFoundError(f"Data directory not found: {self.data_dir}")
        if not self.labels_file.exists():
            raise FileNotFoundError(f"Labels file not found: {self.labels_file}")

        self._labels_payload = self._load_labels_payload()
        self.samples: List[PolicySample] = self._load_samples()
        self._splits = self._build_stratified_splits()

    def _load_labels_payload(self) -> Dict[str, Any]:
        with self.labels_file.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        # Support both formats:
        # Format A (canonical): {"total_policies": N, "labels": [{...}, ...]}
        # Format B (flat dict):  {"policy_001.json": {"label": "vulnerable"}, ...}
        if "labels" in payload and isinstance(payload["labels"], list):
            return payload  # Format A — already correct

        # Convert Format B → Format A
        entries = []
        for filename, meta in payload.items():
            if not isinstance(meta, dict):
                continue
            entry = {"filename": filename}
            entry.update(meta)
            entries.append(entry)

        return {"total_policies": len(entries), "labels": entries}

    def _resolve_label(self, entry: Dict[str, Any]) -> tuple[str, int]:
        """
        Resolve label from an entry dict, handling all known formats:
          - {"label": "vulnerable"} or {"label": "safe"}
          - {"vulnerable": true} or {"vulnerable": false}
          - {"label": "secure"}  (legacy typo — treated as safe)
        Returns (label_text, label_int) where label_text is "vulnerable" or "safe".
        """
        if "label" in entry:
            raw = str(entry["label"]).strip().lower()
            if raw == "vulnerable":
                return "vulnerable", 1
            return "safe", 0  # covers "safe", "secure", anything else

        if "vulnerable" in entry:
            is_vuln = entry["vulnerable"]
            # Handle bool, int, or string representations
            if isinstance(is_vuln, bool):
                return ("vulnerable", 1) if is_vuln else ("safe", 0)
            if str(is_vuln).strip().lower() in {"true", "1", "yes", "vulnerable"}:
                return "vulnerable", 1
            return "safe", 0

        return "safe", 0  # default

    def _load_samples(self) -> List[PolicySample]:
        samples: List[PolicySample] = []
        for entry in self._labels_payload["labels"]:
            filename = entry.get("filename")
            if not filename:
                raise ValueError("Encountered label entry without 'filename'")

            policy_path = self.data_dir / filename
            if not policy_path.exists():
                raise FileNotFoundError(
                    f"Policy file referenced in labels not found: {policy_path}"
                )

            with policy_path.open("r", encoding="utf-8") as handle:
                policy_obj = json.load(handle)

            label_text, label = self._resolve_label(entry)

            graph_result = self.builder.build_graph_from_policy(policy_obj)
            graph = graph_result.graph
            graph.ndata["filename_hash"] = torch.full(
                (graph.num_nodes(),), hash(filename) % (10**9), dtype=torch.int64
            )

            samples.append(
                PolicySample(
                    filename=filename,
                    policy=policy_obj,
                    label_text=label_text,
                    label=label,
                    severity=str(entry.get("severity", "unknown")),
                    vulnerability_type=str(entry.get("vulnerability_type", "unknown")),
                    risk_score=float(entry.get("risk_score", 0.0)),
                    graph=graph,
                )
            )

        expected = int(self._labels_payload.get("total_policies", len(samples)))
        if len(samples) != expected:
            raise ValueError(
                f"Mismatch between loaded sample count and total_policies: "
                f"{len(samples)} vs {expected}"
            )
        return samples

    def _build_stratified_splits(self) -> Dict[str, List[int]]:
        labels = [sample.label for sample in self.samples]
        indices = list(range(len(self.samples)))
        train_idx, temp_idx = train_test_split(
            indices,
            test_size=0.30,
            random_state=self.split_seed,
            stratify=labels,
        )
        temp_labels = [labels[i] for i in temp_idx]
        val_idx, test_idx = train_test_split(
            temp_idx,
            test_size=0.50,
            random_state=self.split_seed,
            stratify=temp_labels,
        )
        return {
            "train": sorted(train_idx),
            "val": sorted(val_idx),
            "test": sorted(test_idx),
        }

    def get_split_indices(self) -> Dict[str, List[int]]:
        """Return train/validation/test indices."""
        return {k: v.copy() for k, v in self._splits.items()}

    def get_split(self, split: str) -> List[PolicySample]:
        if split not in self._splits:
            raise ValueError(
                f"Unsupported split '{split}'. Expected one of {list(self._splits)}"
            )
        return [self.samples[idx] for idx in self._splits[split]]

    def iter_batches(
        self, split: str, batch_size: int = 32
    ) -> Iterator[List[PolicySample]]:
        """Yield batched samples from a split for non-DGL workflows."""
        split_samples = self.get_split(split)
        for i in range(0, len(split_samples), batch_size):
            yield split_samples[i : i + batch_size]

    def get_dgl_dataloader(
        self, split: str, batch_size: int = 32, shuffle: bool = False
    ):
        """Return a DGL GraphDataLoader for a split."""
        from dgl.dataloading import GraphDataLoader

        split_indices = self._splits.get(split)
        if split_indices is None:
            raise ValueError(f"Unknown split '{split}'")

        subset = [self[i] for i in split_indices]

        def collate_fn(batch: Sequence[Tuple[Any, torch.Tensor, Dict[str, Any]]]):
            import dgl

            graphs, labels, metadata = zip(*batch)
            batched_graph = dgl.batch(list(graphs))
            label_tensor = torch.stack(list(labels)).view(-1)
            return batched_graph, label_tensor, list(metadata)

        return GraphDataLoader(
            subset, batch_size=batch_size, shuffle=shuffle, collate_fn=collate_fn
        )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(
        self, index: int
    ) -> Tuple[Any, torch.Tensor, Dict[str, Any]]:
        sample = self.samples[index]
        metadata = {
            "filename": sample.filename,
            "severity": sample.severity,
            "vulnerability_type": sample.vulnerability_type,
            "label_text": sample.label_text,
            "risk_score": sample.risk_score,
        }
        label = torch.tensor(sample.label, dtype=torch.float32)
        return sample.graph, label, metadata
