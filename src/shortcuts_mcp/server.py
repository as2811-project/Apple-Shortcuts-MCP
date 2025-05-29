"""Base MCP Server class for organizing tools."""

import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv


class BaseMCPServer:
    """Base class for MCP server with tool management."""

    def __init__(self, name: str):
        """Initialize the MCP server."""
        load_dotenv()
        self.mcp = FastMCP(name)
        self.tools: List[BaseTool] = []

    def register_tool(self, tool: 'BaseTool') -> None:
        """Register a tool with the MCP server."""
        self.tools.append(tool)
        tool.register_with_mcp(self.mcp)

    def run(self, transport: str = 'stdio') -> None:
        """Run the MCP server."""
        self.mcp.run(transport=transport)


class BaseTool(ABC):
    """Abstract base class for MCP tools."""

    @abstractmethod
    def register_with_mcp(self, mcp: FastMCP) -> None:
        """Register this tool's methods with the MCP server."""
        pass
