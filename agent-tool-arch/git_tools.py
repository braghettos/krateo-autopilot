import os
import yaml
import json
import tempfile
import requests
import subprocess
from pathlib import Path
from base64 import b64encode

def get_github_user_name() -> str:
    """
    Fetches the authenticated user's name from a Github Personal Access Token.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("Error: GITHUB_TOKEN environment variable not set.")

    url = "https://api.github.com/user"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        user_data = response.json()
        return user_data.get("login")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")

def create_repo_from_template(template_owner: str, template_repo: str, name: str, private: bool = False):
    """
    Creates a new GitHub repository from a template.

    Args:
        template_owner (str): The owner of the template repository.
        template_repo (str): The name of the template repository.
        name (str): The name of the new repository to be created.
        private (bool, optional): Whether the new repository should be private. Defaults to False.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set. Please provide a classic GitHub token.")

    url = f"https://api.github.com/repos/{template_owner}/{template_repo}/generate"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {token}",
    }
    data = {
        "owner": get_github_user_name(),
        "name": name,
        "private": private,
    }

    print(f"Attempting to create repository '{name}' from template '{template_owner}/{template_repo}'...")

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        response_data = response.json()
        print(f"Successfully created repository '{response_data['full_name']}'!")
        print(f"URL: {response_data['html_url']}")
        return response_data

    except Exception as err:
        print(f"An unexpected error occurred: {err}")    
