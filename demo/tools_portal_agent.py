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

def validate_yaml(content: str) -> bool:
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
            return True
        else:
            raise ValueError(f"YAML is invalid: {result.stderr.strip()}")

    except Exception as e:
        raise ValueError(f"An unexpected error occurred: {e}")

def create_file(filename: str, content: str) -> str:
    """Creates a file with the given content, including any necessary subdirectories.
    
    Args:
        filename (str): The name of the file to create.
        content (str): The content to write to the file.
    
    Returns:
        str: A message indicating success or failure.
    """    
    if filename.endswith('.yaml') or filename.endswith('.yml'):
        try: 
            validate_yaml(content)
        except ValueError as e:
            return f"Error creating file '{filename}': {str(e)}"
        
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

def apply_manifest(file_path: str) -> str:
    """
    Applies a Kubernetes manifest file (YAML) to the Kubernetes cluster .
    
    Args:
        file_path (str): Path to the manifest file.
        
    Returns:
        str: A message indicating success or failure.
    """

    try:
        result = subprocess.run(
            ["kubectl", "apply", "-f", file_path],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()

    except Exception as e:
        return f"Unexpected error: {str(e)}"

def apply_manifests(file_paths: list[str]) -> list[str]:
    results = []
    for path in file_paths:
        result = apply_manifest(path)
        results.append(result)
    return results

# apply manifest
# create_file
# get_widgets