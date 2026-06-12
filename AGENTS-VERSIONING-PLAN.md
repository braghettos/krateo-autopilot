# Plan — Standardize Autopilot (kagent-native) + Agents Versioning

Goal: make **`braghettos/krateo-autopilot`** the single, standardized source for the
kagent-native autopilot — reconcile the deployed `0.1.7` chart into the repo, strip the
dead ADK residue, fix the `install_krateo` carry-over, and drop the duplicate from
`krateo-installer-charts`. Then define how the autopilot and the federated specialist agents
version.

Context (verified 2026-06-12): the ADK→kagent migration is already essentially complete on
`main` — no ADK agent app source remains; prompts (`chart/files/prompts-eng.yaml`, 2945 lines)
are a superset of the old ADK prompts + 5 new agents; the eval harness already replaced ADK's
`AgentEvaluator`; the custom MCP tool servers and voice-ui are kagent-native. What's left of the
ADK era is stale duplicates + the obsolete install path.

---

## Locked decisions (2026-06-12)

- **D1 — Version: adopt `0.1.7`, then `0.1.7`→`0.1.8`.** Port the deployed `0.1.7` chart into the
  repo verbatim as `0.1.7` (so the installer pin needs no change at cutover), and cut the next
  change as `0.1.8`. No `0.2.0` jump.
- **D2 — Packaging: use kagent-native mechanisms; retire the bespoke release streams.** Lean on
  what the kagent framework already provides instead of maintaining the legacy 9-workflow setup:
  - **Prompts** → kagent `promptTemplate` `dataSources` (the ConfigMap from `chart/files`), as the
    chart already does. **Retire the `release-prompts` / `release-single-prompt` ORAS streams**
    (they publish the stale root `prompts/` dir).
  - **Agents** → kagent `Agent` CRDs (chart templates). **Retire the legacy autopilot-container
    stream** (no ADK app to build).
  - **Skills** → kagent `skillRef` OCI mechanism (`agents.autopilot.skillRef`), not a bespoke
    skill build.
  - **Tools** → kagent `RemoteMCPServer` (chart-wired). The custom MCP tool servers
    (portal-tools w/ widget docs, blueprint-tools) have **no kagent built-in equivalent** (Krateo
    portal/blueprint knowledge), so they REMAIN — but wired the kagent-native way and built with
    standard krateo image CI (single `release-mcp-server` stream), not bespoke machinery.
  - **voice-ui** → prefer kagent's native UI/A2A surface; **park voice-ui** as an optional
    side-artifact (no first-class release stream) pending a look at the kagent dashboard.
  - Net: the repo keeps **the chart release (→ `/krateo`)** + **one MCP-server image stream**;
    everything else is expressed through kagent-native chart constructs.
  > Residual micro-decisions flagged for execution time: (a) confirm the custom MCP servers stay
  > as RemoteMCPServer images vs. folding their knowledge into kagent skills; (b) voice-ui keep-vs-drop
  > once the kagent dashboard is evaluated.
- **D3 — Delete `manifests/`.** The Helm `chart/` is the single source of truth (what the
  installer consumes); remove the parallel raw-manifest deploy path entirely.
- **D4 — Rewire `install_krateo` → `krateo-installer-agent`.** Replace the `install_krateo` tool
  bullet in the prompts with routing to `krateo-installer-agent` (registered via the `extraAgents`
  hook) and remove `skills/krateo-install/`. Confirmed.

---

## Phase 1 — Reconcile the chart (single-source on the repo)  [consequential]

