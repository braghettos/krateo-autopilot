"""
krateo-blueprint-tools MCP Server

Exposes 6 tools via Streamable HTTP (FastMCP):
  - list_blueprints
  - get_blueprint
  - get_blueprint_form
  - get_marketplace_blueprint
  - list_marketplace_blueprints
  - gen_values_schema_json
"""

import json
import logging
import os
import subprocess
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import requests
import yaml
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import Settings as FastMCPSettings

from schema import generate_schema_json

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_port = int(os.getenv("PORT", "8080"))
mcp = FastMCP(
    "krateo-blueprint-tools",
    host="0.0.0.0",
    port=_port,
    streamable_http_path="/mcp",
    # Allow all hosts – this server runs inside Kubernetes and is accessed
    # via cluster-internal DNS names, not localhost.
    transport_security=None,
)


# --------------------------------------------------------------------------- #
# Internal helpers                                                             #
# --------------------------------------------------------------------------- #

def _is_relevant_file(member: str) -> bool:
    if member.endswith("_helpers.tpl"):
        return False
    return (
        "templates/" in member
        or member.endswith("/Chart.yaml")
        or member.endswith("/values.yaml")
    )


def _extract_chart_files(chart_path: Path) -> list[str]:
    files_content: list[str] = []
    with tarfile.open(chart_path, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile() and _is_relevant_file(member.name):
                f = tar.extractfile(member)
                if f:
                    content = f.read().decode("utf-8")
                    files_content.append(f"# File: {member.name}\n{content}")
    return files_content


def _get_blueprint_files(chart: dict) -> list[str]:
    """Download a Helm or OCI chart and return relevant file contents."""
    url = chart.get("url")
    if not url:
        raise ValueError("Chart must contain a 'url' field")

    version = chart.get("version")
    repo = chart.get("repo")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        try:
            is_oci = url.startswith("oci://")
            if is_oci:
                chart_url = f"{url}/{repo}" if repo else url
                if version:
                    chart_url = f"{chart_url}:{version}"
                subprocess.run(
                    ["helm", "pull", chart_url, "--destination", str(tmpdir_path)],
                    check=True, capture_output=True,
                )
            else:
                if not repo:
                    raise ValueError("Helm chart (non-OCI) must contain a 'repo' field")
                if not version:
                    raise ValueError("Helm chart must contain a 'version' field")
                repo_alias = "temp-repo"
                subprocess.run(
                    ["helm", "repo", "add", repo_alias, url],
                    check=True, capture_output=True,
                )
                subprocess.run(
                    ["helm", "repo", "update", repo_alias],
                    check=True, capture_output=True,
                )
                chart_ref = f"{repo_alias}/{repo}"
                subprocess.run(
                    ["helm", "pull", chart_ref, "--version", version, "--destination", str(tmpdir_path)],
                    check=True, capture_output=True,
                )

            tgz_files = list(tmpdir_path.glob("*.tgz"))
            if not tgz_files:
                raise RuntimeError("No .tgz file found after helm pull")

            return _extract_chart_files(tgz_files[0])

        except subprocess.CalledProcessError as e:
            err = e.stderr.decode() if e.stderr else str(e)
            raise RuntimeError(f"Failed to pull chart: {err}") from e


def _get_chart_description(chart: dict) -> str:
    url = chart.get("url", "")
    version = chart.get("version")
    repo = chart.get("repo")
    is_oci = url.startswith("oci://")

    if not is_oci:
        index_url = f"{url.rstrip('/')}/index.yaml"
        resp = requests.get(index_url, timeout=10)
        resp.raise_for_status()
        index_data = yaml.safe_load(resp.text)
        entries = index_data.get("entries", {}).get(repo, [])
        entry = next((e for e in entries if e.get("version") == version), None)
        return entry.get("description", "No description available") if entry else "Not found"

    chart_url = f"{url}/{repo}" if repo else url
    if version:
        chart_url = f"{chart_url}:{version}"
    try:
        result = subprocess.run(
            ["helm", "show", "chart", chart_url],
            capture_output=True, text=True, check=True,
        )
        for line in result.stdout.splitlines():
            if line.strip().startswith("description:"):
                return line.split("description:", 1)[1].strip()
        return ""
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"helm show chart failed: {e.stderr.strip()}") from e


def _get_frontend_address() -> str:
    try:
        result = subprocess.run(
            ["kubectl", "get", "svc", "frontend", "-n", "krateo-system", "-o", "json"],
            capture_output=True, text=True, check=True,
        )
        svc = json.loads(result.stdout)
        svc_type = svc["spec"]["type"]
        ports = svc["spec"].get("ports", [])
        port = ports[0].get("port") if ports else None
        if not port:
            raise ValueError("No ports found in frontend service")

        ip = None
        if svc_type == "LoadBalancer":
            ingress = svc["status"].get("loadBalancer", {}).get("ingress", [])
            if ingress:
                ip = ingress[0].get("ip") or ingress[0].get("hostname")
        elif svc_type == "NodePort":
            ip = svc["spec"].get("externalIPs", [None])[0] or svc["spec"].get("clusterIP")
            port = ports[0].get("nodePort", port)
        elif svc_type == "ClusterIP":
            ip = svc["spec"].get("clusterIP")

        if not ip:
            raise ValueError(f"Could not determine IP for service type {svc_type}")
        return f"{ip}:{port}"
    except Exception as e:
        return f"Failed to get frontend address: {e}"


