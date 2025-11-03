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
    
    if repo: # Helm registry
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
    chart_url = f"{url}:{version}" if version else url
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
    """
    log.info("Listing all blueprints in the cluster.")
    try:
        cmd = ["kubectl", "get", "compositiondefinitions", "-A", "-o", "json"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        descriptions = []
        for item in data.get("items", []):
            chart = item.get("spec").get("chart")   
            name = item.get("metadata").get("name")
            namespace = item.get("metadata").get("namespace")
            
            descriptions.append(f"name: {name}, namespace: {namespace}, description: {get_chart_description(chart)}")
                
        return descriptions       
        
    except Exception as e:
        return []
