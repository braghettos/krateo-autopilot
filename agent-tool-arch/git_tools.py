import os
import json
import requests
import logging
import time
from . import create_repo_secret as repo_secret

log = logging.getLogger(__name__)

def get_github_user_name() -> str:
    """
    Fetches the authenticated user's name from a Github Personal Access Token.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN environment variable not set.")
        raise ValueError("Error: GITHUB_TOKEN environment variable not set.")
    
    log.info("GITHUB_TOKEN found in environment variables.")
    
    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        username = user_data.get("login")
        
        log.info("Successfully fetched GitHub username: %s", username)
        return username

    except requests.exceptions.HTTPError as e:
        # API returned 4xx or 5xx
        log.warning("GitHub API returned an error: %s", e)
        return None
    except requests.exceptions.RequestException as e:
        log.error("Request to GitHub API failed: %s", e)
        return None
    except Exception as e:
        log.critical("Unexpected error while fetching GitHub username: %s", e)
        raise

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
        
        # explicitly enable Actions
        actions_url = f"https://api.github.com/repos/{owner}/{name}/actions/permissions"
        actions_data = {"enabled": True, "allowed_actions": "all"}
        requests.put(actions_url, headers=headers, json=actions_data)
        
        # add repo secret
        log.info(f"Adding GIT_TOKEN secret to the new repository '{name}'...")
        repo_secret.create_or_update_repo_secret(
            owner=owner,
            repo=name,  
            secret_name="GIT_TOKEN",
            secret_value=token
        )
        
        return response_data

    except Exception as err:
        log.error(f"Failed to create repository '{name}': {err}")
        print(f"An unexpected error occurred: {err}")    

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    template_owner = "EdmondDantes21"
    template_repo = "actions-templates"
    new_repo_name = "krateo-autopilot-composition-example-8"
    # new_repo_owner = "leovice-org"
    new_repo_owner = "EdmondDantes21"  # For testing purposes, create under your own user
    
    create_repo_from_template(template_owner, template_repo, new_repo_name, new_repo_owner, private=False)