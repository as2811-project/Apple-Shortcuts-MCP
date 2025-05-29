"""MacOS Shortcuts integration tool."""

import subprocess
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

from ..server import BaseTool


class ShortcutsTool(BaseTool):
    """Tool for integrating with MacOS Shortcuts."""

    def register_with_mcp(self, mcp: FastMCP) -> None:
        """Register shortcuts methods with MCP server."""
        mcp.tool()(self.create_list)

    def create_list(self, items: str) -> Dict[str, Any]:
        """
        Tool to create a list of recipes. Pass the ingredients extracted via the get_recipe() resource as a comma separated list i.e., "item 1 500g, item 2 2x". The MacOS Shortcut expects a comma separated string only.
        :param items: List of objects, each containing a name and quantity"
        :return: Status dictionary
        """
        shortcut_command = f'shortcuts run "Add Items to Groceries List" <<< "{items}"'

        try:
            process = subprocess.run(
                shortcut_command, shell=True, capture_output=True, text=True)

            if process.returncode != 0:
                error_msg = f"Failed to run shortcut: {process.stderr}"
                print(f"Error executing shortcut: {process.stderr}")
                return {"status": "failed", "message": error_msg}

            print(f"Successfully added items to groceries list: {items}")
            return {"status": "success", "ingredients_added": items}

        except Exception as e:
            error_msg = f"Server error: {str(e)}"
            print(f"An error occurred: {e}")
            return {"status": "failed", "message": error_msg}