# --------------------------------------------------------------------------- #
# MCP Tools                                                                    #
# --------------------------------------------------------------------------- #

@mcp.tool()
def list_blueprints() -> list[str]:
    """
    List all blueprints (CompositionDefinitions) in the cluster with their
    chart descriptions.

    Returns a list of strings describing each blueprint (name, namespace,
    description).
    """
    try:
        result = subprocess.run(
            ["kubectl", "get", "compositiondefinitions", "-A", "-o", "json"],
            capture_output=True, text=True, check=True, timeout=15,
        )
        data = json.loads(result.stdout)
        items = data.get("items", [])

        descriptions: list[str] = []
        for item in items:
            meta = item.get("metadata", {})
            name = meta.get("name")
            namespace = meta.get("namespace")
            chart = item.get("spec", {}).get("chart")
            if not name or not namespace:
                continue
            desc = "N/A"
            try:
                desc = _get_chart_description(chart)
            except Exception as e:
                log.warning("Failed to get description for %s: %s", name, e)
            descriptions.append(f"name: {name}, namespace: {namespace}, description: {desc}")

        if not descriptions:
            return ["No blueprints (CompositionDefinitions) are currently installed in the cluster. Use list_marketplace_blueprints to see what's available to install."]
        return descriptions
    except Exception as e:
        return [f"Error listing blueprints: {e}. Try list_marketplace_blueprints instead."]


@mcp.tool()
def get_blueprint(name: str, namespace: str) -> list[str]:
    """
    Get the files of a specific blueprint (CompositionDefinition) by name and
    namespace.

    Returns a list of strings, each representing a file's content in the
    blueprint chart.
    """
    try:
        result = subprocess.run(
            ["kubectl", "get", "compositiondefinition", "-n", namespace,
             "--field-selector", f"metadata.name={name}", "-o", "json"],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        items = data.get("items", [])
        if not items:
            return [f"Error: CompositionDefinition '{name}' not found in namespace '{namespace}'"]

        chart = items[0].get("spec", {}).get("chart")
        if not chart:
            return [f"Error: CompositionDefinition '{name}' has no chart spec"]

        return _get_blueprint_files(chart)
    except subprocess.CalledProcessError as e:
        return [f"Error: kubectl failed: {e.stderr.strip() if e.stderr else e}"]
    except Exception as e:
        return [f"Error: {e}"]


@mcp.tool()
def get_blueprint_form(name: str, namespace: str) -> str:
    """
    Get the form URL for a specific blueprint by name and namespace.

    Returns the form URL if available, or a descriptive error/status message.
    """
    try:
        label_selector = (
            f"krateo.io/blueprint-form-name={name},"
            f"krateo.io/blueprint-form-namespace={namespace}"
        )
        result = subprocess.run(
            ["kubectl", "get", "forms.widgets.templates.krateo.io",
             "-A", "-o", "json", "-l", label_selector],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(result.stdout)
        items = data.get("items", [])
        if not items:
            return "No forms found."

        labels = items[0].get("metadata", {}).get("labels", {})
        form_path = labels.get("krateo.io/blueprint-form-path", "").strip("/")
        if not form_path:
            return "Form found, but no path label set."

        frontend = _get_frontend_address()
        if "Failed" in frontend:
            return "Could not get frontend address."
        return f"Form found: http://{frontend}/{form_path}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_marketplace_blueprint(name: str, version: Optional[str] = None) -> list[str]:
    """
    Get the files of a Krateo marketplace blueprint by name (and optionally
    version). If version is omitted, the latest available version is used.

    Returns a list of strings, each representing a file's content.
    """
    try:
        if version is None:
            index = yaml.safe_load(
                requests.get("https://marketplace.krateo.io/index.yaml", timeout=10).text
            )
            entries = index.get("entries", {})
            if name not in entries:
                return [f"Error: Blueprint '{name}' not found in marketplace"]
            versions = entries[name]
            if not versions:
                return [f"Error: No versions for blueprint '{name}'"]
            version = versions[0].get("version")

        chart = {"url": "https://marketplace.krateo.io", "version": version, "repo": name}
        return _get_blueprint_files(chart)
    except Exception as e:
        return [f"Error: {e}"]


@mcp.tool()
def list_marketplace_blueprints() -> list[str]:
    """
    List all available blueprints in the Krateo marketplace.

    Returns a list of blueprint names.
    """
    try:
        index = yaml.safe_load(
            requests.get("https://marketplace.krateo.io/index.yaml", timeout=10).text
        )
        return list(index.get("entries", {}).keys())
    except Exception as e:
        return [f"Error: {e}"]


@mcp.tool()
def gen_values_schema_json(values: str) -> str:
    """
    Generate a values.schema.json from the given values.yaml string.

    Parses # @schema annotations (krateoctl gen-schema format) and returns the
    resulting JSON Schema as a string.

    Args:
        values: Content of a Helm chart's values.yaml file.

    Returns:
        JSON Schema string, or an error message.
    """
    try:
        return generate_schema_json(values)
    except Exception as e:
        return f"Error generating schema: {e}"


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
