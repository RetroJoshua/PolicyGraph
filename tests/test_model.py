from pathlib import Path

from policygraph.dataset import PolicyDataset
from policygraph.models import GATPolicyRiskModel


ROOT = Path(__file__).resolve().parents[1]


def test_model_forward_pass_returns_expected_outputs():
    dataset = PolicyDataset(
        data_dir=str(ROOT / "data/raw/samples"),
        labels_file=str(ROOT / "data/raw/samples/LABELS.json"),
    )
    dataloader = dataset.get_dgl_dataloader("train", batch_size=4, shuffle=False)
    batch_graph, batch_labels, _ = next(iter(dataloader))

    model = GATPolicyRiskModel()
    output = model(batch_graph)

    assert "logits" in output
    assert "risk_score" in output
    assert output["risk_score"].shape[0] == batch_labels.shape[0]
