import subprocess
import yaml
import logging
from .get_blueprint import _get_blueprint_files

log = logging.getLogger(__name__)

def _get_latest_blueprint_version(name: str) -> str:
    """Get the latest version of a blueprint from the Krateo marketplace index."""
    log.debug(f"Fetching latest version for blueprint '{name}'")
    
    try:
        index_url = "https://marketplace.krateo.io/index.yaml"
        response = subprocess.run(
            ["curl", "-sL", index_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        index_data = yaml.safe_load(response.stdout)
        entries = index_data.get("entries", {})
        
        if name not in entries:
            raise ValueError(f"Blueprint '{name}' not found in marketplace")
        
        versions = entries[name]
        if not versions or not isinstance(versions, list):
            raise ValueError(f"No versions found for blueprint '{name}'")
        
        latest = versions[0].get("version")
        if not latest:
            raise ValueError(f"Could not determine latest version for blueprint '{name}'")
        
        return latest
    
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to fetch marketplace index: {e.stderr}")
        raise RuntimeError(f"Failed to fetch marketplace index: {e.stderr.strip() if e.stderr else str(e)}") from e
    except Exception as e:
        log.exception(f"Error getting latest version for '{name}'")
        raise

def get_marketplace_blueprint(name: str, version: str | None = None) -> list[str]:
    """
    Get the files of a Krateo blueprint by name from the Krateo marketplace.
    
    Args:
        name (str): The name of the Krateo blueprint (e.g., 'portal-blueprint-page').
        version (str | None): The version of the blueprint (e.g., '1.0.6'). 
                              If None, uses the latest available version.
        
    Returns:
        list[str]: A list of strings, each representing a file's content
                   in the blueprint chart.
    """
    log.info(f"Getting Krateo blueprint: name='{name}', version='{version or 'latest'}'")
    
    try:
        # If version not specified, fetch the latest
        if version is None:
            version = _get_latest_blueprint_version(name)
            log.info(f"Using latest version for '{name}': {version}")
        
        chart = {
            "url": "https://marketplace.krateo.io",
            "version": version,
            "repo": name
        }
        
        return _get_blueprint_files(chart)
    
    except Exception as e:
        log.exception(f"Failed to get Krateo blueprint '{name}' version '{version}'")
        return [f"Error: Failed to download Krateo blueprint '{name}' version '{version}': {type(e).__name__}: {str(e)}"]

def list_marketplace_blueprints() -> list[str]:
    """
    List all available blueprints in the Krateo marketplace.
    
    Returns:
        list[str]: A list of blueprint names available in the marketplace.
    """
    log.info("Listing Krateo blueprints from marketplace")
    
    try:
        # Pull the index.yaml from the Krateo marketplace
        index_url = "https://marketplace.krateo.io/index.yaml"
        response = subprocess.run(
            ["curl", "-sL", index_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        index_data = yaml.safe_load(response.stdout)
        
        blueprints = list(index_data.get("entries", {}).keys())
        log.info(f"Found {len(blueprints)} blueprints in Krateo marketplace")
        
        return blueprints
    
    except subprocess.CalledProcessError as e:
        log.error(f"Failed to fetch Krateo marketplace index: {e.stderr}")
        return [f"Error: Failed to fetch Krateo marketplace index: {e.stderr.strip() if e.stderr else str(e)}"]
    
    except Exception as e:
        log.exception("Unexpected error while listing Krateo blueprints")
        return [f"Unexpected error: {type(e).__name__}: {str(e)}"]