The deployed `0.1.7` chart in `krateo-installer-charts/charts/krateo-autopilot` is authoritative
(it's what runs and was validated this session). Port it into `krateo-autopilot/chart/`.

1. Overwrite `repo/chart/` with the `0.1.7` content, bringing over what the repo's `0.1.0` lacks:
   `values.schema.json`, `templates/_helpers.tpl`, `hitlApproval`, Vertex **ADC** config
   (`projectID`/`location`, no SA-key), clickhouse MCP `STREAMABLE_HTTP` (`/mcp`), `skillRef`,
   and the **`extraAgents`** hook (+ its `values.schema.json` entry).
2. Resolve the **bidirectional drift** in `agents-iac.yaml`, `agents-krateo.yaml`,
   `model-config.yaml`: diff both sides; `0.1.7` wins by default, but inspect for any repo-side
   edit worth keeping (these are the only files that differ in both directions).
3. Set `Chart.yaml` version per **D1**.
4. Validate: `helm lint chart` + `helm template smoke chart` (schema-typed values render).

## Phase 2 — Standardize CI + registry (match the other 9 repos)

1. Add the canonical **chart** release → `oci://ghcr.io/braghettos/krateo/krateo-autopilot`
   (the per-component pattern) + the canonical **`lint.yaml`**.
2. Apply **D2** (kagent-native): **delete** the `release-autopilot-*`, `release-prompts-*`,
   `release-single-prompt-*`, `release-voice-ui-*`, `release-chart-*` (legacy) and `release-oci`
   workflows, leaving exactly two streams — the canonical **chart** release and one
   **`release-mcp-server`** image stream. Prompts/agents/skills/tools all flow through the chart
   via kagent constructs (`promptTemplate` dataSources, `Agent` CRDs, `skillRef`, `RemoteMCPServer`).
3. Set repo **description + topics** (`krateo, platformops, kubernetes, kagent, ai-agent,
   autopilot, a2a` — already done) and a standardized README.

## Phase 3 — Strip dead ADK residue  [cleanup]

1. Delete root-level **`prompts/eng` + `prompts/ita`** (stale duplicates of `chart/files/*`).
2. Delete **`descriptions/eng` + `descriptions/ita`** (superseded by inline agent descriptions;
   verify nothing references them first).
3. Apply **D3**: **delete `manifests/` entirely** (chart is the single source of truth).
4. Keep (NOT ADK, still needed): `mcp-servers/{portal-tools,blueprint-tools}` (+ widget docs),
   `eval/` (+ evalsets). **`voice-ui/`**: park per D2 (keep in-tree, no release stream) pending the
   kagent-dashboard look — or drop if superseded.

## Phase 4 — Rewire `install_krateo` → `krateo-installer-agent`  [the one correctness item]

1. In `chart/files/prompts-eng.yaml` + `prompts-ita.yaml` (and any `manifests/prompts/*` kept):
   replace the `install_krateo` tool bullet with **routing to `krateo-installer-agent`** (the
   installer ships its own agent and registers it via the autopilot `extraAgents` hook).
2. Remove **`skills/krateo-install/`** and its references.
3. Re-validate the autopilot prompt renders and the agent list is consistent.

## Phase 5 — Cut over: drop the installer-charts copy

1. Tag `krateo-autopilot` at the reconciled version (D1) → publishes
   `/krateo/krateo-autopilot` from the repo.
2. Remove **`charts/krateo-autopilot`** from `krateo-installer-charts`.
3. Align the installer pin: `chart/values.yaml` `krateo-autopilot` version → the new tag
   (currently `0.1.7`). Ordering: the repo must publish to `/krateo` **before** the installer
   references it.

## Phase 6 — Agents-versioning standard (the broader topic)

Define and document (in this repo + the installer's `AUTOPILOT-DESIGN.md`):
1. **Autopilot chart** = single version stream, tagged in this repo, `/krateo/krateo-autopilot`.
2. **Prompts** ship **inside** the chart (`chart/files`), not as a separate ORAS artifact.
3. **MCP tool servers** (portal-tools, blueprint-tools) = container images versioned on their own
   `release-mcp-server` tag, referenced by the agents as `RemoteMCPServer`.
4. **Federated specialist agents** (the vision: an agent shipped with its component `*-chart`,
   e.g. `krateo-installer-agent` in the installer repo; the 4 codegen agents in their dedicated
   repo) register on the orchestrator via the **`extraAgents`** hook. The orchestrator stays the
   single mandatory entry point. Each federated agent versions with its host chart.

---

## Sequencing & risk

- **P1 is the consequential merge** (overwrites the repo chart with `0.1.7`); do it first, on a
  branch, and diff the 3 bidirectional templates explicitly.
- **P3/P4 are low-risk cleanup** once P1 lands.
- **P5 is the cutover** — gated on the repo publishing to `/krateo`. Until then the installer
  keeps using the installer-charts copy, so do P5 last and in lockstep with the installer pin.
- All work on `sanitize/*`/`feature` branches, PR-per-repo, same as the rest of the sanitization.

## Validation gates

- `helm lint` + `helm template smoke` on the reconciled chart.
- The installer still resolves `krateo-autopilot` at `/krateo` (template check).
- `eval/` evalsets pass against the deployed agents (regression).
- Autopilot prompt no longer references `install_krateo`; `krateo-installer-agent` reachable via
  `extraAgents`.
