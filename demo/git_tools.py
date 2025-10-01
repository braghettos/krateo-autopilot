import os
import json
import requests
import logging
import time
import base64
from typing import Dict, Any

log = logging.getLogger(__name__)

def create_repo_from_template(template_owner: str, template_repo: str, name: str, owner: str, private: bool = False):
    """
    Creates a new GitHub repository from a template.

    Args:
        template_owner (str): The owner of the template repository.
        template_repo (str): The name of the template repository.
        name (str): The name of the new repository to be created.
        owner (str): The owner (user or organization) of the new repository.
        private (bool, optional): Whether the new repository should be private. Defaults to False.
    """
    log.info(f"Creating repository '{name}' from template '{template_owner}/{template_repo}'.")
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN environment variable not set.")
        raise ValueError("GITHUB_TOKEN environment variable not set. Please provide a classic GitHub token.")

    url = f"https://api.github.com/repos/{template_owner}/{template_repo}/generate"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    data = {
        "owner": owner,
        "name": name,
        "private": private,
    }

    log.info(f"Attempting to create repository '{name}' from template '{template_owner}/{template_repo}'...")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        response_data = response.json()
        log.info(f"Repository '{name}' created successfully at {response_data['html_url']}.")
        
        time.sleep(1) # TODO: find a better solution
        
        # explicitly enable Actions
        actions_url = f"https://api.github.com/repos/{owner}/{name}/actions/permissions"
        actions_data = {"enabled": True, "allowed_actions": "all"}
        requests.put(actions_url, headers=headers, json=actions_data)
        
        return response_data

    except Exception as err:
        log.error(f"Failed to create repository '{name}': {err}")

def get_file_contents(
    owner: str,
    repo: str,
    path: str = "",
    ref: str = "",
    sha: str = ""
) -> Dict[str, Any]:
    """Fetches the contents of a file or lists the contents of a directory from a GitHub repository.

    Args:
        owner (str, required): Repository owner (username or organization).
        repo (str, required): Repository name.
        path (str, required): Path to the file or directory.
        ref (str, optional): An optional git ref such as a branch, tag, or pull request.
        sha (str, optional): An optional commit SHA. If specified, it overrides the ref.

    Returns:
        A dictionary containing the type of content ('file' or 'directory') and the corresponding data.
        - For a file: {'type': 'file', 'content': '...', 'sha': '...'}
        - For a directory: {'type': 'directory', 'listing': [...]}
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("The GITHUB_TOKEN environment variable is not set.")

    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}"
    }
    params = {}
    if sha:
        params['ref'] = sha
    elif ref:
        params['ref'] = ref

    response = requests.get(api_url, headers=headers, params=params)
    response.raise_for_status()

    response_data = response.json()

    if isinstance(response_data, list):
        # Path was a directory
        return {"type": "directory", "listing": response_data}
    elif isinstance(response_data, dict) and 'content' in response_data:
        # Path was a file
        encoded_content = response_data['content']
        decoded_content_bytes = base64.b64decode(encoded_content)
        return {
            "type": "file",
            "content": decoded_content_bytes.decode('utf-8'),
            "sha": response_data['sha']
        }
    else:
        raise TypeError("Unexpected response format from GitHub API.")
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    template_owner = "EdmondDantes21"
    template_repo = "actions-templates"
    new_repo_name = "krateo-autopilot-composition-example-8"
    new_repo_owner = "leovice-org"
    # new_repo_owner = "EdmondDantes21"  # For testing purposes, create under your own user
    
    create_repo_from_template(template_owner, template_repo, new_repo_name, new_repo_owner, private=False)