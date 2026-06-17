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
| Custom MCP tool servers | a `RemoteMCPServer` pointing at a server image built+published from its **own code repo** (e.g. `krateo-clickhouse-mcp-server-chart`) | the server repo's image |

- **Chart release** → `oci://ghcr.io/braghettos/krateo/<chart>` on a semver tag (`X.Y.Z`),
  `CHART_VERSION`-substituted (tag-driven). Canonical `release-oci.yaml` + `lint.yaml`.
- **MCP-server images** → built+published from each server's own code repo; the autopilot chart
  references them by `RemoteMCPServer` URL only. (Don't bundle MCP server code in the autopilot
  repo — and per §8 C7, don't build a server for what the model + existing tools already do.)

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

- **Component-scoped, not function-scoped.** One agent per COMPONENT, named `krateo-<component>-agent`,
  and it is the expert on the WHOLE component — all its CRDs, its runtime behaviour, its codebase and
  chart — not a single function. E.g. `krateo-snowplow-agent` covers both RESTActions (the CRD) and
  how snowplow serves/populates portal content at runtime; `krateo-authn-agent` covers all auth
  methods + the authn service. Don't name agents after one CRD/feature (no `krateo-restaction-agent`).
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

## 8. Conformance — the lint-enforced rules

§1–§7 describe the intent; this section is the **checkable contract**. Every agent chart (any
`kagent/chart/` or a `charts/*-agent/` chart) MUST satisfy all of the following. The canonical
`lint.yaml` runs `hack/lint-agents.py` (vendored byte-identical, like the other canonical CI) and
fails the build on any violation.

| # | Rule | Why |
|---|------|-----|
| C1 | **Chart name** matches `^krateo-[a-z0-9-]+-agent$`. | The OCI artifact, the composition Kind (`Krateo<Domain>Agent`), and the routing name all derive from it. |
| C2 | **`Agent.metadata.name` == the chart name**, verbatim — no short form. The `extraAgents` registration in the installer MUST use the same string. | The orchestrator routes by exact name; a short `authn-agent` vs chart `krateo-authn-agent` is the #1 drift. |
| C3 | **ModelConfig is referenced by a canonical name**: `gemini-flash` (default / cheap tier) or `gemini-pro` (heavy / reasoning tier). The name is provider-independent — Gemini vs GeminiVertexAI vs Ollama is a *toggle* owned by autopilot, never encoded in the name. | One fleet-wide model namespace; flipping the whole fleet to Vertex/local is one flag (see `installer-agent-modelconfig-localmodel`). Per-agent names like `vertex-gemini` fragment that. |
| C4 | **`modelConfig.create: false`** (reference autopilot's shared config) — UNLESS the agent is *standalone-capable* (installable without autopilot, e.g. `krateo-installer-agent`). A standalone agent MAY create its own config but MUST create it under a canonical C3 name (so references resolve identically whether autopilot or the agent created it). | Avoids duplicate/divergent ModelConfigs; keeps the agent-only profile working. |
| C5 | **`appVersion: CHART_VERSION`** (CI-stamped) — no literal appVersion. Chart `version` is tag-driven `CHART_VERSION`, or pinned literally only when the chart shares a repo with another primary chart (per §7). | Uniform, traceable provenance; the audit found codegen agents pinning literal `0.1.0`. |
| C6 | **`Chart.yaml` `sources`** lists the braghettos code fork AND the chart repo. | Grounds the agent in real code via github MCP (§7). |
| C7 | **Every `RemoteMCPServer` the agent references is created somewhere** — by autopilot (`chart/templates/mcp-servers.yaml`) for shared servers, or by a deployed component for domain servers. No dangling tool refs. | The audit found `krateo-blueprint-tools` / `krateo-portal-tools` referenced but created nowhere → agent `ReconcileFailed`. |

> **Don't build a domain MCP server for what the LLM + existing tools already do.** A dedicated
> `RemoteMCPServer` is justified only when it exposes a capability that the model itself, the
> shared `kagent-tool-server` (kubectl/helm), and `github-mcp-server` (code + repo-by-topic search)
> cannot. The retired `krateo-blueprint-tools` / `krateo-portal-tools` failed this test —
> schema-generation is something the model does directly, marketplace listing is a github
> topic-search, and widget specs are prompt knowledge or `kubectl explain`. Such capabilities are
> better delivered through the agent's own planning/reasoning than a server to maintain.
> `clickhouse-mcp-server` is the counter-example that *is* justified (live OTel query access).

**Canonical ModelConfig set** (owned by autopilot, `modelOwner: true`):

| Name | Tier | Default model |
|------|------|---------------|
| `gemini-flash` | default / cheap / high-volume | `gemini-2.5-flash` |
| `gemini-pro` | heavy / reasoning (codegen, schema-gen) | `gemini-2.5-pro` |

Pick `gemini-pro` only for agents doing heavy synthesis (the codegen/IaC agents); everything else
uses `gemini-flash`.

## 9. Prompt standard — the specialist agent `systemMessage`

§7–§8 govern how an agent is packaged and configured; §9 governs the **content of its prompt**.
The prompt IS the agent's behavior spec. This standard is grounded in the agentic-prompting
literature (citations at the end) and tuned for the reality of our stack: modern tool-calling +
extended-thinking models, agents that **read their own source/CRDs on demand via the github MCP**
(agentic retrieval — deliberately NOT a RAG vector store), and tools that mutate live clusters.

**The one load-bearing finding:** for these agents, accuracy comes from **grounding** (reading the
real source/cluster state), *not* from persona, not from reasoning scaffolding. A 162-persona ×
2,410-question study found expert personas give **no reliable accuracy gain** [Zheng 2024]; on
native tool-calling models, bolted-on ReAct/CoT scaffolding adds ≈0 [ToolSandbox 2024]. So the
prompt budget goes to *what to ground in and when to act*, not to "you are a brilliant expert, think
step by step".

### 9.1 Canonical structure (in this order)

A specialist `systemMessage` has six sections. Identity + the grounding contract go FIRST, and the
grounding footer restates grounding LAST — because models attend most to the start and end of a
prompt and "lose the middle" [Liu 2023].

1. **Identity & scope** — one sentence: `You are krateo-<domain>-agent, the expert on Krateo
   <component>` — expert on the WHOLE component (CRDs + runtime + codebase + chart), not one
   function. Mirror the agent's `a2aConfig.skills`. (Role sets scope/tone, not correctness.)
2. **Grounding contract** (early, high-priority) — read the relevant source/CRD via the github MCP
   (and inspect live state via `kagent-tool-server`) BEFORE asserting; trust the file you read over
   your training prior; if you cannot verify a claim from something you read, say so and read more —
   **do not guess**; reference the path you relied on.
3. **Domain knowledge** — a LEAN curated reference: the key CRDs, the canonical patterns, SHORT
   examples. Point to the chart/source for exhaustive field-level detail instead of inlining it
   (long prompts degrade accuracy 20–50% — "context rot" [Chroma 2025]; agentic on-demand reads
   match or beat preloaded/RAG context on technical, fast-changing corpora [Subramanian 2025]).
4. **Tools & when to use them** — name the agent's actual tools and the policy: read freely;
   **mutating/irreversible actions (`k8s_apply_manifest`, `helm_upgrade`, deletes) require explicit
   user confirmation first**; reversible reads are autonomous.
5. **Working rules** — clarify ambiguity before assuming; after a tool fails, diagnose from the
   observed output before retrying and don't repeat an identical failing call; report failures
   honestly.
6. **Grounding footer** — `## Your component — <domain> (codebase + chart)`: name the **braghettos
   code fork + chart repo** (the same repos as `Chart.yaml` `sources`, §7/C6) and instruct the agent
   to read them via the github tools. This restates grounding at the end of the prompt by design.

### 9.2 Rules (DO)

- **Lead with a one-line role** for scope/tone — and rely on grounding, not the title, for accuracy
  [Zheng 2024; Kong 2024; Anthropic best-practices].
- **Mandate read-before-claim + abstention + attribution.** Explicit in-prompt grounding raised
  accuracy up to 28% / mean 12% [Addlesee 2024]; an explicit "say you don't know rather than guess"
  rule is the fix for confident hallucination [Kalai 2025]; "according to the source" framing
  increases verbatim sourcing [Weller 2023]; citing the path is a measurable faithfulness signal
  [Bohnet 2022]. Anthropic ships the same instruction ("never speculate about code you have not
  opened … read the file before answering"); OpenAI's GPT-4.1 agent reminder is "do NOT guess".
- **State an explicit tool-use policy** — when, and when NOT, to call each tool — in the prompt, not
  only in the tool schema [OpenAI function-calling; Anthropic].
- **Confirm before irreversible / shared-infra mutations; keep reversible actions autonomous**
  [Anthropic best-practices]. Also enforce confirmation in the tool/HITL layer, not the prompt alone
  [OpenAI function-calling] — `hitlApproval` already does this; the prompt must agree with it.
- **Self-correct only against ground truth.** Reflect/retry when anchored to a real tool observation
  (exit status, rollout health, file contents); never "re-read your own answer and judge it" —
  intrinsic self-correction is unreliable and can degrade reasoning [Huang 2024].
- **Keep it lean; load detail on demand** via the github MCP rather than pre-stuffing references
  [Chroma 2025; Subramanian 2025]. Treat a 500+-line prompt as a smell.
- **Put the highest-priority instructions at the START and restate them at the END**; fence
  tool-retrieved source from instructions with Markdown headings / XML tags (not JSON) [Liu 2023;
  OpenAI GPT-4.1; Anthropic].
- **Positive, specific instructions with the *why*** beat negative/bare ones [Anthropic].
- **3–5 diverse examples** if examples are used [Anthropic; OpenAI].

### 9.3 Anti-patterns (DON'T)

- **No hand-rolled ReAct / "think step by step" / CoT scaffolding.** Native tool-calling + extended
  thinking already do the Thought→Action→Observation loop; generic scaffolding is redundant and can
  duplicate reasoning [Yao 2022; ToolSandbox 2024; Anthropic extended-thinking].
- **No forceful "MUST / CRITICAL / ALWAYS" spam** — it *overtriggers* current Claude models; use
  plain imperatives [Anthropic best-practices].
- **Don't lean on persona for correctness, and don't stack multiple/elaborate personas** — wrong-fit
  personas can *degrade* reasoning [Zheng 2024; Kim 2024].
- **Don't preload large reference dumps / full CRD or API dumps** into the prompt — read them on
  demand [Chroma 2025].
- **Don't describe tools in prose** — define them structurally (kagent `tools` / MCP); invest in the
  tool description text instead [OpenAI; Anthropic].
- **No multi-path search (Tree-of-Thoughts / self-consistency) in an action prompt** — it N×s cost
  and can't be majority-voted over irreversible side effects [Yao 2023].

### 9.4 Mechanics (lint-enforced — `hack/lint-agents.py`)

- **Storage:** `kagent/chart/files/prompts-<lang>.yaml` as a ConfigMap, data key `<domain>_agent`,
  rendered via `templates/prompts.yaml`. NOT a large inline `systemMessage` in `agent.yaml`.
- **P1 — non-empty:** the prompt must have content (catches empty/placeholder prompts).
- **P2 — bilingual:** both `prompts-eng.yaml` and `prompts-ita.yaml` exist and are non-empty,
  structurally identical (only the prose translated).
- **P3 — grounding footer:** the prompt contains the `## Your component` grounding section (warn).

### 9.5 Reference skeleton

```markdown
# krateo-<domain>-agent
You are krateo-<domain>-agent, the expert on Krateo <component> — its CRDs, runtime, source and chart.

## Grounding (do this first)
Before answering anything factual, read the relevant file from your source/chart via the github
tools and prefer it over memory. If you can't verify a claim from something you read, say so and
read more — don't guess. Mention the path you relied on.

## What you help with
- <skill 1, mirrors a2aConfig.skills> …

## <Domain> essentials
<lean reference: key CRDs + canonical patterns + short examples; link to source for the rest>

## Tools
- kagent-tool-server: inspect/operate the cluster (kubectl/helm). Read freely; for k8s_apply_manifest
  / helm_upgrade / deletes, confirm with the user first.
- github-mcp-server: read your own source/chart (the repos below) and search by topic.

## Working rules
Clarify ambiguity before acting. After a tool fails, diagnose from its output before retrying.
Report failures honestly.

## Your component — <domain> (codebase + chart)
You are authoritative on <component> because you read both: codebase `github.com/braghettos/<repo>`,
chart `github.com/braghettos/krateo-<domain>-chart`. Read them via the github tools for exact
fields, defaults, and behavior.
```

### 9.6 References

Reasoning/acting: ReAct [Yao 2022, arxiv 2210.03629]; Reflexion [Shinn 2023, arxiv 2303.11366];
CoT [Wei 2022, arxiv 2201.11903]; Plan-and-Solve [Wang 2023, arxiv 2305.04091]; ToT [Yao 2023,
arxiv 2305.10601]; "LLMs Cannot Self-Correct Reasoning Yet" [Huang 2024, arxiv 2310.01798];
ToolSandbox [Apple 2024, arxiv 2408.04682]. Grounding/structure/persona: "According to…" [Weller
2023, arxiv 2305.13252]; in-prompt grounding [Addlesee 2024, ACL Safety4ConvAI]; "Why LMs
Hallucinate" [Kalai 2025, arxiv 2509.04664]; Attributed QA [Bohnet 2022, arxiv 2212.08037];
agentic vs RAG retrieval [Subramanian 2025]; Lost in the Middle [Liu 2023, arxiv 2307.03172];
Context Rot [Chroma 2025]; persona-no-accuracy [Zheng 2024, arxiv 2311.10054]; role-play-for-
reasoning [Kong 2024, arxiv 2308.07702]; persona double-edged [Kim 2024, arxiv 2408.08631]. Vendor:
Anthropic prompt best-practices, Building Effective Agents, Writing tools for agents, extended
thinking; OpenAI GPT-4.1 prompting guide, function-calling guide.

## 10. Documentation standard — version-correct, agent-fetchable component docs

§9 tells an agent to ground by reading its component; §10 makes that **precise and
version-correct**. Today component repos ship only a `README.md`, so agents spelunk raw code
(slow, inconsistent) and may read `main` while an OLDER version is deployed — describing fields or
behavior that aren't in the running build. §10 fixes both: a **standardized docs artifact in every
component repo** that the agent fetches **at the exact tag matching the deployed version**.

### 10.0 Two audiences, one source of truth

Component docs serve **both** consumers as first-class — neither is an afterthought:

- **Humans** (contributors, operators, blueprint authors): narrative, tutorials, and decisions —
  `README.md`, `howto/`, `CONTRIBUTING.md`, ADRs, architecture deep-dives. Browseable and didactic;
  may be as rich as the component warrants.
- **Agents** (the component's specialist agent, grounding via the github MCP): a **lean,
  code-traced, self-contained, version-tagged** reference reached through **`llms.txt`**.

There is **one source of truth** — the same Markdown files serve both; the agent does NOT get a
forked copy of reality. **`llms.txt` is the bridge** ([llmstxt.org](https://llmstxt.org)): a curated
index that (a) lets an LLM navigate the set and (b) points the agent at the reference subset it
should ground in. Optionally ship `llms-full.txt` (the agent-relevant docs concatenated) for a
one-shot fetch. Two hard rules make the shared set safe for the agent:

- **Self-contained from code.** The agent CANNOT read project memory or your working notes — it sees
  only what's in the repo at the tag. Agent-reachable docs must be derived from and traceable to the
  code (`file:line`), never relying on memory/notes the agent can't see.
- **Version-honest per tag.** Because the agent fetches at the deployed version's tag (§10.2), the
  docs at tag `V` must describe `V`. "Re-verify at `file:line`" is therefore a *per-release*
  obligation, not a one-time write.

Human-only material (ADR narrative, tutorials, contributor guides) can be richer and is simply left
OUT of the agent path by `llms.txt` — it stays for people without bloating what the agent ingests.

### 10.1 The two doc sets (both repos)

A component spans a **chart repo** (`krateo-<domain>-chart`, the deployment unit) and a **code
repo** (`braghettos/<component>`, the implementation). Each carries its own `docs/`, versioned by
its own repo's tags, with an `llms.txt` index (per the [llmstxt.org](https://llmstxt.org)
convention — a curated markdown map the agent reads first, then fetches only the page it needs):

**Chart repo `docs/` — the deployment + API view** (`krateo-<domain>-chart/docs/`):
```
docs/
  llms.txt        # index: one-line map + links to the files below
  overview.md     # what the component is; how it deploys as a Krateo composition
  crds.md         # the CRDs it owns: purpose + key fields (curated, not the raw schema)
  wiring.md       # composition/installer wiring: values, exposure, deps, gotchas
  examples/*.yaml # canonical minimal manifests
```

**Code repo `docs/` — the internals + runtime view** (`braghettos/<component>/docs/`):
```
docs/
  llms.txt        # index
  architecture.md # how the service is built; the key packages/flows
  behavior.md     # runtime behavior, endpoints, integration contracts
  gotchas.md      # runtime pitfalls
```

Each set cross-links the other and notes that each is versioned in its own repo. Docs are
**curated and grounded in the real code/CRDs** (never invented), and **lean** (§9 ethos — the doc
is the curated grounding; the agent can still open raw source for exhaustive detail). Because docs
live in-repo, **every release tag captures the docs as-of that version automatically** — no
separate docs-versioning machinery.

### 10.2 Version-correct retrieval (the tag match)

The matching primitive already holds in our CI:

- **Chart repo tag == chart version.** `Chart.yaml` ships `version: CHART_VERSION`, substituted to
  the git tag at release (`release-oci.yaml`). So `docs/` at tag `V` *is* the docs for chart
  version `V`. The deployed chart version is cluster-observable from
  `CompositionDefinition.spec.chart.version` (and the Composition's apiVersion `v<maj>-<min>-<patch>`).
- **Code repo tag == image version == chart `appVersion`.** The chart's `appVersion` is stamped
  from the code repo's latest semver tag (`APP_VERSION`), and that is the deployed container image
  tag. The agent reads it from the component Deployment's image tag.

So an agent grounds in **version-correct** docs by reading the deployed versions off the cluster and
fetching each repo's `docs/` **at the matching tag**:

1. Resolve versions (via `kagent-tool-server`): chart version ← `CompositionDefinition.spec.chart.version`;
   image version ← the component Deployment's container image tag.
2. Fetch via github MCP at the matching ref:
   `get_file_contents("krateo-<domain>-chart", "docs/llms.txt", ref=<chart-version>)` and
   `get_file_contents("<component>", "docs/llms.txt", ref=<image-version>)`.
3. From each index, fetch the specific page needed — always at that same `ref`.

> The agent reads the DEPLOYED COMPONENT's version — NOT its own agent-chart version. The agent
> chart (`kagent/chart`, `0.1.x`) versions independently of the component it speaks for.

### 10.3 The grounding footer (supersedes §9.1's footer)

The agent's `## Your component` footer encodes the §10.2 procedure verbatim, e.g.:

```markdown
## Your component — snowplow (codebase + chart)
Ground every answer in the VERSION-CORRECT docs. First get the deployed versions with the k8s
tools: chart version = `CompositionDefinition.spec.chart.version` for snowplow; image version =
the snowplow Deployment's image tag. Then read, via the github tools at those tags:
- `braghettos/krateo-snowplow-chart` `docs/llms.txt` @ <chart-version> — deployment, CRDs, wiring.
- `braghettos/krateo-snowplow` `docs/llms.txt` @ <image-version> — internals, runtime behavior.
Open the specific page each index points to (same ref). If something isn't in the docs, read the
source at that tag — don't guess.
```

### 10.4 Enforcement (lint)

`hack/lint-agents.py` checks (warn during rollout, hard once adopted):
- **D1** — the chart repo has `docs/llms.txt` (the agent index) and that index covers the required
  **topics** (deployment/overview, CRDs, wiring/operations). D1 enforces the *index + topic
  coverage*, NOT a rigid filename set — a mature repo may keep a richer tree (e.g. snowplow's
  `architecture/` + `adr/` + `howto/`) as long as `llms.txt` maps it. The §10.1 file list is the
  recommended baseline for a repo starting from scratch, not a hard schema.
- **D2** — the agent's grounding footer references the version-pinned docs retrieval
  (`docs/llms.txt` + a `ref=`/`@ <version>` cue), not a bare "read the source".

The code repo's `llms.txt` + coverage is checked in the code repo's own CI. The `llms.txt` index is
the load-bearing artifact for both D-checks: it is what makes one human-readable doc set also
agent-navigable.

The code repo's `docs/` presence is checked in the code repo's own CI (canonical `release-tag.yaml`
/ `lint.yaml`). Adoption is per-component: a component is §10-conformant once both repos ship the
docs set and its agent footer points at the version-pinned retrieval.
