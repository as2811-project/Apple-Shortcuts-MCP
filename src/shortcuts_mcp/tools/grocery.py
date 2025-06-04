"""Grocery price comparison tool for Coles and Woolworths."""

from functools import cache
import requests
import json
import re
import time
import random
from typing import Dict, Any, List, Optional, Tuple
from mcp.server.fastmcp import FastMCP

from ..server import BaseTool


class GroceryTool(BaseTool):
    """Tool for comparing grocery prices between Coles and Woolworths."""

    def __init__(self):
        """Initialize the grocery tool."""
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/113.0.0.0 Safari/537.36",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def register_with_mcp(self, mcp: FastMCP) -> None:
        """Register grocery price comparison methods with MCP server."""
        mcp.tool()(self.compare_grocery_prices)

    def _parse_item_with_weight(self, item_string: str) -> Tuple[str, Optional[float], Optional[str]]:
        """
        Parse item string to extract name, weight, and unit.

        Examples:
        - "garlic 100g" -> ("garlic", 100.0, "g")
        - "carrots 1kg" -> ("carrots", 1.0, "kg") 
        - "milk 3L" -> ("milk 3L", None, None)  # Keep volume in name
        - "bread" -> ("bread", None, None)

        Returns: (item_name, weight_amount, weight_unit)
        """
        # Regex to match weight patterns like "100g", "1kg", "1.5kg", "500g"
        weight_pattern = r'^(.+?)\s+(\d+(?:\.\d+)?)\s*(g|kg)$'
        match = re.match(weight_pattern, item_string.strip(), re.IGNORECASE)

        if match:
            item_name = match.group(1).strip()
            weight_amount = float(match.group(2))
            weight_unit = match.group(3).lower()
            return item_name, weight_amount, weight_unit
        else:
            # No weight specified, return as-is
            return item_string.strip(), None, None

    def _calculate_price_for_weight(self, product_data: Dict[str, Any],
                                    requested_weight: float, requested_unit: str) -> Dict[str, Any]:
        """
        Calculate price based on requested weight for weighted items.
        """
        if not product_data.get("is_weighted"):
            # Not a weighted item, return package price as-is
            return {
                **product_data,
                "note": f"Fixed package price (requested {requested_weight}{requested_unit})"
            }

        # Extract per-kg price from the unit string
        unit_str = product_data.get("unit", "")
        per_kg_match = re.search(r'\$(\d+\.?\d*)\s*per\s*1?kg', unit_str)

        if per_kg_match:
            per_kg_price = float(per_kg_match.group(1))

            # Convert requested weight to kg
            if requested_unit in ['g', 'gram', 'grams']:
                weight_in_kg = requested_weight / 1000
            elif requested_unit in ['kg', 'kilo', 'kilos', 'kilogram']:
                weight_in_kg = requested_weight
            else:
                # Default to grams if unclear
                weight_in_kg = requested_weight / 1000

            calculated_price = per_kg_price * weight_in_kg

            return {
                **product_data,
                "price": round(calculated_price, 2),
                "calculated_for": f"{requested_weight}{requested_unit}",
                "original_per_kg_price": per_kg_price
            }

        # Fallback: couldn't parse per-kg price, return original
        return {
            **product_data,
            "note": f"Could not calculate for {requested_weight}{requested_unit}, showing package price"
        }

    def _calculate_woolworths_price_for_weight(self, product_data: Dict[str, Any],
                                               requested_weight: float, requested_unit: str) -> Dict[str, Any]:
        """
        Calculate price based on requested weight for Woolworths weighted items.
        """
        unit_str = product_data.get("unit", "")

        # Look for per-kg pricing in Woolworths format like "$11.50 / 1KG"
        per_kg_match = re.search(
            r'\$(\d+\.?\d*)\s*/\s*1?kg', unit_str, re.IGNORECASE)

        if per_kg_match:
            per_kg_price = float(per_kg_match.group(1))

            if requested_unit in ['g', 'gram', 'grams']:
                weight_in_kg = requested_weight / 1000
            elif requested_unit in ['kg', 'kilo', 'kilos', 'kilogram']:
                weight_in_kg = requested_weight
            else:
                weight_in_kg = requested_weight / 1000

            calculated_price = per_kg_price * weight_in_kg

            return {
                **product_data,
                "price": round(calculated_price, 2),
                "calculated_for": f"{requested_weight}{requested_unit}",
                "original_per_kg_price": per_kg_price
            }

        # Fallback: couldn't parse per-kg price, return original
        return {
            **product_data,
            "note": f"Could not calculate for {requested_weight}{requested_unit}, showing package price"
        }

    @cache
    def _get_coles_build_id(self) -> str:
        """Get the build ID required for Coles API calls."""
        resp = self.session.get(
            "https://www.coles.com.au/", headers=self.headers)
        resp.raise_for_status()
        html = resp.text

        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>',
            html,
        )
        if not m:
            raise RuntimeError("Could not locate __NEXT_DATA__ in Coles HTML")

        payload = json.loads(m.group(1))
        build_id = payload.get("buildId")
        if not build_id:
            raise RuntimeError("buildId not found in __NEXT_DATA__")
        return build_id

    def _search_coles(self, term: str, build_id: str) -> Optional[Dict[str, Any]]:
        """Search for a product on Coles."""
        try:
            delay = round(random.uniform(1.5, 3.5), 2)
            time.sleep(delay)

            url = f"https://www.coles.com.au/_next/data/{build_id}/en/search/products.json?q={term}"
            r = self.session.get(url, headers=self.headers)
            r.raise_for_status()
            data = r.json()

            results = data.get("pageProps", {}).get(
                "searchResults", {}).get("results", [])
            for item in results:
                if item.get("_type") == "PRODUCT":
                    desc = item.get("description", "<no description>")
                    pricing = item.get("pricing", {})

                    unit_info = pricing.get("unit", {})
                    is_weighted = unit_info.get("isWeighted", False)

                    # Use comparable price only for truly weighted items
                    comparable = pricing.get("comparable")
                    if comparable and is_weighted:
                        price_match = re.search(r'\$(\d+\.?\d*)', comparable)
                        if price_match:
                            price = float(price_match.group(1))
                            return {
                                "description": desc,
                                "price": price,
                                "unit": comparable,
                                "is_weighted": True
                            }

                    # Use regular "now" price for pre-packaged items or as fallback
                    price = pricing.get("now")
                    if price is not None:
                        unit_display = comparable if comparable else ""
                        return {
                            "description": desc,
                            "price": price,
                            "unit": unit_display,
                            "is_weighted": is_weighted
                        }
            return None
        except Exception as e:
            print(f"Error searching Coles for '{term}': {e}")
            return None

    def _search_woolworths(self, term: str) -> Optional[Dict[str, Any]]:
        """Search for a product on Woolworths."""
        try:
            url = "https://www.woolworths.com.au/apis/ui/Search/products"
            params = {"searchTerm": term}
            headers = {
                "User-Agent": self.headers["User-Agent"],
                "Accept": "application/json, text/plain, */*",
            }
            r = requests.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()

            for section in data.get("Products", []):
                for product in section.get("Products", []):
                    name = product.get("Name") or product.get(
                        "DisplayName", "Unknown")
                    price = product.get("Price")
                    unit = product.get("CupString", "")
                    if name and price is not None:
                        return {"description": name, "price": price, "unit": unit}
            return None
        except Exception as e:
            print(f"Error searching Woolworths for '{term}': {e}")
            return None

    def compare_grocery_prices(self, items: List[str]) -> Dict[str, Any]:
        """
        Compare grocery prices between Coles and Woolworths for a list of items.
        Items can include weights: ["garlic 100g", "carrots 1kg", "milk 3L", "bread"]

        :param items: List of grocery items to search for, optionally with weights
        :return: Detailed price comparison results
        """
        try:
            build_id = self._get_coles_build_id()
            coles_total = 0
            woolies_total = 0
            comparison_results = []

            for item in items:
                # Parse item to separate name and weight
                item_name, requested_weight, weight_unit = self._parse_item_with_weight(
                    item)

                print(f"🔍 Searching for: {item_name}" +
                      (f" (calculating for {requested_weight}{weight_unit})" if requested_weight else ""))

                coles_result = self._search_coles(item_name, build_id)
                woolies_result = self._search_woolworths(item_name)

                # Process results
                item_comparison = {
                    "item": item,
                    "item_name": item_name,
                    "requested_amount": f"{requested_weight}{weight_unit}" if requested_weight else None,
                    "coles": None,
                    "woolworths": None
                }

                if coles_result:
                    # Calculate price based on requested weight if specified
                    if requested_weight and weight_unit:
                        coles_processed = self._calculate_price_for_weight(
                            coles_result, requested_weight, weight_unit)
                    else:
                        coles_processed = coles_result

                    item_comparison["coles"] = {
                        "description": coles_processed["description"],
                        "price": coles_processed["price"],
                        "unit": coles_processed.get("unit", ""),
                        "is_weighted": coles_processed.get("is_weighted", False),
                        **{k: v for k, v in coles_processed.items()
                           if k in ["calculated_for", "note", "original_per_kg_price"]}
                    }
                    coles_total += coles_processed["price"]

                if woolies_result:
                    # Calculate price based on requested weight if specified
                    if requested_weight and weight_unit:
                        woolies_processed = self._calculate_woolworths_price_for_weight(
                            woolies_result, requested_weight, weight_unit)
                    else:
                        woolies_processed = woolies_result

                    item_comparison["woolworths"] = {
                        "description": woolies_processed["description"],
                        "price": woolies_processed["price"],
                        "unit": woolies_processed.get("unit", ""),
                        **{k: v for k, v in woolies_processed.items()
                           if k in ["calculated_for", "note", "original_per_kg_price"]}
                    }
                    woolies_total += woolies_processed["price"]

                comparison_results.append(item_comparison)

            # Calculate summary
            summary = {
                "coles_total": round(coles_total, 2),
                "woolworths_total": round(woolies_total, 2),
                "cheaper_store": None,
                "savings": 0
            }

            if coles_total > 0 and woolies_total > 0:
                difference = abs(coles_total - woolies_total)
                summary["cheaper_store"] = "Coles" if coles_total < woolies_total else "Woolworths"
                summary["savings"] = round(difference, 2)

            return {
                "status": "success",
                "items_compared": len(items),
                "results": comparison_results,
                "summary": summary
            }

        except Exception as e:
            return {
                "status": "failed",
                "message": f"Error comparing prices: {str(e)}"
            }
