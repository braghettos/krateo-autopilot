# KAgent Slack Integration for Pod Restart Alerts

This directory contains instructions to integrate the Krateo Autopilot (and Observability Agent) with Slack, so users can @mention the bot to investigate pod restart alerts posted by the observability stack.

## Target Channel and Workspace

- **Slack channel:** `#krateo-troubleshooting`
- **Slack workspace:** `aiagents-gruppo`

Both the HyperDX pod restart alert webhook and the KAgent Slack bot must target this channel. Create the Slack incoming webhook in the `aiagents-gruppo` workspace and configure it to post to `#krateo-troubleshooting`. Invite the KAgent bot to the same channel so it receives @mentions when alerts fire.

## Overview

1. **Pod restart alerts** (from `observability-stack/pod-restart-alert`, created in HyperDX UI) post to `#krateo-troubleshooting` when pods restart.
2. **KAgent Slack bot** runs in the same channel and invokes the Krateo Autopilot via A2A.
3. When users @mention the bot or use `/mykagent`, the Autopilot routes through the **agent chain**: Observability Agent (diagnosis) → k8s-agent (remediation) → helm-agent (Helm troubleshooting).

## Prerequisites

- Krateo Autopilot and Observability Agent deployed (see `manifests/agents/`)
- KAgent controller running in the cluster
- Slack workspace with admin access to create apps

## Setup

### 1. Create a Slack App

1. Go to [Slack API – Your Apps](https://api.slack.com/apps)
2. **Create New App** → **From scratch** → name it (e.g. "Krateo Observability")
3. **OAuth & Permissions** → add Bot Token Scopes:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history` (if the bot should read channel messages)
   - `commands`
4. **Install to Workspace** → authorize
5. Copy the **Bot User OAuth Token** (`xoxb-...`) → `SLACK_BOT_TOKEN`
6. **Basic Information** → **App-Level Tokens** → Generate:
   - Name: `socket-mode`
   - Scope: `connections:write`
7. Copy the token → `SLACK_APP_TOKEN` (`xapp-...`)
8. **Socket Mode** → Enable
9. **Slash Commands** → Create:
   - Command: `/krateo` (or `/mykagent`)
   - Request URL: (not needed for Socket Mode)
   - Short description: "Ask Krateo Observability Agent"

### 2. Deploy the A2A Slack Bot

Use the [kagent a2a-slack-template](https://github.com/kagent-dev/a2a-slack-template):

```bash
git clone https://github.com/kagent-dev/a2a-slack-template.git
cd a2a-slack-template
cp .env.example .env
```

Edit `.env`:

```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
# Krateo Autopilot A2A URL (routes to Observability Agent for troubleshooting)
KAGENT_A2A_URL=http://kagent-controller.kagent.svc.cluster.local:8083/api/a2a/krateo-system/krateo-autopilot/
```

**If KAgent runs in a different namespace**, adjust the URL. To use the Observability Agent directly:

```bash
KAGENT_A2A_URL=http://kagent-controller.kagent.svc.cluster.local:8083/api/a2a/krateo-system/krateo-observability-agent/
```

Run locally (with port-forward to kagent-controller if needed):

```bash
uv venv && source .venv/bin/activate
uv sync
uv run main.py
```

Or deploy in-cluster: build a Docker image and deploy with the env vars in a Secret.

### 3. Add Bot to the Alerts Channel

1. In Slack workspace `aiagents-gruppo`, go to `#krateo-troubleshooting`
2. `/invite @Krateo Observability` (or your app name)

### 4. Wire Pod Restart Alert to the Same Channel

Ensure the HyperDX Slack webhook (created in the HyperDX UI per `observability-stack/pod-restart-alert/README.md`) posts to `#krateo-troubleshooting` in `aiagents-gruppo`. When an alert appears, users can:

- Reply in thread: `@Krateo Observability investigate this pod restart`
- Use slash command: `/krateo investigate the pod restarts in krateo-system`

**Agent chain:** The Autopilot routes to:
1. **Observability Agent** – diagnoses via ClickHouse (pod logs, K8s events, metrics)
2. **k8s-agent** ([kagent.dev/agents/k8s-agent](https://kagent.dev/agents/k8s-agent)) – remediation (ApplyManifest, PatchResource, DeleteResource, GetPodLogs, ExecuteCommand, etc.)
3. **helm-agent** ([kagent.dev/agents/helm-agent](https://kagent.dev/agents/helm-agent)) – Helm troubleshooting (ListReleases, GetRelease, Upgrade, Uninstall, RepoAdd, RepoUpdate) for chart config, upgrades, rollbacks, and release issues

Integrate k8s-agent and helm-agent as sub-agents or route to them when the user/bot requests remediation or Helm-related fixes.

## Architecture

```
Slack #krateo-troubleshooting (aiagents-gruppo)
    │
    ├── Pod Restart Alert (HyperDX) ──► posts alert message
    │
    └── User: @KrateoBot investigate
              │
              ▼
        KAgent Slack Bot (A2A client)
              │
              ▼
        KAgent Controller
              │
              ▼
        Krateo Autopilot
              │
              ├── Observability Agent (diagnosis, ClickHouse MCP)
              ├── k8s-agent (remediation: ApplyManifest, GetPodLogs, ...)
              └── helm-agent (Helm: ListReleases, Upgrade, Uninstall, ...)
```

## Troubleshooting

- **Bot doesn't respond**: Ensure Socket Mode is enabled and the bot is invited to the channel.
- **Agent timeout**: The kagent-controller must be reachable from where the bot runs. Use the in-cluster URL when the bot runs in the cluster.
- **Observability Agent can't query**: Ensure the ClickHouse MCP server is deployed and the agent has the `clickhouse-mcp-server` RemoteMCPServer configured.
