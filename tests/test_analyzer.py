from pathlib import Path

from policygraph.analyzer import PolicyAnalyzer


ROOT = Path(__file__).resolve().parents[1]


def test_analyzer_single_policy_analysis():
    analyzer = PolicyAnalyzer(model_path=None)
    sample_file = ROOT / "data/raw/samples/sts_assume_role_wildcard.json"

    result = analyzer.analyze_policy(sample_file)
    assert "risk_score" in result
    assert "prediction" in result
    assert "vulnerabilities_detected" in result
