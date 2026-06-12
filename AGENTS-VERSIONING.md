# Krateo Agents — Versioning & Federation Standard

How the Krateo Autopilot and its specialist agents are packaged, versioned, federated, and
evaluated. The companion `AGENTS-VERSIONING-PLAN.md` records the one-off migration that
established this; **this** file is the standing convention.

## 1. Principle — one mandatory entry point

`krateo-autopilot` is the **single mandatory entry point**. Every user request enters the
orchestrator, which routes to specialist sub-agents over A2A (kagent `type: Agent` tools).
No specialist is addressed directly; there are no standalone agents.

## 2. Packaging — kagent-native, two release streams

Everything an agent needs is expressed through kagent constructs in **one Helm chart**, and the
repo publishes exactly **two** OCI streams:

| Concern | kagent mechanism | Stream |
|---------|------------------|--------|
| Agents | `Agent` CRDs (chart templates) | **chart** |
| Prompts | `promptTemplate` `dataSources` → ConfigMap from `chart/files/prompts-{lang}.yaml` | **chart** (NOT a separate ORAS artifact) |
| Models | `ModelConfig` (Gemini, or GeminiVertexAI via ADC) | **chart** |
| Skills | kagent `skillRef` OCI | **chart** (referenced) |
| Tools | `RemoteMCPServer` | **chart** (referenced) |
| Custom MCP tool servers | container images on component-prefixed tags (`portal-tools/X.Y.Z`) | **release-mcp-server** image |

- **Chart release** → `oci://ghcr.io/braghettos/krateo/<chart>` on a semver tag (`X.Y.Z`),
  `CHART_VERSION`-substituted (tag-driven). Canonical `release-oci.yaml` + `lint.yaml`.
- **MCP-server image release** → built on `portal-tools/X.Y.Z`, `blueprint-tools/X.Y.Z` tags.

No other streams. The legacy autopilot-container / prompts-ORAS / single-prompt / voice-ui
workflows are retired; prompts and agents are not versioned independently of the chart.

## 3. Versioning rules

- **Autopilot chart** — single version stream, tagged in `krateo-autopilot`, one artifact
  `/krateo/krateo-autopilot`. The installer pins this version; bump the tag to release.
- **MCP tool servers** — version independently of the chart (their own image tags), since their
  code lifecycle differs from the agent definitions. The chart references them by `RemoteMCPServer`
  URL, not by image tag.
- **Federated specialist agents** (see §4) — version **with their host chart**, not with the
  autopilot. The autopilot chart only owns the orchestrator + the agents it bundles today.

## 4. Federation — `extraAgents`

The autopilot chart exposes an **`extraAgents`** hook (in `agents-autopilot.yaml`):

```yaml
extraAgents:
  - name: krateo-installer-agent   # name required; kind/apiGroup optional (Agent / kagent.dev)
```

A component or blueprint ships **its own** `Agent` and registers it on the orchestrator without
forking the autopilot chart. The orchestrator stays the single entry point; the extra agent is
reachable only through its A2A routing. The installer wires this through
`componentValues.krateo-autopilot.extraAgents`.

**Current state:** the domain specialists (auth, blueprint, documentation, portal, restaction,
observability, code-analysis, the IaC/codegen agents) are bundled in the autopilot chart.
**Target state:** each specialist federates to the repo that owns its domain and registers via
`extraAgents` — so an agent versions and ships with the component it speaks for.

### Agent → repo mapping

| Agent(s) | Home repo | How it registers |
|----------|-----------|------------------|
| `krateo-autopilot` (orchestrator) + currently-bundled specialists | `krateo-autopilot` | the chart |
| `krateo-installer-agent` | `krateo-installer` | `extraAgents` (the umbrella ships it) |
| `krateo-code-analysis`, `krateo-ansible-to-operator`, `krateo-tf-provider-to-operator`, `krateo-tf-to-helm` | a dedicated codegen-agents repo | `extraAgents` |
| per-domain specialists (auth, portal, snowplow/restaction, …) | their component `*-chart` repos (target) | `extraAgents` |

## 5. Evaluation — outcome-based (kagent benchmark pattern)

Agents are evaluated by **outcome**, not text scoring (kagent's *Kubernetes Agent Benchmark*
model, not ADK `evalset`/`AgentEvaluator`):

- **Challenges** (`eval/challenges/*.yaml`) — a task/symptom `prompt`, optional fault `steps`, and
  `asserts` on real Krateo cluster state.
