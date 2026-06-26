"""Policy analysis APIs and high-level user-facing wrapper."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

import torch

from policygraph.exceptions import ModelLoadingError, PolicyParsingError
from policygraph.graph_builder import IAMGraphBuilder
from policygraph.models import GATPolicyRiskModel

logger = logging.getLogger(__name__)


class PolicyAnalyzer:
    """Analyze IAM policies using a trained GAT model."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        device: Optional[str] = None,
        threshold: float = 0.3,
    ) -> None:
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        logger.info(f"Initializing PolicyAnalyzer with device: {self.device}")
        self.threshold = threshold
        self.builder = IAMGraphBuilder()
        self.model = GATPolicyRiskModel().to(self.device)
        self.model.eval()

        if model_path:
            logger.info(f"Loading model from {model_path}")
            self.load_model(model_path)
        else:
            logger.info("Using untrained model (model_path not provided)")

    def load_model(self, model_path: str) -> None:
        try:
            logger.info(f"Loading checkpoint from {model_path}")
            checkpoint = torch.load(model_path, map_location=self.device)
            state_dict = checkpoint.get("model_state_dict", checkpoint)
            self.model.load_state_dict(state_dict)
            self.model.eval()
            logger.info(f"Successfully loaded model from {model_path}")
        except FileNotFoundError as e:
            logger.error(f"Model file not found: {model_path}")
            raise ModelLoadingError(f"Model file not found: {model_path}") from e
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}")
            raise ModelLoadingError(f"Failed to load model: {e}") from e

    def _load_policy(self, policy_input: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(policy_input, dict):
            logger.debug("Using provided policy dictionary")
            return policy_input
        path = Path(policy_input)
        if not path.exists():
            logger.error(f"Policy file not found: {path}")
            raise PolicyParsingError(f"Policy file not found: {path}")
        try:
            logger.debug(f"Loading policy from {path}")
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse policy JSON from {path}: {e}")
            raise PolicyParsingError(f"Invalid JSON in policy file {path}: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load policy from {path}: {e}")
            raise PolicyParsingError(f"Failed to load policy from {path}: {e}") from e

    def _extract_risky_patterns(self, policy: Dict[str, Any]) -> List[str]:
        risky_patterns: List[str] = []
        statements = policy.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        for statement in statements:
            if not isinstance(statement, dict):
                continue
            actions = statement.get("Action", [])
            resources = statement.get("Resource", [])
            if isinstance(actions, str):
                actions = [actions]
            if isinstance(resources, str):
                resources = [resources]

            action_set = {str(a).lower() for a in actions}
            resource_set = {str(r) for r in resources}

            if "iam:passrole" in action_set and (
                "lambda:createfunction" in action_set
                or "ec2:runinstances" in action_set
                or "cloudformation:createstack" in action_set
                or "glue:createdevendpoint" in action_set
                or "datapipeline:createpipeline" in action_set
            ):
                risky_patterns.append("PassRole + privileged service creation can enable role abuse")
            if "sts:assumerole" in action_set and "*" in resource_set:
                risky_patterns.append("Wildcard AssumeRole allows broad cross-role access")
            if any(a.startswith("iam:attach") or a.startswith("iam:put") for a in action_set):
                risky_patterns.append("Direct policy attachment/modification capability detected")
            if any(a in {"iam:createpolicyversion", "iam:setdefaultpolicyversion"} for a in action_set):
                risky_patterns.append("Policy version manipulation can overwrite effective permissions")
            if any(a in {"iam:createaccesskey", "iam:createloginprofile", "iam:updateassumerolepolicy"} for a in action_set):
                risky_patterns.append("Credential or trust-policy manipulation capability detected")
            if "*" in action_set or any(a.endswith(":*") for a in action_set):
                risky_patterns.append("Wildcard action grants excessive privileges")
            if "*" in resource_set and any(a.startswith("iam:") for a in action_set):
                risky_patterns.append("IAM action on wildcard resource broadens privilege escalation scope")

        return sorted(set(risky_patterns))

    def _heuristic_risk_score(self, policy: Dict[str, Any], risky_patterns: List[str]) -> float:
        statements = policy.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        score = 0.0
        has_deny_mfa_guardrail = False
        for statement in statements:
            if not isinstance(statement, dict):
                continue
            effect = str(statement.get("Effect", "Allow")).lower()
            actions = statement.get("Action", [])
            resources = statement.get("Resource", [])
            condition = statement.get("Condition", {})
            if isinstance(actions, str):
                actions = [actions]
            if isinstance(resources, str):
                resources = [resources]

            action_set = {str(a).lower() for a in actions}
            resource_set = {str(r) for r in resources}

            if effect == "deny" and "aws:multifactorauthpresent" in str(condition).lower():
                has_deny_mfa_guardrail = True

            if effect == "allow":
                if any(a.startswith("iam:") for a in action_set):
                    score += 0.18
                if "sts:assumerole" in action_set:
                    score += 0.15
                if any(a.endswith(":*") or a == "*" for a in action_set):
                    score += 0.2
                if "*" in resource_set:
                    score += 0.12

        score += 0.10 * len(risky_patterns)
        if has_deny_mfa_guardrail:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def analyze_policy(self, policy_input: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a single policy and return risk score and explanation."""
        logger.info(f"Starting policy analysis for: {policy_input if not isinstance(policy_input, dict) else 'dict'}")
        policy = self._load_policy(policy_input)
        graph_result = self.builder.build_graph_from_policy(policy)
        graph = graph_result.graph.to(self.device)

        with torch.no_grad():
            output = self.model(graph, return_attention=True)

        model_risk_score = float(output["risk_score"].item())
        vulnerabilities = self._extract_risky_patterns(policy)
        heuristic_risk_score = self._heuristic_risk_score(policy, vulnerabilities)

        risk_score = max(0.0, min(1.0, 0.3 * model_risk_score + 0.7 * heuristic_risk_score))
        prediction = int(risk_score >= self.threshold)

        logger.info(f"Policy analysis complete: risk_score={risk_score:.3f}, prediction={prediction}, vulnerabilities={len(vulnerabilities)}")

        return {
            "risk_score": risk_score,
            "model_risk_score": model_risk_score,
            "heuristic_risk_score": heuristic_risk_score,
            "prediction": prediction,
            "prediction_label": "vulnerable" if prediction == 1 else "secure",
            "threshold": self.threshold,
            "vulnerabilities_detected": vulnerabilities,
            "attack_paths": [
                {
                    "type": "potential_escalation",
                    "description": text,
                }
                for text in vulnerabilities
            ],
            "explanation": {
                "reason": "Model score + sensitive IAM pattern matching",
                "attention_available": "attentions" in output,
                "num_nodes": int(graph.num_nodes()),
                "num_edges": int(graph.num_edges()),
            },
        }

    def analyze_batch(self, policy_files: Iterable[Union[str, Path]]) -> List[Dict[str, Any]]:
        """Analyze multiple policy files."""
        policy_list = list(policy_files)
        logger.info(f"Starting batch analysis of {len(policy_list)} policies")
        results = []
        for idx, policy_file in enumerate(policy_list, 1):
            logger.debug(f"Analyzing policy {idx}/{len(policy_list)}: {policy_file}")
            analysis = self.analyze_policy(policy_file)
            analysis["policy_file"] = str(policy_file)
            results.append(analysis)
        logger.info(f"Batch analysis complete: {len(results)} policies processed")
        return results


class PolicyGraph:
    """High-level facade class expected by package users."""

    def __init__(self, model_path: Optional[str] = None, threshold: float = 0.5) -> None:
        self.analyzer = PolicyAnalyzer(model_path=model_path, threshold=threshold)

    def analyze(self, policies: Iterable[Union[str, Path, Dict[str, Any]]]) -> List[Dict[str, Any]]:
        outputs = []
        for policy in policies:
            outputs.append(self.analyzer.analyze_policy(policy))
        return outputs

    def analyze_policy(self, policy: Union[str, Path, Dict[str, Any]]) -> Dict[str, Any]:
        return self.analyzer.analyze_policy(policy)
