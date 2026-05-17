"""Training CLI wrapper."""

import argparse

from policygraph.pipeline import run_training
from policygraph.utils import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PolicyGraph GAT model")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    run_training(config)


if __name__ == "__main__":
    main()
