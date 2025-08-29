import os
import yaml
import json
import tempfile
import requests
import subprocess
from pathlib import Path
from base64 import b64encode

def apply_manifest(manifest: str) -> str:
    """
    Applies a Kubernetes manifest string to the Kubernetes cluster.

    This function works by writing the manifest content to a temporary
    file and then using `kubectl apply -f` to apply it.

    Args:
        manifest: A string containing the Kubernetes YAML manifest.

    Returns:
        str: A string with the stdout and stderr from the kubectl command.
    """
    # Check if the manifest string is empty
    if not manifest or not manifest.strip():
        return "Error: Manifest string cannot be empty."
    
    try:
        # Validate that the manifest is a valid YAML file
        try:
            yaml.safe_load(manifest)
        except yaml.YAMLError as e:
            return f"Error: Invalid YAML format.\nDetails: {e}"
        
        # Use a temporary file to store the manifest
        tmp_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False)
        temp_filename = tmp_file.name
        tmp_file.write(manifest)
        tmp_file.close()

        command = ["kubectl", "apply", "-f", temp_filename]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False 
        )
        return f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"

    except FileNotFoundError:
        # This error occurs if kubectl is not installed or not in the PATH
        error_message = "Error: 'kubectl' command not found. Please ensure it is installed and in your system's PATH."
        return False, error_message
    except Exception as e:
        # Catch any other unexpected errors
        return False, f"An unexpected error occurred: {str(e)}"
    finally:
        # Clean up the temporary file
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)

def install_krateo(installation_method: int) -> str:
    """This tool installs Krateo PlatformOps on the current Kubernetes cluster.
    
    Args:
        installation_method (int): The method to use for installation.
        0 : Basic installation.
        1 : Installation with LoadBalancer using external IP.
        2 : Installation with LoadBalancer using external hostname.
    
    Returns:
        str: status and result or error msg.
    """
    
    try:
        result = subprocess.run(
            ["./scripts/install_krateo.sh", str(installation_method)],
            capture_output=True,
            text=True,
            check=True
        )
        post_installation_message = ""
        match installation_method:
            case 0:
                post_installation_message = open("scripts/Basic.txt").read()
            case 1:
                post_installation_message = open("scripts/LoadBalancerExternalIP.txt").read()
            case 2:
                post_installation_message = open("scripts/LoadBalancerExternalHostname.txt").read()
        
        return result.stdout + "\n" + post_installation_message
    except subprocess.CalledProcessError as e:
        return f"Installation failed with error:\n{e.stderr}"
    except FileNotFoundError:
        return "Script install_krateo.sh not found or not executable."

def create_file(filename: str, content: str) -> str:
    """Creates a file with the given content, including any necessary subdirectories.
    
    Args:
        filename (str): The name of the file to create.
        content (str): The content to write to the file.
    
    Returns:
        str: A message indicating success or failure.
    """
    try:
        directory = os.path.dirname(filename)
        
        # Create the directory if it does not exist
        if directory:
            os.makedirs(directory, exist_ok=True)
            
        with open(filename, 'w') as f:
            f.write(content)
            
        return f"File '{filename}' created successfully."
    except Exception as e:
        return f"Error creating file '{filename}': {str(e)}"

def create_repository(repo_name: str, description: str = "", private: bool = True) -> str:
    """Creates a new Github repository with the given name.
    
    Args:
        repo_name (str): The name of the repository to create.
        description (str, optional): A short description of the repository.
        private (boolean, optional): Whether repo should be private. 

    Returns:
        str: A message indicating success or failure, including the repo URL on success.
    """
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable not set. Please create a personal access token and set it."

    url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "name": repo_name,
        "description": description,
        "private": private
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        if response.status_code == 201:  # 201 Created is the success code
            repo_url = response.json().get("html_url")
            return f"Successfully created repository '{repo_name}'. URL: {repo_url}"
        else:
            return f"Failed to create repository. Status code: {response.status_code}, Response: {response.text}"

    except requests.exceptions.HTTPError as http_err:
        if response.status_code == 422:
            return f"Error: Repository '{repo_name}' already exists. Details: {response.json().get('errors', '')}"
        return f"HTTP error occurred: {http_err} - {response.text}"
    except requests.exceptions.RequestException as err:
        return f"An error occurred: {err}"
    
