# Krateo Autopilot (kagent)

Krateo Autopilot is an AI assistant for [Krateo PlatformOps](https://krateo.io),
re-engineered to run natively on [kagent](https://kagent.dev) — the open-source
framework for Kubernetes-native AI agents.

## Architecture

```
kagent Controller
└── Agent: krateo-autopilot (orchestrator)
    ├── Skill: krateo-install-skill     (Helm-based Krateo installer)
    ├── Agent: krateo-auth-agent        (authentication management)
    ├── Agent: krateo-blueprint-agent   (blueprint/composition creation)
    │   └── MCP: krateo-blueprint-tools (list/get/marketplace/schema tools)
    ├── Agent: krateo-documentation-agent (Krateo knowledge base)
    ├── Agent: krateo-portal-agent      (portal widget YAML generation)
    │   └── MCP: krateo-portal-tools    (widget specification files)
    └── Agent: krateo-restaction-agent  (RESTAction CRD generation)
```

## Prerequisites

- Kubernetes cluster with kagent installed ([kagent.dev/docs/getting-started](https://kagent.dev/docs/getting-started))
- `kubectl` configured to access the cluster
- Helm 3
- A Google Cloud project with Vertex AI enabled

## Installation

### 1. Create the Krateo namespace and GCP credentials Secret

```bash
kubectl create namespace krateo-system

kubectl create secret generic gcloud-credentials \
  --from-file=key.json=/path/to/your/service-account-key.json \
  -n krateo-system
```

### 2. Deploy the MCP servers

```bash
helm upgrade --install krateo-blueprint-tools \
  ./mcp-servers/blueprint-tools/chart \
  --namespace krateo-system

helm upgrade --install krateo-portal-tools \
  ./mcp-servers/portal-tools/chart \
  --namespace krateo-system
```

### 3. Apply the prompt ConfigMaps

```bash
# English prompts (default)
kubectl apply -f manifests/prompts/eng-configmap.yaml

# Italian prompts (optional)
kubectl apply -f manifests/prompts/ita-configmap.yaml
```

### 4. Apply ModelConfig and ModelProviderConfig

```bash
kubectl apply -f manifests/model-provider-config.yaml
kubectl apply -f manifests/model-config.yaml
```

### 5. Register MCP servers with kagent

```bash
kubectl apply -f manifests/mcp-servers/krateo-blueprint-tools.yaml
kubectl apply -f manifests/mcp-servers/krateo-portal-tools.yaml
```

### 6. Deploy the agents

```bash
# Sub-agents first
kubectl apply -f manifests/agents/auth-agent.yaml
kubectl apply -f manifests/agents/blueprint-agent.yaml
kubectl apply -f manifests/agents/documentation-agent.yaml
kubectl apply -f manifests/agents/portal-agent.yaml
kubectl apply -f manifests/agents/restaction-agent.yaml

# Root agent last (depends on sub-agents)
kubectl apply -f manifests/agents/autopilot.yaml
```

### 7. Verify

```bash
kubectl get agents -n krateo-system
kubectl get remotemcpservers -n krateo-system
```

## Usage

```bash
# Interact via the kagent CLI
kagent invoke --agent krateo-autopilot --namespace krateo-system \
  --message "List all blueprints installed in the cluster"

# Or use the kagent UI
kagent ui
```

## Language Switching

To switch from English to Italian prompts, patch each agent's `promptTemplate`
to reference `krateo-prompts-ita` instead of `krateo-prompts-eng`:

```bash
# Example for root agent
kubectl patch agent krateo-autopilot -n krateo-system --type=merge \
  -p '{"spec":{"declarative":{"promptTemplate":{"dataSources":[{"kind":"ConfigMap","name":"krateo-prompts-ita","namespace":"krateo-system","alias":"prompts"}]}}}}'
```

## Project Structure

```
autopilot/
├── manifests/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── model-config.yaml
│   ├── model-provider-config.yaml
│   ├── agents/                   # kagent Agent CRDs
│   │   ├── autopilot.yaml
│   │   ├── auth-agent.yaml
│   │   ├── blueprint-agent.yaml
│   │   ├── documentation-agent.yaml
│   │   ├── portal-agent.yaml
│   │   └── restaction-agent.yaml
│   ├── mcp-servers/              # RemoteMCPServer CRDs
│   │   ├── krateo-blueprint-tools.yaml
│   │   └── krateo-portal-tools.yaml
│   └── prompts/                  # Agent system prompts as ConfigMaps
│       ├── eng-configmap.yaml
│       └── ita-configmap.yaml
├── mcp-servers/                  # Custom MCP server implementations
│   ├── blueprint-tools/          # Blueprint/composition/schema tools
│   │   ├── server.py
│   │   ├── schema.py             # Python port of krateoctl gen-schema logic
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── chart/
│   └── portal-tools/             # Portal widget specification tools
│       ├── server.py
│       ├── requirements.txt
│       ├── Dockerfile
│       ├── widgets/              # Widget spec markdown files
│       └── chart/
├── skills/                       # Container-based skills
│   └── krateo-install/           # Krateo installation skill
│       ├── SKILL.md
│       ├── Dockerfile
│       └── scripts/
├── prompts/                      # Source prompt markdown files
│   ├── eng/
│   └── ita/
├── descriptions/                 # Agent description files
│   ├── eng/
│   └── ita/
└── eval/                         # Evaluation tests (kagent invoke based)
```

## Building Container Images

```bash
# Blueprint tools MCP server
docker build -t ghcr.io/krateoplatformops/krateo-blueprint-tools:latest \
  mcp-servers/blueprint-tools/

# Portal tools MCP server
docker build -t ghcr.io/krateoplatformops/krateo-portal-tools:latest \
  mcp-servers/portal-tools/

# Krateo install skill
docker build -t ghcr.io/krateoplatformops/krateo-install-skill:latest \
  skills/krateo-install/
```

## Notes on gen_values_schema_json

The `gen_values_schema_json` tool in `krateo-blueprint-tools` is a pure Python
port of [`krateoctl gen-schema`](https://github.com/krateoplatformops/krateoctl).
It parses the same `# @schema` annotation format used in Krateo blueprint charts,
so all existing charts remain compatible without any changes.
