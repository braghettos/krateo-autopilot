import os
import logging
import subprocess

log = logging.getLogger(__name__)

def get_widget(widget: str) -> str:
    """
    Get the widget detailed specification from the given widget string.

    Args:
        widget (str): The widget string. Available widgets are: "BarChart", "Button", "Column", "DataGrid", "EventList",
        "Filter", "FlowChart", "Form", "LineChart", "Markdown", "NavMenu", "NavMenuItem", "Page", "Panel", "Paragraph",
        "PieChart", "Route", "RoutesLoader", "Row", "Table", "TabList", "YamlViewer".
    Returns:
        str: The detailed specification of the widget.
    """
    
    widget = os.path.basename(widget) # Extract the base name to prevent directory traversal
    widget_path = f"tools/widgets/{widget}.md"
    
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
        widgets (list[str]): A list of widget strings. Available widgets are: "BarChart", "Button", "Column", "DataGrid", "EventList",
        "Filter", "FlowChart", "Form", "LineChart", "Markdown", "NavMenu", "NavMenuItem", "Page", "Panel", "Paragraph",
        "PieChart", "Route", "RoutesLoader", "Row", "Table", "TabList", "YamlViewer".
    Returns:
        dict[str, str]: A dictionary mapping each widget string to its detailed specification.
    """
    return {widget: get_widget(widget) for widget in widgets}

def validate_yaml(content: str) -> str:
    command = ['kubectl', 'apply', '--dry-run=server', '-f', '-']

    try:
        result = subprocess.run(
            command,
            input=content,
            capture_output=True,
            text=True,
            check=False 
        )

        if result.returncode == 0:
            return "YAML is valid."
        else:
            return f"YAML is invalid: {result.stderr.strip()}"

    except Exception as e:
        return f"An unexpected error occurred: {e}"

def apply_manifest(manifest: str) -> str:
    """
    Applies a Kubernetes manifest from a string to the Kubernetes cluster.
    
    Args:
        manifest (str): The string content of the YAML manifest to apply..
        
    Returns:
        str: The stdout message from kubectl indicating success, or an error message.
    """

    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            capture_output=True,
            text=True,
            input=manifest,  # Pass the YAML string as input
            check=True       # Raise an error if kubectl fails
        )
        return result.stdout.strip()

    except Exception as e:
        return f"Unexpected error: {str(e)}"
