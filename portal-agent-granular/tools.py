import os
import json
import logging
import subprocess

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

if __name__ == "__main__":
    # Example usage
    widget_name = "non-existent-widget"
    print(get_widget(widget_name)) # Error
    
    widget_name = "Form"
    print(get_widget(widget_name)) # Success
    
    widget_name = "../../etc/passwd"
    print(get_widget(widget_name)) # Error