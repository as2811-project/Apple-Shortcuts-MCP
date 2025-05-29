"""Notes creation tool using MacOS Shortcuts."""

import subprocess
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from ..server import BaseTool


class CalendarTool(BaseTool):
    """Tool for creating calendar events via MacOS Shortcuts."""

    def register_with_mcp(self, mcp: FastMCP) -> None:
        """Register calendar methods with MCP server."""
        mcp.tool()(self.create_event)

    def create_event(self, title: str, start: str, end: str) -> Dict[str, Any]:
        """
        Tool to add a calendar event.
        :param title: string; title of the event
        :param start: string; start date and time of the event (ex. "31/05/2025 14:30")
        :param end: string; end date and time of the event (ex. "31/05/2025 15:30")
        :return: Status
        """
        shortcut_command = f'shortcuts run "Add New Event" <<< "{title}, {start}, {end}"'

        try:
            process = subprocess.run(
                shortcut_command, shell=True, capture_output=True, text=True)

            if process.returncode != 0:
                error_msg = f"Failed to run shortcut: {process.stderr}"
                print(f"Error executing shortcut: {process.stderr}")
                return {"status": "failed", "message": error_msg}

            print(f"Successfully created event.")
            return {"status": "success"}

        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            print(f"An error occurred: {e}")
            return {"status": "failed", "message": error_msg}
