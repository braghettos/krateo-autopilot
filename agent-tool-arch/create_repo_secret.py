import os
import requests
from base64 import b64encode
from nacl import encoding, public

import logging
log = logging.getLogger(__name__)

def get_repo_public_key(owner: str, repo: str) -> dict:
    """
    Gets the public key required to encrypt secrets for a repository.

    Args:
        owner (str): The account owner of the repository.
        repo (str): The name of the repository.

    Returns:
        A dictionary containing the key and key_id, or None if the request fails.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN environment variable not set.")
        raise ValueError("GITHUB_TOKEN environment variable not set. Please provide a classic GitHub token.")
    
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/public-key"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        log.info(f"Successfully fetched public key for {owner}/{repo}.")
        return response.json()
    except requests.exceptions.RequestException as e:
        log.error(f"Error fetching public key: {e}")
        log.error(f"Response content: {e.response.text if e.response else 'No response'}")
        return None

def encrypt_secret(public_key: str, secret_value: str) -> str:
    """
    Encrypts a secret value using the repository's public key.

    Args:
        public_key: The public key string from the GitHub API.
        secret_value: The secret string to encrypt.

    Returns:
        The base64 encoded encrypted secret.
    """
    public_key_bytes = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key_bytes)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def create_or_update_repo_secret(
    owner: str,
    repo: str,
    secret_name: str,
    secret_value: str,
) -> bool:
    """
    Creates or updates a secret in a GitHub repository.

    Args:
        owner: The account owner of the repository.
        repo: The name of the repository.
        secret_name: The name of the secret.
        secret_value: The value of the secret.

    Returns:
        True if the secret was created/updated successfully, False otherwise.
    """
    # Get GitHub token from environment variable
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        log.error("GITHUB_TOKEN environment variable not set.")
        raise ValueError("GITHUB_TOKEN environment variable not set. Please provide a classic GitHub token.")
    
    # Fetch the public key for the repository
    log.info("Fetching repository public key...")
    public_key = get_repo_public_key(owner, repo)
    if not public_key:
        log.error("Could not retrieve public key. Aborting.")
        return False

    key = public_key["key"]
    key_id = public_key["key_id"]
    
    # Encrypt the secret value
    log.info("Encrypting secret value...")
    encrypted_value = encrypt_secret(key, secret_value)
    log.info("Secret value encrypted successfully.")
    
    # Create or update the secret via GitHub API
    url = f"https://api.github.com/repos/{owner}/{repo}/actions/secrets/{secret_name}"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    data = {
        "encrypted_value": encrypted_value,
        "key_id": key_id,
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        response.raise_for_status()

        if response.status_code == 201:
            log.info(f"Successfully created secret '{secret_name}' in '{owner}/{repo}'.")
            return True
        elif response.status_code == 204:
            log.info(f"Successfully updated secret '{secret_name}' in '{owner}/{repo}'.")
            return True
        else:
            log.error(f"Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        log.error(f"Error creating/updating secret: {e}")
        log.error(f"Response content: {e.response.text if e.response else 'No response'}")
        return False

def main():
    """
    Main function to demonstrate the process of creating a repository secret.
    """
    logging.basicConfig(level=logging.DEBUG)
    # --- Configuration ---
    REPO_OWNER = "EdmondDantes21"  # The owner of the repository (e.g., your GitHub username)
    REPO_NAME = "krateo-autopilot-composition-example"   # The name of the repository
    SECRET_NAME = "MY_API_KEY_4"
    SECRET_VALUE = "this_is_a_very_secret_value_12345"

    if not all([REPO_OWNER, REPO_NAME]):
        log.error("Please set GITHUB_TOKEN, REPO_OWNER, and REPO_NAME variables in the script.")
        return

    log.info(f"\nStep 3: Creating/updating secret '{SECRET_NAME}'...")
    success = create_or_update_repo_secret(
        owner=REPO_OWNER,
        repo=REPO_NAME,
        secret_name=SECRET_NAME,
        secret_value=SECRET_VALUE,
    )

    if success:
        log.info("\nProcess completed successfully!")
    else:
        log.info("\nProcess failed.")

if __name__ == "__main__":
    main()