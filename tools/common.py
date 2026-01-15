import os
import logging
import subprocess
import yaml
import tempfile
import uuid

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
            ["./tools/scripts/install_krateo.sh", str(installation_method)],
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

def gen_values_schema_json(values: str) -> str:
    """
    Generates the values.schema.json from the values.yaml string.
    
    Args:
        values: A string containing the content of a Helm chart's
                      values.yaml file.

    Returns:
        A string containing the generated JSON schema if successful.
        A string containing the error message from stderr if the command fails.
    """
    random_suffix = uuid.uuid4()
    values_filename = f"tmp-values-{random_suffix}.yaml"
    values_schema_json = f"tmp-values-{random_suffix}.schema.json"

    try:
        with open(values_filename, 'w', encoding='utf-8') as f:
            f.write(values)

        command = ["krateoctl", "gen-schema", values_filename]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode != 0:
            error_message = f"Error executing krateoctl: {result.stderr}"
            return error_message

        if not os.path.exists(values_schema_json):
            return f"Error: Command executed but '{values_schema_json}' was not created."

        with open(values_schema_json, 'r', encoding='utf-8') as f:
            schema_json_content = f.read()

        return schema_json_content.replace('"additionalProperties": false', '"additionalProperties": true')

    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        if os.path.exists(values_filename):
            os.remove(values_filename)
        if os.path.exists(values_schema_json):
            os.remove(values_schema_json)
    
def get_admin_psw() -> str:
    """
    Gets the password of the predefined `admin` account in Krateo
    
    Returns: 
        str: The admin's password.
    """
    
    command = 'kubectl get secret admin-password -n krateo-system -o jsonpath="{.data.password}" | base64 -d'
    try:
        log.debug("Running kubectl to fetch admin password.")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )   

        password = result.stdout
        log.info("Successfully retrieved admin password (decoded).")
        return password    
    
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}"

def validate_yaml(yaml_content: str) -> str:
    """
    Validates if the provided string is a valid Kubernetes YAML using kubectl dry-run.
    If you have multiple yaml files to verify, append them with the '---' separator.

    Args:
        yaml_content (str): The YAML content as a string.

    Returns:
        str: A message indicating whether the YAML is valid or not.
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_file.write(yaml_content)
        temp_file_path = temp_file.name
    
    try:
        result = subprocess.run(
            ['kubectl', 'apply', '--dry-run=server', '-f', temp_file_path],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            return f"YAML is valid."
        else:
            return f"YAML is invalid. Error:\n{result.stderr}"
        
    except Exception as e:
        return f"An error occurred during validation: {str(e)}"
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
