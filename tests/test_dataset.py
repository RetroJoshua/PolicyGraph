from pathlib import Path

from policygraph.dataset import PolicyDataset


ROOT = Path(__file__).resolve().parents[1]


def test_dataset_loads_all_policies():
    dataset = PolicyDataset(
        data_dir=str(ROOT / "data/raw/samples"),
        labels_file=str(ROOT / "data/raw/samples/LABELS.json"),
    )
    assert len(dataset) == 108


def test_dataset_has_valid_splits_and_batching():
    dataset = PolicyDataset(
        data_dir=str(ROOT / "data/raw/samples"),
        labels_file=str(ROOT / "data/raw/samples/LABELS.json"),
    )
    splits = dataset.get_split_indices()
    assert set(splits) == {"train", "val", "test"}
    assert len(splits["train"]) + len(splits["val"]) + len(splits["test"]) == len(dataset)

    # Should be close to 70/15/15
    assert 70 <= len(splits["train"]) <= 80
    assert 12 <= len(splits["val"]) <= 20
    assert 12 <= len(splits["test"]) <= 20

    batch = next(dataset.iter_batches("train", batch_size=8))
    assert len(batch) <= 8
