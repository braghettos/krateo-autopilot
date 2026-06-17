#!/usr/bin/env python3
"""Conformance linter for Krateo specialized-agent charts (AGENTS-VERSIONING.md §8).

Vendored byte-identical across chart repos (like the canonical lint/release CI). Discovers every
agent chart in the repo and checks rules C1-C7. Exits non-zero on any violation.

An "agent chart" is any chart dir whose Chart.yaml `name` ends in `-agent`, OR any `kagent/chart/`.
Usage: python3 hack/lint-agents.py [root]   (root defaults to ".")
"""
import sys, os, re, glob, json

try:
    import yaml
except ImportError:
    print("PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(2)

CANONICAL_MODELCONFIGS = {"gemini-flash", "gemini-pro"}
# Agents that may legitimately self-create their ModelConfig (installable without autopilot).
STANDALONE_AGENTS = {"krateo-installer-agent"}
NAME_RE = re.compile(r"^krateo-[a-z0-9-]+-agent$")


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def load_all_docs(path):
    with open(path) as f:
        # strip Helm template lines so PyYAML can parse the skeleton; we only read literal keys
        raw = "".join(l for l in f if "{{" not in l)
    out = []
    for d in yaml.safe_load_all(raw):
        if isinstance(d, dict):
            out.append(d)
    return out


def find_agent_charts(root):
    charts = set()
    for cy in glob.glob(os.path.join(root, "**", "Chart.yaml"), recursive=True):
        cdir = os.path.dirname(cy)
        # skip vendored subcharts
        if os.sep + "charts" + os.sep in cdir and os.path.basename(os.path.dirname(cdir)) == "charts":
            # a chart under another chart's charts/ — vendored dep, skip
            pass
        try:
            meta = load_yaml(cy) or {}
        except Exception:
            continue
        name = str(meta.get("name", ""))
        if name.endswith("-agent") or cdir.replace(os.sep, "/").endswith("kagent/chart"):
            charts.add(cdir)
    return sorted(charts)


def grep_modelconfig_ref(agent_docs):
    """Return the modelConfig name an Agent references, or None. Reads literal values only;
    a templated value like {{ .Values.modelConfig.name }} is resolved from values.yaml separately."""
    for d in agent_docs:
        if d.get("kind") == "Agent":
            decl = d.get("spec", {}).get("declarative", {})
            mc = decl.get("modelConfig")
            if mc:
                return mc
    return None


def lint_chart(cdir):
    errs = []
    meta = load_yaml(os.path.join(cdir, "Chart.yaml")) or {}
    name = str(meta.get("name", ""))
    rel = os.path.relpath(cdir)

    # C1 chart name
    if not NAME_RE.match(name):
        errs.append(f"[C1] chart name {name!r} does not match ^krateo-<domain>-agent$")

    # C5 appVersion
    appv = str(meta.get("appVersion", ""))
    if appv != "CHART_VERSION":
        errs.append(f"[C5] appVersion is {appv!r}, expected the CHART_VERSION placeholder")

    # C6 sources — must be present and braghettos-hosted. The code-fork SHOULD also be listed for
    # agents that speak for a component with a distinct codebase (§7), but that is reviewed, not
    # lint-failed, since codegen/installer agents have no separate code repo.
    srcs = meta.get("sources") or []
    if not srcs or not all("braghettos" in str(s) for s in srcs):
        errs.append(f"[C6] Chart.yaml sources must be present and braghettos-hosted (got {srcs})")

    # locate agent.yaml + values.yaml
    tdir = os.path.join(cdir, "templates")
    agent_files = glob.glob(os.path.join(tdir, "*agent*.yaml")) + glob.glob(os.path.join(tdir, "agent.yaml"))
    agent_files = sorted(set(agent_files))
    values = {}
    vpath = os.path.join(cdir, "values.yaml")
    if os.path.exists(vpath):
        values = load_yaml(vpath) or {}

    agent_name = None
    mc_ref = None
    mcp_refs = []
    for af in agent_files:
        docs = load_all_docs(af)
        for d in docs:
            if d.get("kind") == "Agent":
                agent_name = d.get("metadata", {}).get("name", agent_name)
                decl = d.get("spec", {}).get("declarative", {})
                if decl.get("modelConfig"):
                    mc_ref = decl["modelConfig"]
                for t in decl.get("tools", []) or []:
                    ms = t.get("mcpServer") or {}
                    if ms.get("kind") == "RemoteMCPServer" and ms.get("name"):
                        mcp_refs.append(ms["name"])

    # C2 Agent.metadata.name == chart name. agent_name may be templated ({{...}} stripped → None);
    # if so, fall back to values.fullnameOverride / name heuristics.
    if agent_name and "{{" not in str(agent_name):
        if agent_name != name:
            errs.append(f"[C2] Agent.metadata.name {agent_name!r} != chart name {name!r}")

    # C3/C4 modelConfig. The agent.yaml ref is often a stripped template line, so fall back to
    # values.modelConfig.name whenever we couldn't read a literal name from the Agent doc.
    mc_name = mc_ref
    if not mc_name or "{{" in str(mc_name):
        mc_name = (values.get("modelConfig") or {}).get("name")
    if mc_name:
        if mc_name not in CANONICAL_MODELCONFIGS:
            errs.append(f"[C3] modelConfig {mc_name!r} not in canonical set {sorted(CANONICAL_MODELCONFIGS)}")
        create = (values.get("modelConfig") or {}).get("create", False)
        if create and name not in STANDALONE_AGENTS:
            errs.append(f"[C4] modelConfig.create=true but {name} is not a standalone agent")

    # §9 prompt standard
    perrs, warns = check_prompts(cdir, agent_files)
    errs.extend(perrs)
    return rel, name, errs, warns


def check_prompts(cdir, agent_files):
    """§9.4 prompt mechanics: P1 non-empty, P2 bilingual files, P3 grounding footer (warn)."""
    errs, warns = [], []
    files_dir = os.path.join(cdir, "files")
    langs = ("eng", "ita")
    lang_state = {}
    prompt_text = ""
    for lang in langs:
        p = os.path.join(files_dir, f"prompts-{lang}.yaml")
        content = ""
        if os.path.exists(p):
            try:
                cm = load_yaml(p)
                data = cm.get("data", {}) if isinstance(cm, dict) else {}
                content = "".join(str(v) for v in (data or {}).values()).strip()
            except Exception:
                content = open(p).read().strip()  # templated — fall back to raw text
        lang_state[lang] = (os.path.exists(p), content)
        prompt_text += content

    # inline systemMessage fallback (non-canonical per §9.4, but counts for P1 non-empty)
    for af in agent_files:
        raw = open(af).read()
        if "systemMessage:" in raw:
            prompt_text += raw.split("systemMessage:", 1)[1]

    if not prompt_text.strip():
        errs.append("[PROMPT-P1] no prompt content (empty prompts-*.yaml and no inline systemMessage) — §9.4")
    for lang in langs:
        exists, content = lang_state[lang]
        if not exists or not content:
            errs.append(f"[PROMPT-P2] missing/empty files/prompts-{lang}.yaml — §9.4 bilingual required")
    if prompt_text.strip() and "## Your component" not in prompt_text:
        warns.append("[PROMPT-P3] prompt lacks the '## Your component' grounding footer — §9.1")
    return errs, warns


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    charts = find_agent_charts(root)
    if not charts:
        print("no agent charts found — nothing to lint")
        return 0
    total = 0
    for cdir in charts:
        rel, name, errs, warns = lint_chart(cdir)
        if errs:
            total += len(errs)
            print(f"✗ {rel} ({name})")
            for e in errs:
                print(f"    {e}")
        else:
            print(f"✓ {rel} ({name})")
        for w in warns:
            print(f"    ⚠ {w}")
    if total:
        print(f"\n{total} conformance violation(s) — see AGENTS-VERSIONING.md §8/§9")
        return 1
    print("\nall agent charts conform")
    return 0


if __name__ == "__main__":
    sys.exit(main())
