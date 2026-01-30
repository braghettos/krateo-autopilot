import subprocess
import json
import requests
import yaml
import logging
log = logging.getLogger(__name__)

def get_chart_description(chart) -> str:
    log.info(f"Getting chart description for: {chart}")
    url = chart.get("url")
    version = chart.get("version")
    repo = chart.get("repo")
    
    is_oci = url.startswith("oci://")
    
    if not is_oci: # Helm registry
        chart_url = f"{url.rstrip('/')}/index.yaml"
        response = requests.get(chart_url)
        response.raise_for_status()
        index_data = yaml.safe_load(response.text)
        
        chart_entries = index_data.get("entries", {}).get(repo, [])
        chart = next((c for c in chart_entries if c.get("version") == version), None)
        
        if chart:
            return chart.get("description", "No description available")
        else:
            return f"Chart '{repo}' with version '{version}' not found in index.yaml"
    
    # OCI registry
    if repo:
        chart_url = f"{url}/{repo}"
    else:
        chart_url = url
    if version:
        chart_url = f"{chart_url}:{version}"
    
    log.debug(f"Processing OCI chart from URL '{chart_url}'")
    try:
        result = subprocess.run(
            ["helm", "show", "chart", chart_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        for line in result.stdout.splitlines():
            if line.strip().startswith("description:"):
                return line.split("description:", 1)[1].strip()
        
        return ""  # No description found
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Error running helm: {e.stderr.strip()}")

def list_blueprints() -> list[str]:
    """
    List all blueprints in the cluster with their chart descriptions.
    
    Returns:
        list[str]: A list of strings describing each blueprint.
                   Returns empty list if operation fails.
    """
    log.info("Listing all blueprints in the cluster.")
    
    try:
        cmd = ["kubectl", "get", "compositiondefinitions", "-A", "-o", "json"]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            check=True,
            timeout=10
        )
        log.debug(f"kubectl command executed successfully. Return code: {result.returncode}")
        
        data = json.loads(result.stdout)
        items = data.get("items", [])
        log.info(f"Found {len(items)} compositiondefinitions")
        
        descriptions = []
        for item in items:
            metadata = item.get("metadata", {})
            spec = item.get("spec", {})
            
            name = metadata.get("name")
            namespace = metadata.get("namespace")
            chart = spec.get("chart")
            
            if not name or not namespace:
                log.warning(f"Item missing required fields (name: {name}, namespace: {namespace}), skipping")
                continue
            
            # Handle chart description failure gracefully without breaking the loop
            chart_description = "N/A"
            try:
                chart_description = get_chart_description(chart)
            except Exception as chart_error:
                log.warning(f"Failed to get chart description for blueprint '{name}': {chart_error}")
            
            descriptions.append(
                f"name: {name}, namespace: {namespace}, description: {chart_description}"
            )
        
        log.info(f"Successfully processed {len(descriptions)} blueprints")
        return descriptions
        
    except subprocess.TimeoutExpired:
        log.error("kubectl command timed out after 10 seconds", exc_info=True)
        return []
    except subprocess.CalledProcessError as e:
        log.error(f"kubectl command failed with exit code {e.returncode}: {e.stderr}", exc_info=True)
        return []
    except FileNotFoundError:
        log.error("kubectl command not found. Please ensure kubectl is installed and in PATH", exc_info=True)
        return []
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse kubectl output as JSON: {e}", exc_info=True)
        return []
    except KeyError as e:
        log.error(f"Unexpected JSON structure, missing key: {e}", exc_info=True)
        return []
    except Exception as e:
        log.error(f"Unexpected error while listing blueprints: {e}", exc_info=True)
        return []