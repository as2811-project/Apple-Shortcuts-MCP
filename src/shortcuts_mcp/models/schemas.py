"""Pydantic models for the Shortcuts MCP server."""

from pydantic import BaseModel


class Ingredients(BaseModel):
    """Model for recipe ingredients."""
    name: str
    quantity: str


class ToolResult(BaseModel):
    """Standard result model for tool operations."""
    status: str
    message: str = ""
    data: dict = {}
