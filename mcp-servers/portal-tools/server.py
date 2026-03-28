"""
krateo-portal-tools MCP Server

Exposes 2 tools via Streamable HTTP (FastMCP):
  - get_widget   - returns widget spec markdown by name
  - get_widgets  - returns multiple widget specs
"""

import logging
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

_port = int(os.getenv("PORT", "8080"))
mcp = FastMCP(
    "krateo-portal-tools",
    host="0.0.0.0",
    port=_port,
    streamable_http_path="/mcp",
    transport_security=None,
)

WIDGETS_DIR = Path(__file__).parent / "widgets"

AVAILABLE_WIDGETS = [
    "BarChart", "Button", "Column", "DataGrid", "EventList", "Filter",
    "FlowChart", "Form", "InlineGroup", "LineChart", "Markdown", "NavMenu",
    "NavMenuItem", "Page", "Panel", "Paragraph", "PieChart", "Route",
    "RoutesLoader", "Row", "TabList", "Table", "YamlViewer",
]


@mcp.tool()
def get_widget(widget: str) -> str:
    """
    Get the detailed specification of a Krateo portal widget.

    Available widgets: BarChart, Button, Column, DataGrid, EventList, Filter,
    FlowChart, Form, InlineGroup, LineChart, Markdown, NavMenu, NavMenuItem,
    Page, Panel, Paragraph, PieChart, Route, RoutesLoader, Row, TabList,
    Table, YamlViewer.

    Args:
        widget: The widget name (case-sensitive, e.g. "Button").

    Returns:
        The widget specification markdown, or an error message.
    """
    # Prevent directory traversal
    safe_name = Path(widget).name
    widget_path = WIDGETS_DIR / f"{safe_name}.md"

    try:
        return widget_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            f"Widget '{safe_name}' not found. "
            f"Available widgets: {', '.join(AVAILABLE_WIDGETS)}"
        )
    except Exception as e:
        return f"Error reading widget spec for '{safe_name}': {e}"


@mcp.tool()
def get_widgets(widgets: list[str]) -> list[str]:
    """
    Get the detailed specifications for multiple Krateo portal widgets.

    Args:
        widgets: List of widget names (e.g. ["Button", "Table"]).

    Returns:
        List of widget specification strings (one per requested widget).
    """
    return [get_widget(w) for w in widgets]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
