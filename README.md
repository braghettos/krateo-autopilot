# krateo-autopilot

Krateo Autopilot — the **kagent-native** AI orchestrator for [Krateo PlatformOps](https://krateo.io).
A single mandatory entry point that routes user requests to specialist sub-agents over A2A. Built
on [kagent](https://kagent.dev), the framework for Kubernetes-native AI agents.

Part of the [krateo-installer](https://github.com/braghettos/krateo-installer) ecosystem.

## What it ships

| Path | Chart | OCI artifact |
|------|-------|--------------|
| `chart/` | `krateo-autopilot` | `oci://ghcr.io/braghettos/krateo/krateo-autopilot` |

The chart renders, via kagent constructs:

- **`Agent` CRDs** — the orchestrator + specialists: `krateo-auth-agent`, `krateo-blueprint-agent`,
  `krateo-documentation-agent`, `krateo-portal-agent`, `krateo-restaction-agent`,
  `krateo-observability-agent`, `krateo-code-analysis-agent`, the IaC/codegen agents
  (`krateo-ansible-to-operator-agent`, `krateo-tf-provider-to-operator-agent`,
  `krateo-tf-to-helm-agent`), plus the built-in `k8s-agent` / `helm-agent`.
- **`ModelConfig`** — Gemini, or **GeminiVertexAI via Application Default Credentials** when
  `vertexAI.enabled=true` (no API key / SA-key; the pod uses the GKE node SA token).
- **`RemoteMCPServer`** — the tool servers (`kagent-tool-server`, `clickhouse-mcp-server`,
  `github-mcp-server`). Domain MCP servers live in their own code repos; don't add one for what the
  model + these already do (see `AGENTS-VERSIONING.md` §8 C7).
- **Prompts** — `promptTemplate` `dataSources` ConfigMap rendered from `chart/files/prompts-{eng,ita}.yaml`.
- **`hitlApproval`** — a human-in-the-loop gate on mutating Kubernetes tools.

## How the installer consumes it

The installer umbrella deploys `krateo-autopilot` (when `features.observabilityAgents=true`) as a
composition pulling `oci://ghcr.io/braghettos/krateo/krateo-autopilot`. The orchestrator is the
**single mandatory entry point**; specialists are reachable only through its A2A routing.

### Federated specialist agents (`extraAgents`)

Components and blueprints can ship their own specialist agent and register it on the orchestrator
without forking this chart, via the `extraAgents` hook:

```yaml
extraAgents:
  - name: krateo-installer-agent   # shipped by the installer repo
```

This is how Krateo installation is driven — the autopilot routes install requests to
`krateo-installer-agent` (which edits the `Installer` CR), **not** a bundled install skill.

## Custom MCP tool servers

A domain MCP server is justified only when it exposes a capability the model itself + the shared
`kagent-tool-server` (kubectl/helm) + `github-mcp-server` (code & repo-by-topic search) cannot —
e.g. `clickhouse-mcp-server` (live OTel query access), which lives in its own code repo. The former
`portal-tools` / `blueprint-tools` servers were removed: widget specs are prompt knowledge,
schema-generation is something the model does directly, and marketplace listing is a github
topic-search. See `AGENTS-VERSIONING.md` §8 C7.

## Evaluation

`eval/` runs the per-agent `*.evalset.json` scenarios against the live agents (pytest/A2A harness).

## Local validation

```sh
helm lint chart
helm template smoke chart
```

## Release

- **Chart** → push a semver tag (`X.Y.Z`) → `release-oci.yaml` publishes to
  `oci://ghcr.io/braghettos/krateo`.
- **MCP-server images** → built+published from each server's own code repo (not this repo).

## Links

- Installer umbrella: https://github.com/braghettos/krateo-installer
- kagent: https://kagent.dev
