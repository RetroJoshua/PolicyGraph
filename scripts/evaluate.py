"""Evaluation CLI wrapper."""

import argparse

from policygraph.pipeline import run_evaluation
from policygraph.utils import load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate PolicyGraph model")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument("--model", required=True, help="Path to trained model checkpoint")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    run_evaluation(config=config, model_path=args.model)


if __name__ == "__main__":
    main()
