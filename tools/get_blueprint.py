import subprocess
import json
import requests
import tarfile
from urllib.parse import urljoin
import io
import logging
import tempfile
from pathlib import Path
import os
from tools.get_blueprint_form import get_blueprint_form
log = logging.getLogger(__name__)

def is_relevant_file(member, repo) -> bool:
    """Return True if this file should be included in files_content."""
    if member.endswith("_helpers.tpl"):
        return False
    return (
        "templates/" in member or
        member in {f"{repo}/Chart.yaml", f"{repo}/values.yaml"}
    )
    
def get_blueprint_files_from_helm_repo(chart_url: str, repo: str) -> list[str]:
    response = requests.get(chart_url)
    response.raise_for_status()
    chart_bytes = io.BytesIO(response.content)
    
    files_content = []
    with tarfile.open(fileobj=chart_bytes, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile() and is_relevant_file(member.name, repo):
                f = tar.extractfile(member)
                if f:
                    content = f.read().decode("utf-8")
                    files_content.append(f"# File: {member.name}\n{content}")
    
    return files_content

def get_blueprint_files_from_oci_registry(chart_url: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        subprocess.run(
            ["helm", "pull", chart_url, "--untar", "--untardir", str(tmpdir_path)],
            check=True
        )

        file_contents = []
        for root, _, files in os.walk(tmpdir_path):
            for file in files:
                file_path = Path(root) / file
                
                if is_relevant_file(str(file_path), str(root)):
                    content = file_path.read_text(encoding="utf-8")
                    file_contents.append(f"# File: {file_path.relative_to(tmpdir_path)}\n{content}")
    
        return file_contents
 
def get_blueprint_files(chart) -> list[str]:
    """
    Download a Helm or OCI chart and return the contents of each file
    inside the chart as a list of strings.
    """
    log.info(f"Downloading chart: {chart}")
    url = chart.get("url")
    version = chart.get("version")
    repo = chart.get("repo")
    
    if repo: # Helm registry
        chart_filename = f"{repo}-{version}.tgz"
        chart_url = urljoin(url + "/", chart_filename)
        return get_blueprint_files_from_helm_repo(chart_url, repo)
    else: # OCI registry
        chart_url = f"{url}:{version}" if version else url
        return get_blueprint_files_from_oci_registry(chart_url)
    
def get_blueprint(name: str, namespace: str) -> list[str]:
    """
    Get the files of a specific blueprint by name and namespace.
    
    Use these files to organize the blueprint explanation as follows:
    - Blueprint overview: provide a brief summary of what the blueprint does.
    - Customization Options: list the options available in values.yaml
    - Blueprint form: provide the link to the form if available.
    
    Args:
        name (str): The name of the blueprint.
        namespace (str): The namespace of the blueprint.
        
    Returns:
        list[str]: A list of strings, each representing a file's content
                   in the blueprint chart.
    """
    log.info(f"Getting blueprint: name='{name}', namespace='{namespace}'")
    try:
        cmd = [
            "kubectl", "get", "compositiondefinition",
            "-n", namespace,
            "--field-selector", f"metadata.name={name}",
            "-o", "json"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout).get("items", [])[0]
        chart = data.get("spec").get("chart")
        
        blueprint_form = get_blueprint_form(name, namespace)
        blueprint_files = get_blueprint_files(chart)
        return blueprint_files + [blueprint_form]
       
    except Exception as e:
        return [f"Unexpected error: {str(e)}"]

