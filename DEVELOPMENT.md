# PolicyGraph Development Quick Start

## 1) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .
```

## 2) Verify package

```bash
python -c "import policygraph; print(policygraph.__version__)"
python -c "from policygraph import PolicyGraph; print(PolicyGraph)"
```

## 3) Train

```bash
policygraph train --config config.yaml
# or
python scripts/train.py --config config.yaml
```

Model checkpoints and CSV logs are saved in `checkpoints/`.

## 4) Evaluate

```bash
policygraph evaluate --config config.yaml --model checkpoints/best_model.pt
# or
python scripts/evaluate.py --config config.yaml --model checkpoints/best_model.pt
```

Reports are saved to `results/evaluation_report.json` (+ confusion matrix PNG).

## 5) Analyze a policy

```bash
policygraph analyze data/raw/samples/sts_assume_role_wildcard.json --model checkpoints/best_model.pt
```

## 6) Batch analysis

```bash
policygraph batch data/raw/samples --model checkpoints/best_model.pt
```

## 7) Run tests

```bash
pytest tests -v
```
