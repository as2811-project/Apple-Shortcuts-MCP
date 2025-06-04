"""Pydantic models for the Shortcuts MCP server."""

from pydantic import BaseModel
from typing import Optional, List


class Ingredients(BaseModel):
    """Model for recipe ingredients."""
    name: str
    quantity: str


class ToolResult(BaseModel):
    """Standard result model for tool operations."""
    status: str
    message: str = ""
    data: dict = {}


class StoreProduct(BaseModel):
    """Model for a product from a grocery store."""
    description: str
    price: float
    unit: Optional[str] = None
    is_weighted: Optional[bool] = False


class ItemComparison(BaseModel):
    """Model for comparing a single item across stores."""
    item: str
    coles: Optional[StoreProduct] = None
    woolworths: Optional[StoreProduct] = None


class PriceComparisonSummary(BaseModel):
    """Model for price comparison summary."""
    coles_total: float
    woolworths_total: float
    cheaper_store: Optional[str] = None
    savings: float


class PriceComparisonResult(BaseModel):
    """Model for complete price comparison results."""
    status: str
    items_compared: int
    results: List[ItemComparison]
    summary: PriceComparisonSummary
    message: Optional[str] = None
