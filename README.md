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
  `github-mcp-server`, and the custom `krateo-portal-tools` / `krateo-blueprint-tools`).
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

`mcp-servers/portal-tools` (with the 24 portal widget specs) and `mcp-servers/blueprint-tools`
give the portal/blueprint agents Krateo-specific knowledge. They are container images, built and
published on component-prefixed tags (`portal-tools/X.Y.Z`, `blueprint-tools/X.Y.Z`) and wired in
as `RemoteMCPServer`.

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
- **MCP-server images** → push a `portal-tools/X.Y.Z` or `blueprint-tools/X.Y.Z` tag →
  `release-mcp-server-tag.yaml` builds and pushes the image.

## Links

- Installer umbrella: https://github.com/braghettos/krateo-installer
- kagent: https://kagent.dev
