"""Recipe extraction tool using Gemini API."""

import os
from typing import Dict, Any
from google.genai import types
from google import genai
from mcp.server.fastmcp import FastMCP

from ..server import BaseTool
from ..models.schemas import Ingredients


class RecipeTool(BaseTool):
    """Tool for extracting recipes using Gemini API."""

    def __init__(self):
        """Initialize the recipe tool."""
        self.api_key = os.getenv("GEMINI_API_KEY")

    def register_with_mcp(self, mcp: FastMCP) -> None:
        """Register recipe methods with MCP server."""
        mcp.tool()(self.get_recipe)

    async def get_recipe(self, url: str) -> str:
        """
        Use this resource to send the URL provided by the user to the Gemini API
        :param url: URL or file path to the recipe
        :return: JSON string of ingredients list
        """
        try:
            if not self.api_key:
                return "Error: GEMINI_API_KEY environment variable not set"

            client = genai.Client(api_key=self.api_key)

            response = client.models.generate_content(
                model='models/gemini-2.5-flash-preview-05-20',
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=url)
                        ),
                        types.Part(
                            text='Extract the ingredients and its quantities (by weight or just by number)')
                    ]
                ),
                config={
                    "response_mime_type": "application/json",
                    "response_schema": list[Ingredients]
                }
            )

            return response.text

        except Exception as e:
            return f"Error processing recipe: {str(e)}"