def create_or_update_file(branch: str, content: str, message: str, owner: str, path: str, repo: str, sha: str = None) -> str:
    """Creates or updates a file in a GitHub repository.

    Args:
        branch (str): The branch to create or update the file in.
        content (str): The content of the file.
        message (str): The commit message.
        owner (str): The owner of the repository (username or organization).
        path (str): Path where to create/update the file.
        repo (str): The name of the repository.
        sha (str, optional): Required if updating an existing file. The blob SHA of the file being replaced.

    Returns:
        str: A message indicating success or failure.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable not set. Please create a personal access token and set it."

    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    data = {
        "branch": branch,
        "content": b64encode(content.encode()).decode(),
        "message": message,
    }
    if sha:
        data["sha"] = sha  # Include SHA for updates

    try:
        response = requests.put(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()

        if response.status_code in [200, 201]:  # 200 OK for update, 201 Created for new file
            action = "updated" if sha else "created"
            return f"Successfully {action} file '{path}' in repository '{repo}'."
        else:
            return f"Failed to create/update file. Status code: {response.status_code}, Response: {response.text}"

    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err} - {response.text}"
    except requests.exceptions.RequestException as err:
        return f"An error occurred: {err}"

def push_chart_to_ghcr(path: str, owner: str) -> str:
    """
    Packages a Helm chart, authenticates to GHCR, pushes the chart,
    and cleans up credentials.

    Args:
        path (str): The local filesystem path to the Helm chart directory.
        owner (str): The GitHub username or organization name who owns the repository.

    Returns:
        str: A message indicating success or failure.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable is not set."

    chart_path = Path(path) / "chart"
    chart_yaml_path = chart_path / "Chart.yaml"
    
    print(f"Packaging Helm chart from path: {chart_path}")
    print(f"Looking for Chart.yaml at: {chart_yaml_path}")

    if not chart_yaml_path.is_file():
        print(f"Chart.yaml not found at path: {chart_yaml_path}")
        return f"Error: Chart.yaml not found at path: {chart_yaml_path}"

    # 1. Read Chart.yaml to get name and version
    try:
        with open(chart_yaml_path, 'r') as f:
            chart_info = yaml.safe_load(f)
        chart_name = chart_info.get("name")
        chart_version = chart_info.get("version")
        if not chart_name or not chart_version:
            print("Chart.yaml is missing 'name' or 'version' fields.")
            return "Error: Could not find 'name' or 'version' in Chart.yaml."
    except Exception as e:
        print(f"Error reading or parsing Chart.yaml: {e}")
        return f"Error reading or parsing Chart.yaml: {e}"

    # 2. Package the Helm chart
    packaged_chart_file = f"{chart_name}-{chart_version}.tgz"
    try:
        subprocess.run(
            ["helm", "package", str(chart_path)],
            check=True,
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        print("Helm CLI not found. Please ensure it is installed and in your PATH.")
        return "Error: Helm CLI not found. Please ensure it is installed and in your PATH."
    except subprocess.CalledProcessError as e:
        print(f"Error packaging Helm chart: {e.stderr}")
        return f"Helm packaging failed: {e.stderr}"

    # 3. Authenticate with GHCR using the GITHUB_TOKEN
    registry = "ghcr.io"
    oci_url = f"oci://{registry}/{owner.lower()}"
    try:
        login_command = [
            "helm", "registry", "login", registry,
            "--username", owner,
            "--password-stdin"
        ]
        # Pass the token securely to the command's standard input
        subprocess.run(
            login_command,
            input=token,
            text=True,
            check=True,
            capture_output=True
        )
    except subprocess.CalledProcessError as e:
        return f"Helm registry login failed: {e.stderr}"

    # 4. Push the chart and clean up
    try:
        push_command = ["helm", "push", packaged_chart_file, oci_url]
        result = subprocess.run(push_command, check=True, capture_output=True, text=True)
        # Clean up the local packaged chart file
        os.remove(packaged_chart_file)
        return f"Successfully pushed {chart_name}:{chart_version} to {oci_url}\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        return f"Helm push failed: {e.stderr}"
    finally:
        # 5. Log out from the registry as a security best practice
        subprocess.run(["helm", "registry", "logout", registry], check=False)

def apply_composition_definition(path: str, owner: str) -> str: 
    """Applies a Composition Defintiion to the Kubernetes cluster.
    
    This function packages and pushes the Helm chart located at `path` to the GitHub Container Registry (GHCR)
    under the specified `owner`, then applies the `compositiondefinition.yaml` file in that path to the Kubernetes cluster.

    Args:
        path (str): The local filesystem path to the `compositiondefinition.yaml` file.
        owner (str): The GitHub username or organization name who owns the repository.

    Returns:
        str: A message indicating success or failure.
    """
    composition_definition_path = Path(path) / "compositiondefinition.yaml"
    
    if not composition_definition_path.is_file():
        return f"Error: compositiondefinition.yaml not found at path: {composition_definition_path}"
    
    # Step 0: Build Helm dependency
    try:
        subprocess.run(
            ["helm", "dependency", "build"],
            cwd=path + "/chart",
            capture_output=True,
            text=True,
            check=False
        )
    except subprocess.CalledProcessError as e:
        return f"Helm dependency build failed: {e.stderr}"
    
    # Step 1: Push Helm chart to GHCR
    push_result = push_chart_to_ghcr(path, owner)
    if "Error" in push_result or "failed" in push_result.lower():
        return f"Failed to push Helm chart: {push_result}"

    # Step 2: Apply the composition definition using kubectl
    try:
        with open(composition_definition_path, 'r') as f:
            manifest = f.read()
        apply_result = apply_manifest(manifest)
        return f"Composition definition applied successfully.\n{apply_result}"
    except Exception as e:
        return f"Error applying composition definition: {e}"