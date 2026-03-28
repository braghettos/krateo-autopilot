"""
Krateo Autopilot evaluation suite.

These tests evaluate the kagent-based Autopilot using `kagent invoke` instead
of the previous FastAPI / ADK AgentEvaluator approach.

Usage:
  kagent invoke --agent krateo-autopilot --namespace krateo-system \
    --message "List all blueprints"
"""

import json
import subprocess
from pathlib import Path

import pytest

AGENT_NAME = "krateo-autopilot"
NAMESPACE = "krateo-system"
DATA_DIR = Path(__file__).parent / "data"


def _invoke(message: str) -> str:
    """Run kagent invoke and return the response text."""
    result = subprocess.run(
        [
            "kagent", "invoke",
            "--agent", AGENT_NAME,
            "--namespace", NAMESPACE,
            "--message", message,
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    return result.stdout.strip()


def _load_evalset(path: Path) -> list[dict]:
    with open(path) as f:
        return json.load(f)


@pytest.mark.parametrize(
    "evalset_file",
    [
        pytest.param(f, id=f.stem)
        for f in DATA_DIR.rglob("*.evalset.json")
    ],
)
def test_eval(evalset_file: Path):
    """Run each message in an evalset and check the response is non-empty."""
    cases = _load_evalset(evalset_file)
    for case in cases:
        user_input = case.get("input") or case.get("query") or case.get("message", "")
        if not user_input:
            continue
        response = _invoke(user_input)
        assert response, f"Empty response for input: {user_input!r}"
