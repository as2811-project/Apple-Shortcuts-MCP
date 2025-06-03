"""Grocery price comparison tool for Coles and Woolworths."""

from functools import cache
import requests
import json
import re
import time
import random
from typing import Dict, Any, List, Optional
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
                    price = item.get("pricing", {}).get("now")
                    if price is not None:
                        return {"description": desc, "price": price}
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

        :param items: List of grocery items to search for
        :return: Detailed price comparison results
        """
        try:
            build_id = self._get_coles_build_id()
            coles_total = 0
            woolies_total = 0
            comparison_results = []

            for item in items:
                print(f"🔍 Searching for: {item}")

                # Search both stores
                coles_result = self._search_coles(item, build_id)
                woolies_result = self._search_woolworths(item)

                # Process results
                item_comparison = {
                    "item": item,
                    "coles": None,
                    "woolworths": None
                }

                if coles_result:
                    item_comparison["coles"] = {
                        "description": coles_result["description"],
                        "price": coles_result["price"]
                    }
                    coles_total += coles_result["price"]

                if woolies_result:
                    item_comparison["woolworths"] = {
                        "description": woolies_result["description"],
                        "price": woolies_result["price"],
                        "unit": woolies_result["unit"]
                    }
                    woolies_total += woolies_result["price"]

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
