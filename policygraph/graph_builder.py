"""IAM policy to DGL graph conversion utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import dgl
import torch


SENSITIVE_ACTION_PATTERNS = {
    "iam:*",
    "sts:*",
    "sts:assumerole",
    "iam:passrole",
    "iam:attachuserpolicy",
    "iam:attachrolepolicy",
    "iam:attachgrouppolicy",
    "iam:putuserpolicy",
    "iam:putrolepolicy",
    "iam:putgrouppolicy",
    "iam:createpolicyversion",
    "iam:setdefaultpolicyversion",
    "iam:createaccesskey",
    "iam:createloginprofile",
    "iam:updateassumerolepolicy",
    "organizations:*",
    "lambda:createfunction",
    "lambda:updatefunctioncode",
    "ec2:runinstances",
    "glue:createdevendpoint",
    "datapipeline:createpipeline",
    "cloudformation:*",
    "cloudformation:createstack",
    "sagemaker:create*",
}


@dataclass
class GraphBuildResult:
    """Structured output from graph construction."""

    graph: dgl.DGLGraph
    node_index: Dict[Tuple[str, str], int]
    node_metadata: List[Dict[str, Any]]


class IAMGraphBuilder:
    """Builds DGL graphs from IAM JSON policy documents."""

    NODE_FEATURE_NAMES = [
        "is_principal",
        "is_action",
        "is_resource",
        "is_condition",
        "is_wildcard",
        "is_sensitive",
    ]

    EDGE_FEATURE_NAMES = [
        "permission_grant",
        "resource_binding",
        "condition_check",
    ]

    def __init__(self, principal_name: str = "implicit-principal") -> None:
        self.principal_name = principal_name

    def _to_list(self, value: Any) -> List[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]

    def _flatten_condition(self, condition: Any) -> List[str]:
        if not condition:
            return []
        flattened: List[str] = []
        if isinstance(condition, dict):
            for operator, payload in condition.items():
                if isinstance(payload, dict):
                    for key, value in payload.items():
                        flattened.append(f"{operator}:{key}={value}")
                else:
                    flattened.append(f"{operator}:{payload}")
        else:
            flattened.append(str(condition))
        return flattened

    def _is_wildcard(self, token: str) -> bool:
        return "*" in token

    def _is_sensitive_action(self, action: str) -> bool:
        action_l = action.lower()
        if action_l in SENSITIVE_ACTION_PATTERNS:
            return True
        if any(action_l.startswith(p.replace("*", "")) for p in SENSITIVE_ACTION_PATTERNS if p.endswith("*")):
            return True
        if action_l.endswith(":*") and action_l.split(":", 1)[0] in {
            "iam",
            "sts",
            "organizations",
            "lambda",
            "ec2",
            "cloudformation",
            "datapipeline",
            "glue",
            "sagemaker",
        }:
            return True
        return False

    def _build_node_feature(self, node_type: str, value: str) -> torch.Tensor:
        is_sensitive = 1.0 if node_type == "action" and self._is_sensitive_action(value) else 0.0
        return torch.tensor(
            [
                1.0 if node_type == "principal" else 0.0,
                1.0 if node_type == "action" else 0.0,
                1.0 if node_type == "resource" else 0.0,
                1.0 if node_type == "condition" else 0.0,
                1.0 if self._is_wildcard(value) else 0.0,
                is_sensitive,
            ],
            dtype=torch.float32,
        )

    def build_graph_from_policy(self, policy: Dict[str, Any]) -> GraphBuildResult:
        """Convert an IAM policy dict into a DGL graph with typed features."""
        statements = policy.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]
        if not isinstance(statements, list):
            raise ValueError("Invalid IAM policy: 'Statement' must be a list or object.")

        node_index: Dict[Tuple[str, str], int] = {}
        node_metadata: List[Dict[str, Any]] = []
        node_features: List[torch.Tensor] = []
        src_nodes: List[int] = []
        dst_nodes: List[int] = []
        edge_features: List[torch.Tensor] = []

        def add_node(node_type: str, value: str) -> int:
            key = (node_type, value)
            if key in node_index:
                return node_index[key]
            node_id = len(node_index)
            node_index[key] = node_id
            node_metadata.append({"type": node_type, "value": value})
            node_features.append(self._build_node_feature(node_type, value))
            return node_id

        def add_edge(src: int, dst: int, feat: List[float]) -> None:
            src_nodes.append(src)
            dst_nodes.append(dst)
            edge_features.append(torch.tensor(feat, dtype=torch.float32))

        principal_id = add_node("principal", self.principal_name)

        for statement in statements:
            if not isinstance(statement, dict):
                continue
            effect = str(statement.get("Effect", "Allow")).lower()
            actions = [str(v) for v in self._to_list(statement.get("Action"))]
            resources = [str(v) for v in self._to_list(statement.get("Resource", "*"))]
            conditions = [str(v) for v in self._flatten_condition(statement.get("Condition"))]

            if not actions:
                actions = ["<no-action>"]
            if not resources:
                resources = ["*"]

            for action in actions:
                action_id = add_node("action", action)
                permission_grant = 1.0 if effect == "allow" else 0.0
                add_edge(principal_id, action_id, [permission_grant, 0.0, 0.0])

                for resource in resources:
                    resource_id = add_node("resource", resource)
                    add_edge(action_id, resource_id, [0.0, 1.0, 0.0])

                for cond in conditions:
                    condition_id = add_node("condition", cond)
                    add_edge(action_id, condition_id, [0.0, 0.0, 1.0])

        graph = dgl.graph((src_nodes, dst_nodes), num_nodes=len(node_index))
        graph.ndata["feat"] = torch.stack(node_features) if node_features else torch.zeros((0, 6), dtype=torch.float32)
        graph.edata["feat"] = torch.stack(edge_features) if edge_features else torch.zeros((0, 3), dtype=torch.float32)
        graph.ndata["node_type"] = torch.tensor(
            [self._node_type_to_id(meta["type"]) for meta in node_metadata], dtype=torch.int64
        )

        return GraphBuildResult(graph=graph, node_index=node_index, node_metadata=node_metadata)

    def _node_type_to_id(self, node_type: str) -> int:
        mapping = {"principal": 0, "action": 1, "resource": 2, "condition": 3}
        return mapping.get(node_type, 4)
