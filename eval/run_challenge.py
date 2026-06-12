"""
Krateo Autopilot eval harness — kagent-native, outcome-based.

Mirrors kagent's run-challenge.sh: for each challenge it sets up baseline, optionally
injects a fault, drives the live agent with `kagent invoke`, then grades on REAL Krateo
cluster state (krateo_checks.run_asserts) — pass/fail, not text scoring.

Run all (pytest):      pytest run_challenge.py
Run one (CLI):         python run_challenge.py challenges/portal-table-widget.yaml
Requires:              the `kagent` CLI + `kubectl` on PATH, and a cluster with the
                       autopilot deployed (KRATEO_EVAL_CONTEXT / KRATEO_EVAL_NAMESPACE).
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import yaml

from krateo_checks import run_asserts

HERE = pathlib.Path(__file__).parent
CHALLENGES_DIR = HERE / "challenges"
RESULTS_DIR = HERE / "results"
DEFAULT_AGENT = os.environ.get("KRATEO_EVAL_AGENT", "krateo-autopilot")
NAMESPACE = os.environ.get("KRATEO_EVAL_NAMESPACE", "krateo-system")
INVOKE_TIMEOUT = int(os.environ.get("KRATEO_EVAL_TIMEOUT", "180"))


def _run_cmds(cmds: list) -> None:
    for c in cmds:
        run = c["run"] if isinstance(c, dict) else c
        subprocess.run(run, shell=True, check=False)


def invoke_agent(agent: str, prompt: str) -> str:
    """Drive the live agent: echo "$prompt" | kagent invoke -v --agent <agent> -S --task -"""
    p = subprocess.run(
        ["kagent", "invoke", "-v", "--agent", agent, "--namespace", NAMESPACE, "-S", "--task", "-"],
        input=prompt, text=True, capture_output=True, timeout=INVOKE_TIMEOUT,
    )
    return (p.stdout or "") + (p.stderr or "")


def run_challenge(path: pathlib.Path) -> tuple[bool, list[dict], str]:
    doc = yaml.safe_load(path.read_text())
    name = doc.get("metadata", {}).get("name", path.stem)
    spec = doc.get("spec", {})

    _run_cmds(spec.get("setup", []))          # establish baseline
    _run_cmds(spec.get("steps", []))          # inject fault (fix-it challenges)

    log = ""
    try:
        log = invoke_agent(spec.get("agent", DEFAULT_AGENT), spec["prompt"])
    except subprocess.TimeoutExpired:
        log = "TIMED OUT"

    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / f"{name}.log").write_text(log)

    ok, results = run_asserts(spec.get("asserts", []))
    _run_cmds(spec.get("cleanup", []))        # always tidy up
    return ok, results, log


# --- pytest entrypoint -----------------------------------------------------
try:
    import pytest

    @pytest.mark.parametrize(
        "challenge",
        sorted(CHALLENGES_DIR.glob("*.yaml")),
        ids=lambda p: p.stem,
    )
    def test_challenge(challenge):
        ok, results, _ = run_challenge(challenge)
        failed = "; ".join(f"{r['kind']}: {r['detail']}" for r in results if not r["ok"])
        assert ok, f"{challenge.stem} FAILED — {failed}"
except ImportError:
    pass


# --- CLI entrypoint (mirrors run-challenge.sh) -----------------------------
if __name__ == "__main__":
    targets = [pathlib.Path(a) for a in sys.argv[1:]] or sorted(CHALLENGES_DIR.glob("*.yaml"))
    n_pass = 0
    for t in targets:
        ok, results, _ = run_challenge(t)
        print(f"\n=== {t.stem}: {'SUCCESS' if ok else 'FAILURE'} ===")
        for r in results:
            print(f"  [{'ok' if r['ok'] else 'XX'}] {r['kind']}: {r['detail']}")
        n_pass += ok
    total = len(targets)
    print(f"\nsuccess: {n_pass}/{total}  failures: {total - n_pass}")
    sys.exit(0 if n_pass == total else 1)
