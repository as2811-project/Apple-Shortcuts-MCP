"""Main application entry point for Shortcuts MCP server."""

from .server import BaseMCPServer
from .tools.recipe import RecipeTool
from .tools.shortcuts import ShortcutsTool
from .tools.notes import NotesTool
from .tools.calendar import CalendarTool
# from .tools.example import ExampleTool


class ShortcutsMCPServer(BaseMCPServer):
    """Main MCP server for Shortcuts integration."""

    def __init__(self):
        """Initialize the Shortcuts MCP server with all tools."""
        super().__init__("Shortcuts-MCP")
        self._register_tools()

    def _register_tools(self):
        """Register all available tools."""
        # Register recipe tool
        recipe_tool = RecipeTool()
        self.register_tool(recipe_tool)

        # Register shortcuts tool
        shortcuts_tool = ShortcutsTool()
        self.register_tool(shortcuts_tool)

        # Register notes tool
        notes_tool = NotesTool()
        self.register_tool(notes_tool)

        # Register calendar tool
        calendar_tool = CalendarTool()
        self.register_tool(calendar_tool)


def main():
    """Main entry point."""
    server = ShortcutsMCPServer()
    server.run(transport='stdio')


if __name__ == "__main__":
    main()
