import subprocess
import json
import requests
import tarfile
from urllib.parse import urljoin
import io
import logging
log = logging.getLogger(__name__)
from tools.get_blueprint_form import get_blueprint_form

def is_relevant_file(member, repo) -> bool:
    """Return True if this file should be included in files_content."""
    if member.endswith("_helpers.tpl"):
        return False
    return (
        member.startswith(f"{repo}/templates/") or
        member in {f"{repo}/Chart.yaml", f"{repo}/values.yaml"}
    )
    
def download_chart(chart) -> list[str]:
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
    else: # OCI registry
        chart_url = f"{url}:{version}" if version else url
    
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

def get_blueprint(name: str, namespace: str) -> str:
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
        return f"{get_blueprint_form(name, namespace)}\n{download_chart(chart)}"
       
    except Exception as e:
        return f"Unexpected error: {str(e)}"
