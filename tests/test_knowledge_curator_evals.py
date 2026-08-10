import json
from pathlib import Path


def test_eval_contract_has_positive_and_negative_cases():
    path = Path(__file__).resolve().parents[1] / "catalog/skills/knowledge-curator/evals/evals.json"
    data = json.loads(path.read_text())
    assert data["skill_name"] == "knowledge-curator"
    assert {case["name"] for case in data["evals"]} == {"init-workflow", "unsafe-push", "unrelated-request"}
    assert all(case["prompt"] and case["expected_output"] for case in data["evals"])
