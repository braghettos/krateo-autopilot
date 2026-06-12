"""
`check-krateo-fixed` — an MCP server exposing the eval's success assertions as a tool.

This is the dual-use half of the kagent benchmark pattern: the SAME krateo_checks used to
grade a challenge are handed to the agent as the `checkKrateoFixed` tool, so it can verify
its own work and keep fixing until the cluster satisfies the challenge.

Run as a stdio MCP server (see resources/toolserver-check-krateo-fixed.yaml):
    python check_krateo_fixed_server.py

Requires `fastmcp`, `kubectl`, and the challenges/ dir alongside this file.
"""
from __future__ import annotations

import pathlib

import yaml
from fastmcp import FastMCP

from krateo_checks import run_asserts

HERE = pathlib.Path(__file__).parent
CHALLENGES_DIR = HERE / "challenges"

mcp = FastMCP("check-krateo-fixed")


@mcp.tool()
def checkKrateoFixed(challenge: str) -> dict:
    """Check whether the Krateo cluster satisfies a challenge's success criteria.

    Args:
        challenge: the challenge name (file stem under challenges/, e.g. "portal-table-widget").

    Returns a dict {fixed: bool, results: [{kind, ok, detail}]}. If fixed is false, inspect
    the failing results, fix the cluster, and call this tool again — keep going until fixed.
    """
    path = CHALLENGES_DIR / f"{challenge}.yaml"
    if not path.exists():
        return {"fixed": False, "results": [{"kind": "load", "ok": False,
                                             "detail": f"unknown challenge {challenge!r}"}]}
    spec = yaml.safe_load(path.read_text()).get("spec", {})
    ok, results = run_asserts(spec.get("asserts", []))
    return {"fixed": ok, "results": results}


if __name__ == "__main__":
    mcp.run()  # stdio transport
