# Autopilot eval — kagent-native, outcome-based

This suite evaluates the **deployed** Krateo Autopilot the way kagent evaluates its own agents:
**outcome-based challenges**, not text scoring. Each challenge gives the agent a task (optionally
after injecting a fault), drives it with `kagent invoke`, then grades on **real Krateo cluster
state** — was the resource created? did the Composition reconcile? did the workload recover?

It follows kagent's *Kubernetes Agent Benchmark* pattern (`.github/data/agent-framework/` in
`kagent-dev/kagent`): `Challenge` fixtures with a symptom/task `prompt` and optional fault `steps`,
a `run-challenge` loop, cluster-state assertions, and a self-check tool the agent calls to iterate
until green. The previous ADK `*.evalset.json` + `test_config.json` (`tool_trajectory_avg_score`,
`response_match_score`) are gone — kagent grades outcomes, not turns. The old ADK Q&A evalsets are
preserved under `legacy-evalsets/` for reference.

## Layout

| Path | Purpose |
|------|---------|
| `challenges/*.yaml` | `kind: Challenge` fixtures — `{prompt, setup, steps (fault), asserts, cleanup}` |
| `krateo_checks.py` | the assertion library (kubectl-based check kinds) — shared by grader **and** tool |
| `run_challenge.py` | the harness: baseline → break → `kagent invoke` → grade (pytest + CLI) |
| `check_krateo_fixed_server.py` | `fastmcp` MCP server exposing `checkKrateoFixed` (same assertions) |
| `resources/toolserver-check-krateo-fixed.yaml` | `kind: ToolServer` registering the tool with kagent |
| `legacy-evalsets/` | the old ADK Q&A evalsets, kept for reference (not run) |

## Prerequisites

- `kagent` CLI + `kubectl` on PATH, and a cluster with the autopilot deployed.
- `pip install -r requirements.txt` (pyyaml, pytest; fastmcp only for the tool server).
- Env (see `.env.example`): `KRATEO_EVAL_CONTEXT`, `KRATEO_EVAL_NAMESPACE`, `KRATEO_EVAL_AGENT`.

## Run

```sh
pytest run_challenge.py                                     # all challenges
python run_challenge.py challenges/snowplow-recover.yaml    # one challenge, verbose
```

The harness, per challenge: runs `setup` → `steps` (fault injection) → pipes `prompt` to
`kagent invoke --agent <agent> --task -` (log saved under `results/`) → runs `asserts` → `cleanup`.
Pass/fail is purely the assertions on cluster state.

## Check kinds (`krateo_checks.py`)

| kind | asserts |
|------|---------|
| `resourceExists` | `kubectl get <resource> <name> -n <ns>` returns an object |
| `conditionTrue` | `status.conditions[type=<type>].status == "True"` (default `Ready`) — for Compositions |
| `deploymentReady` | `readyReplicas == replicas` (> 0) |
| `fieldEquals` | a jsonpath `path` equals `value` |

## The self-check tool

`check_krateo_fixed_server.py` exposes the **same** assertions as the `checkKrateoFixed` MCP tool.
Registered via `resources/toolserver-check-krateo-fixed.yaml`, the agent calls it after acting and
keeps fixing until `fixed=true` — exactly how kagent hands agents `checkKubernetesClusterFixed`.
To use it in-cluster, bundle this `eval/` dir + `kubectl` + `fastmcp` into the tool image (kagent's
upstream equivalent is the published `check-kubernetes-cluster-fixed` npm package run via `npx`).

## Scope

Outcome challenges cover the **operational/creation** agents (portal, restaction, auth, blueprint,
installer, k8s/observability). The **documentation agent** is Q&A — that's the *other* kagent eval
style (expected-output / LLM-judge, like kagent's `.claude/skills/*/evals/evals.json`) and is a
separate, future addition rather than an outcome challenge.

## Adding a challenge

Drop a `challenges/<name>.yaml` with a `prompt`, optional `setup`/`steps`, and `asserts` using the
check kinds above. Point its prompt at `checkKrateoFixed` with `challenge: "<name>"` so the agent
can self-verify. That's it — `pytest` discovers it automatically.
