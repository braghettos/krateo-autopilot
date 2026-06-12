"""
Outcome-based Krateo cluster-state checks for the Autopilot eval.

Shared by BOTH the grader (run_challenge.py) and the `check-krateo-fixed` MCP tool
(check_krateo_fixed_server.py) — so the agent self-verifies against the *exact* same
assertions used to grade it (the kagent benchmark pattern: one assertion suite, two
consumers). Checks are outcome-based (real cluster state via kubectl), never text scoring.

Set KRATEO_EVAL_CONTEXT to target a specific kube context; otherwise the current one is used.
"""
from __future__ import annotations

import json
import os
import subprocess

CONTEXT = os.environ.get("KRATEO_EVAL_CONTEXT", "")


def _kubectl(args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    cmd = ["kubectl"]
    if CONTEXT:
        cmd += ["--context", CONTEXT]
    cmd += args
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _target(a: dict) -> list[str]:
    """resource [name] (-n ns | -A) selector from an assert spec."""
    args = [a["resource"]]
    if a.get("name"):
        args.append(a["name"])
    if a.get("namespace"):
        args += ["-n", a["namespace"]]
    elif a.get("allNamespaces"):
        args += ["-A"]
    return args


# --- check kinds -----------------------------------------------------------

def resource_exists(a: dict) -> tuple[bool, str]:
    r = _kubectl(["get", *_target(a), "-o", "name"])
    ok = r.returncode == 0 and r.stdout.strip() != ""
    return ok, (f"found {r.stdout.strip()}" if ok else f"not found: {r.stderr.strip() or a}")


def condition_true(a: dict) -> tuple[bool, str]:
    ctype = a.get("type", "Ready")
    r = _kubectl(["get", *_target(a), "-o", "json"])
    if r.returncode != 0:
        return False, f"get failed: {r.stderr.strip()}"
    obj = json.loads(r.stdout)
    conds = (obj.get("status") or {}).get("conditions") or []
    for c in conds:
        if c.get("type") == ctype:
            ok = c.get("status") == "True"
            return ok, f"condition {ctype}={c.get('status')} ({c.get('reason','')})"
    return False, f"condition {ctype} not present"


def deployment_ready(a: dict) -> tuple[bool, str]:
    spec = {"resource": "deployment", **a}
    r = _kubectl(["get", *_target(spec), "-o", "json"])
    if r.returncode != 0:
        return False, f"get failed: {r.stderr.strip()}"
    st = json.loads(r.stdout).get("status", {})
    ready, want = st.get("readyReplicas", 0), st.get("replicas", 0)
    return ready == want and want > 0, f"readyReplicas={ready}/{want}"


def field_equals(a: dict) -> tuple[bool, str]:
    r = _kubectl(["get", *_target(a), "-o", f"jsonpath={a['path']}"])
    if r.returncode != 0:
        return False, f"get failed: {r.stderr.strip()}"
    got = r.stdout.strip()
    ok = got == str(a["value"])
    return ok, f"{a['path']}={got!r} (want {a['value']!r})"


CHECKS = {
    "resourceExists": resource_exists,
    "conditionTrue": condition_true,
    "deploymentReady": deployment_ready,
    "fieldEquals": field_equals,
}


def run_asserts(asserts: list[dict]) -> tuple[bool, list[dict]]:
    """Run every assert; return (all_passed, per-assert results)."""
    results = []
    for a in asserts:
        kind = a.get("kind")
        fn = CHECKS.get(kind)
        if fn is None:
            results.append({"kind": kind, "ok": False, "detail": f"unknown check kind {kind!r}"})
            continue
        try:
            ok, detail = fn(a)
        except Exception as e:  # noqa: BLE001 — surface any kubectl/JSON error as a failed check
            ok, detail = False, f"error: {e}"
        results.append({"kind": kind, "ok": ok, "detail": detail})
    return all(r["ok"] for r in results), results
