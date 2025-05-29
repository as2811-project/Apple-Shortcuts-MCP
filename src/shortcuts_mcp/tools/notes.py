"""Notes creation tool using MacOS Shortcuts."""

import subprocess
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from ..server import BaseTool


class NotesTool(BaseTool):
    """Tool for creating notes via MacOS Shortcuts."""

    def register_with_mcp(self, mcp: FastMCP) -> None:
        """Register notes methods with MCP server."""
        mcp.tool()(self.create_note)

    def create_note(self, summary: str) -> Dict[str, Any]:
        """
        Tool to create a summary of the chat conversation using MacOS Shortcuts.
        :param summary: string; content of the summary
        :return: Status
        """
        shortcut_command = f'shortcuts run "Claude Notes" <<< "{summary}"'

        try:
            process = subprocess.run(
                shortcut_command, shell=True, capture_output=True, text=True)

            if process.returncode != 0:
                error_msg = f"Failed to run shortcut: {process.stderr}"
                print(f"Error executing shortcut: {process.stderr}")
                return {"status": "failed", "message": error_msg}

            print(f"Successfully created note.")
            return {"status": "success"}

        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            print(f"An error occurred: {e}")
            return {"status": "failed", "message": error_msg}
