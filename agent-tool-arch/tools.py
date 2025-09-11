import os
import yaml
import json
import tempfile
import requests
import logging
import subprocess
from pathlib import Path
from base64 import b64encode

log = logging.getLogger(__name__)

def apply_manifest(manifest: str) -> str:
    """
    Applies a Kubernetes manifest string to the Kubernetes cluster.

    This function can handle strings containing single or multiple YAML documents
    separated by '---'. It works by writing the manifest content to a 
    temporary file and then using `kubectl apply -f` to apply it.

    Args:
        manifest: A string containing the Kubernetes YAML manifest(s).

    Returns:
        str: A string with the stdout and stderr from the kubectl command, 
             or an error message.
    """
    # Check if the manifest string is empty or just whitespace
    if not manifest or not manifest.strip():
        return "Error: Manifest string cannot be empty."
    
    temp_filename = None
    try:
        try:
            list(yaml.safe_load_all(manifest))
        except yaml.YAMLError as e:
            return f"Error: Invalid YAML format.\nDetails: {e}"
        
        # Use a temporary file to store the manifest string
        with tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False) as tmp_file:
            temp_filename = tmp_file.name
            tmp_file.write(manifest)

        command = ["kubectl", "apply", "-f", temp_filename]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False  # Check the result manually
        )
        
        output = ""
        if result.stdout:
            output += f"STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"STDERR:\n{result.stderr}"
        
        return output.strip()

    except FileNotFoundError:
        return "Error: 'kubectl' command not found. Please ensure it is installed and in your system's PATH."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
    finally:
        if temp_filename and os.path.exists(temp_filename):
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
    
def read_file(file_path: str) -> str:
    """Reads the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file or an error message if the file cannot be read.
    """
    try:
        log.debug(f"Reading file at path: {file_path}")
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        log.error(f"Error reading file '{file_path}': {e}")
        return f"Error reading file '{file_path}': {str(e)}"