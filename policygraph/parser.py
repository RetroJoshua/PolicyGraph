"""Lightweight NetworkX parser for IAM policies (legacy utility)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import networkx as nx


class IAMPolicyParser:
    """Convert IAM policy JSON documents into NetworkX directed graphs."""

    def __init__(self) -> None:
        self.graph = nx.DiGraph()

    @staticmethod
    def _to_list(value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def parse_policy(self, policy_path: str) -> nx.DiGraph:
        """Parse policy from disk and return a directed graph."""
        path = Path(policy_path)
        if not path.exists():
            raise FileNotFoundError(f"Policy file not found: {path}")

        with path.open("r", encoding="utf-8") as handle:
            policy: Dict[str, Any] = json.load(handle)

        statements = policy.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        self.graph.clear()

        for i, statement in enumerate(statements):
            effect = statement.get("Effect", "Allow")
            actions = [str(v) for v in self._to_list(statement.get("Action"))]
            resources = [str(v) for v in self._to_list(statement.get("Resource", "*"))]

            for action in actions:
                for resource in resources:
                    self.graph.add_node(action, type="action", effect=effect)
                    self.graph.add_node(resource, type="resource")
                    self.graph.add_edge(action, resource, effect=effect, statement_id=i)

        return self.graph
