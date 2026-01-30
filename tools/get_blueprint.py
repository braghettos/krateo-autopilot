import subprocess
import json
import tarfile
from pathlib import Path
import logging
import tempfile

log = logging.getLogger(__name__)

def _is_relevant_file(member: str) -> bool:
    """Return True if this file should be included in files_content."""
    if member.endswith("_helpers.tpl"):
        return False
    return (
        "templates/" in member or
        member.endswith("/Chart.yaml") or
        member.endswith("/values.yaml")
    )

def _extract_chart_files(chart_path: Path) -> list[str]:
    """Extract and read relevant files from a Helm chart tarball."""
    files_content = []
    
    with tarfile.open(chart_path, mode="r:gz") as tar:
        for member in tar.getmembers():
            if member.isfile() and _is_relevant_file(member.name):
                f = tar.extractfile(member)
                if f:
                    content = f.read().decode("utf-8")
                    files_content.append(f"# File: {member.name}\n{content}")
    
    return files_content

def _get_blueprint_files(chart: dict) -> list[str]:
    """
    Download a Helm or OCI chart using `helm pull` and return the contents 
    of each relevant file inside the chart as a list of strings.
    
    Args:
        chart: Dictionary containing chart information with keys:
               - url (str): The chart URL or repo URL
               - version (str, optional): The chart version
               - repo (str, optional): The chart name (for Helm repos) or additional path component (for OCI)
    
    Returns:
        list[str]: A list of strings, each representing a file's content
    
    Raises:
        ValueError: If chart is missing required fields
        RuntimeError: If helm pull fails
    """
    log.debug(f"Downloading chart: {chart}")
    
    # Validate chart structure
    if not isinstance(chart, dict):
        log.error(f"Invalid chart type: expected dict, got {type(chart).__name__}")
        raise ValueError(f"Chart must be a dictionary, got {type(chart).__name__}")
    
    url = chart.get("url")
    if not url:
        log.error("Chart is missing required 'url' field")
        raise ValueError("Chart must contain a 'url' field")
    
    version = chart.get("version")
    repo = chart.get("repo")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        try:
            is_oci = url.startswith("oci://")
            
            if is_oci:  # OCI registry
                if repo:
                    chart_url = f"{url}/{repo}"
                else:
                    chart_url = url
                
                # Add version if provided
                if version:
                    chart_url = f"{chart_url}:{version}"
                
                log.debug(f"Processing OCI chart from URL '{chart_url}'")
                
                # Pull the OCI chart
                pull_cmd = ["helm", "pull", chart_url, "--destination", str(tmpdir_path)]
                log.debug(f"Pulling OCI chart: {chart_url}")
                subprocess.run(pull_cmd, check=True, capture_output=True)
            
            else:  # Traditional Helm registry
                if not repo:
                    log.error("Helm chart is missing required 'repo' field")
                    raise ValueError("Helm chart (non-OCI) must contain a 'repo' field")
                
                if not version:
                    log.error("Helm chart is missing required 'version' field")
                    raise ValueError("Helm chart (with 'repo') must contain a 'version' field")
                
                log.debug(f"Processing Helm chart '{repo}' from registry '{url}' version '{version}'")
                
                # Add and update the Helm repo (using a fixed alias name)
                repo_alias = "temp-repo"
                subprocess.run(
                    ["helm", "repo", "add", repo_alias, url],
                    check=True,
                    capture_output=True
                )
                subprocess.run(
                    ["helm", "repo", "update", repo_alias],
                    check=True,
                    capture_output=True
                )
                
                # Pull the chart (repo is the chart name)
                chart_ref = f"{repo_alias}/{repo}"
                log.debug(f"Pulling Helm chart: {chart_ref} version {version}")
                subprocess.run(
                    ["helm", "pull", chart_ref, "--version", version, "--destination", str(tmpdir_path)],
                    check=True,
                    capture_output=True
                )
            
            # Find the downloaded .tgz file
            tgz_files = list(tmpdir_path.glob("*.tgz"))
            if not tgz_files:
                raise RuntimeError("No .tgz file found after helm pull")
            
            chart_path = tgz_files[0]
            log.debug(f"Extracting chart from: {chart_path}")
            
            return _extract_chart_files(chart_path)
        
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            log.exception(f"Helm command failed: {error_msg}")
            raise RuntimeError(f"Failed to pull chart: {error_msg}") from e
        
        except Exception as e:
            log.exception(f"Failed to download chart from {url}")
            raise RuntimeError(f"Failed to download chart: {type(e).__name__}: {str(e)}") from e

def get_blueprint(name: str, namespace: str) -> list[str]:
    """
    Get the files of a specific blueprint by name and namespace.
    
    Use these files to organize the blueprint explanation as follows:
    - Blueprint overview: provide a brief summary of what the blueprint does.
    - Customization Options: list the options available in values.yaml
    - Composition example: an example composition.yaml for this blueprint. in the api version, make sure to use the version that Chart.yaml version
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
        log.debug(f"kubectl output: {result.stdout}")
        
        data = json.loads(result.stdout)
        items = data.get("items", [])
        
        # Handle case where no resources are found
        if not items:
            log.warning(f"CompositionDefinition '{name}' not found in namespace '{namespace}'")
            return [f"Error: CompositionDefinition '{name}' not found in namespace '{namespace}'. "
                    f"Please verify the blueprint name and namespace are correct."]
        
        # Get the first item (should be the only one with field-selector)
        resource = items[0]
        
        # Check if spec and chart exist
        spec = resource.get("spec")
        if not spec:
            log.error(f"CompositionDefinition '{name}' has no spec field")
            return [f"Error: CompositionDefinition '{name}' is malformed (missing 'spec' field)"]
        
        chart = spec.get("chart")
        if not chart:
            log.error(f"CompositionDefinition '{name}' has no chart in spec")
            return [f"Error: CompositionDefinition '{name}' is malformed (missing 'spec.chart' field)"]
        
        return _get_blueprint_files(chart)
    
    except subprocess.CalledProcessError as e:
        log.error(f"kubectl command failed: {e.stderr}")
        return [f"Error: Failed to query Kubernetes. Details: {e.stderr.strip() if e.stderr else str(e)}"]
    
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse kubectl output as JSON: {e}")
        return [f"Error: Invalid response from Kubernetes API (JSON parsing failed)"]
    
    except IndexError:
        log.warning(f"CompositionDefinition '{name}' not found in namespace '{namespace}'")
        return [f"Error: CompositionDefinition '{name}' not found in namespace '{namespace}'"]
    
    except Exception as e:
        log.exception(f"Unexpected error while getting blueprint '{name}' in namespace '{namespace}'")
        return [f"Unexpected error: {type(e).__name__}: {str(e)}"]
