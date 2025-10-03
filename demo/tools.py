import os
import json
import logging
import subprocess
import yaml
import tempfile
import uuid

log = logging.getLogger(__name__)

def get_widget(widget: str) -> str:
    """
    Get the widget detailed specification from the given widget string.

    Args:
        widget (str): The widget string. Available widgets are: "BarChart", "Button", "Column", "EventList",
        "FlowChart", "Form", "LineChart", "Markdown", "NavMenuItem", "Page", "Panel", "Paragraph",
        "PieChart", "Row", "Table", "TabList", "YamlViewer".
    Returns:
        str: The detailed specification of the widget.
    """
    
    widget = os.path.basename(widget) # Extract the base name to prevent directory traversal
    widget_path = f"portal-agent-granular/widgets/{widget}.md"
    
    try:
        log.debug(f"Trying to access widget file at path: {widget_path}")
        with open(widget_path, 'r') as file:
            return file.read()
    except Exception as e:
        log.error(f"Error reading file '{widget_path}': {e}")
        return f"Error reading file '{widget_path}': {str(e)}"

def get_widgets(widgets: list[str]) -> dict[str, str]:
    """
    Get the detailed specifications for a list of widgets.

    Args:
        widgets (list[str]): A list of widget strings. Available widgets are: "BarChart", "Button", "Column", "EventList",
        "FlowChart", "Form", "LineChart", "Markdown", "NavMenuItem", "Page", "Panel", "Paragraph",
        "PieChart", "Row", "Table", "TabList", "YamlViewer".
    Returns:
        dict[str, str]: A dictionary mapping each widget string to its detailed specification.
    """
    return {widget: get_widget(widget) for widget in widgets}

def check_yaml(yaml_content: str) -> str:
    """
    Checks if the provided YAML string is a valid Kubernetes manifest
    by running 'kubectl apply --dry-run=server'.

    Args:
        yaml_content (str): A string containing the Kubernetes YAML manifest.

    Returns:
        str: A message indicating whether the YAML is valid, including the
             output or error from kubectl.
    """
    command = ['kubectl', 'apply', '--dry-run=server', '-f', '-']

    try:
        result = subprocess.run(    # TODO: use k8s py library to do this because spawning a process is SLOW
            command,
            input=yaml_content,
            capture_output=True,
            text=True,
            check=False 
        )

        if result.returncode == 0:
            log.info(f"YAML is valid.")
            return f"YAML is valid"
        else:
            log.error(f"YAML is invalid.\n---\n{result.stderr.strip()}")
            return f"YAML is invalid.\n---\n{result.stderr.strip()}"

    except Exception as e:
        log.critical(f"An unexpected error occurred: {e}")
        return f"Error: An unexpected error occurred: {e}"

def check_yamls(yaml_contents: list[str]) -> str:
    """
    Validate a list of Kubernetes YAML manifests.

    Args:
        yaml_contents (list[str]): A list of YAML manifest strings to validate.

    Returns:
        str: A JSON string mapping the index of each YAML document in the input
        list to the validation result returned by `check_yaml`.
    """ 
    results = {i: check_yaml(yaml_contents[i]) for i in range(len(yaml_contents))}
    return json.dumps(results)

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
    
def _is_valid_json(content: str) -> bool:
    """
    Verifies if a given string represents a valid JSON object.

    Args:
        content: The string content to be validated.

    Returns:
        True if the string is valid JSON, False otherwise.
    """
    # Ensure the input is a string, as json.loads() requires it.
    if not isinstance(content, str):
        return False
        
    try:
        json.loads(content)
    except json.JSONDecodeError:
        return False
    return True

def create_file(filename: str, content: str) -> str:
    """Creates a file with the given content, including any necessary subdirectories.
    
    Args:
        filename (str): The name of the file to create.
        content (str): The content to write to the file.
    
    Returns:
        str: A message indicating success or failure.
    """
    # If the filename ends with .json, validate the content first.
    if filename.endswith('.json'):
        if not _is_valid_json(content):
            return f"Error creating file '{filename}': Invalid JSON content."
        
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

        return schema_json_content

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

if __name__ == "__main__":
    # Example usage
    widget_name = "non-existent-widget"
    print(get_widget(widget_name)) # Error
    
    widget_name = "Form"
    print(get_widget(widget_name)) # Success
    
    widget_name = "../../etc/passwd"
    print(get_widget(widget_name)) # Error