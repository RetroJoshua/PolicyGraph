"""Command-line interface for PolicyGraph."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from policygraph.analyzer import PolicyAnalyzer
from policygraph.pipeline import run_evaluation, run_training
from policygraph.utils import load_config


def cmd_analyze(args: argparse.Namespace) -> None:
    analyzer = PolicyAnalyzer(model_path=args.model)
    result = analyzer.analyze_policy(args.policy)
    print(json.dumps(result, indent=2))


def cmd_batch(args: argparse.Namespace) -> None:
    analyzer = PolicyAnalyzer(model_path=args.model)
    directory = Path(args.directory)
    files = sorted(directory.glob("*.json"))
    results = analyzer.analyze_batch(files)
    print(json.dumps(results, indent=2))


def cmd_train(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    best_path = run_training(config)
    print(json.dumps({"best_checkpoint": best_path}, indent=2))


def cmd_evaluate(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    run_evaluation(config=config, model_path=args.model)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="policygraph", description="PolicyGraph CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Analyze a single policy JSON file")
    analyze_parser.add_argument("policy", help="Path to policy JSON file")
    analyze_parser.add_argument("--model", default=None, help="Path to trained model checkpoint")
    analyze_parser.set_defaults(func=cmd_analyze)

    batch_parser = subparsers.add_parser("batch", help="Analyze all JSON policies in a directory")
    batch_parser.add_argument("directory", help="Directory containing policy JSON files")
    batch_parser.add_argument("--model", default=None, help="Path to trained model checkpoint")
    batch_parser.set_defaults(func=cmd_batch)

    train_parser = subparsers.add_parser("train", help="Train model from labeled dataset")
    train_parser.add_argument("--config", default="config.yaml", help="Path to config file")
    train_parser.set_defaults(func=cmd_train)

    evaluate_parser = subparsers.add_parser("evaluate", help="Evaluate a trained model")
    evaluate_parser.add_argument("--config", default="config.yaml", help="Path to config file")
    evaluate_parser.add_argument("--model", required=True, help="Path to trained model checkpoint")
    evaluate_parser.set_defaults(func=cmd_evaluate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