- **Harness** — `setup → break → kagent invoke --agent <agent> --task - → assert`, pass/fail.
- **Self-check tool** — the same assertions exposed as the `checkKrateoFixed` MCP tool
  (`kind: ToolServer`) so the agent iterates until green.
- A federated agent ships **its own** challenges with its chart; the autopilot eval covers
  orchestration/routing. Q&A-style agents (documentation) use the separate expected-output style.

## 6. Registry & CI (per the repo-sanitization standard)

All agent charts publish to the single consolidated registry
`oci://ghcr.io/braghettos/krateo`, carry the canonical `lint.yaml` + `release-oci.yaml`, and use
the `krateo-` repo naming + topic taxonomy. See the installer's `kagent/AUTOPILOT-DESIGN.md` for
the orchestration design and the org repo-sanitization standard for naming/registry/CI.

## 7. The `/kagent` directory — shipping a federated agent

A component repo that ships its own specialist agent puts it under **`/kagent`** as a **dedicated
agent chart** (decision 2026-06-12), NOT raw manifests and NOT mixed into the component's
blueprint chart:

```
<component-repo>/kagent/
├── chart/
│   ├── Chart.yaml            # name: krateo-<domain>-agent
│   ├── values.yaml
│   ├── values.schema.json    # core-provider requires it
│   └── templates/
│       ├── agent.yaml        # kind: Agent (kagent.dev/v1alpha2)
│       ├── modelconfig.yaml  # OPTIONAL — prefer referencing the autopilot's ModelConfig by name
│       └── rbac.yaml         # OPTIONAL — only if the agent needs cluster authority (e.g. patch a CR)
├── compositiondefinition.yaml   # → oci://ghcr.io/braghettos/krateo/krateo-<domain>-agent
└── README.md
```

The agent chart is published by the **repo's** `.github/workflows/release-oci.yaml` (workflows
can't live under `kagent/`) and linted by the canonical `lint.yaml` (its `find -maxdepth 3`
already discovers `kagent/chart/`). **Versioning:** if `kagent/chart/` is the repo's *only*
primary artifact, use the tag-driven `CHART_VERSION`; if it **shares** the repo with another
primary chart (e.g. the installer umbrella), pin the agent chart version **literally** so it
versions independently of that repo's tag, and add a publish step for `kagent/chart` to the repo's
release workflow.

Rules:

- **Naming — `krateo-<domain>-agent`** (e.g. `krateo-installer-agent`, `krateo-portal-agent`). This
  is exactly the name the orchestrator routes to via `extraAgents`; the old kog `-expert` naming is
  retired for platform agents.
- **Deployment** — the agent chart publishes to `/krateo` like any other component. The installer
  adds it to `values.yaml` `components` (gated on the relevant feature) and registers it on the
  orchestrator with `componentValues.krateo-autopilot.extraAgents: [{ name: krateo-<domain>-agent }]`.
- **Model** — reference the autopilot's `ModelConfig` by name; only ship a `ModelConfig` if the
  agent needs a different tier.
- **Tools** — the domain's tools as `RemoteMCPServer` (or builtin kagent tools).
- **Eval** — the agent ships its own `eval/challenges/*.yaml` (§5) for its domain.
- **No standalone entry point** — reachable only through the orchestrator's A2A routing.
- **Knows its codebase + chart (required).** A dedicated agent must be the authoritative expert on
  its component, grounded in real code — never guessing. This is wired **structurally**, not in
  prose: the agent chart's `Chart.yaml` `sources` declares the **braghettos fork of the codebase**
  AND the chart repo that packages it (per `CHART-STANDARD.md` — fork from krateoplatformops if the
  codebase fork is missing), and the agent is given **github MCP tools** (`get_file_contents`,
  `search_code`, …) plus a prompt section naming those repos, so it reads the actual code/CRDs/schema
  on demand. Reference: `krateo-authn-agent` → `sources: [braghettos/authn, braghettos/krateo-authn-chart]`.

**Current state & migration:** only `krateo-installer/kagent/` exists today, and it is the legacy
kog-style raw-manifest "expert" pattern — its Agent is named **`krateo-installer-expert`** while the
orchestrator (and this standard) route to **`krateo-installer-agent`**. That mismatch breaks
routing and is the first thing to fix: rename to `krateo-installer-agent`, repackage as the chart
above, register via `extraAgents`. The per-domain `*-chart` repos have no `/kagent` yet — they
adopt this structure as they federate. The kog `agent-<x>-expert.yaml` reference is superseded by
this standard for installer-integrated agents.
