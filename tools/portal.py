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

def get_widgets(widgets: list[str]) -> list[str, str]:
    """
    Get the detailed specifications for a list of widgets.

    Args:
        widgets (list[str]): A list of widget strings. Available widgets are: "BarChart", "Button", "Column", "DataGrid", "EventList",
        "Filter", "FlowChart", "Form", "LineChart", "Markdown", "NavMenu", "NavMenuItem", "Page", "Panel", "Paragraph",
        "PieChart", "Route", "RoutesLoader", "Row", "Table", "TabList", "YamlViewer".
    Returns:
        list[str, str]: A list of tuples mapping each widget string to its detailed specification.
    """
    return [get_widget(widget) for widget in widgets]
