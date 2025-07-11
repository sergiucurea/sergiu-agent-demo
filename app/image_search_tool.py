from langchain.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import requests
import re

class ImageSearchInput(BaseModel):
    query: str = Field(..., description="The search query for the image")
    max_results: int = Field(3, description="Maximum number of images to return")

class ImageSearchTool(BaseTool):
    name: str = "image_search"
    description: str = "Searches for images related to a query using DuckDuckGo and returns image URLs."
    args_schema: Type[BaseModel] = ImageSearchInput

    def _run(self, query: str, max_results: int = 3):
        url = "https://duckduckgo.com/"
        params = {"q": query}
        res = requests.post(url, data=params)
        search_obj = res.text

        vqd_match = re.search(r'vqd=([\d-]+)\&', search_obj)
        if not vqd_match:
            return ""
        vqd = vqd_match.group(1)

        headers = {"User-Agent": "Mozilla/5.0"}
        image_url = f"https://duckduckgo.com/i.js"
        params = {"q": query, "vqd": vqd, "o": "json"}
        res = requests.get(image_url, headers=headers, params=params)

        # Robust: check for valid JSON response
        if res.status_code != 200 or not res.text.strip().startswith("{"):
            return ""
        try:
            data = res.json()
        except Exception:
            return ""
        results = [img["image"] for img in data.get("results", [])]
        if not results:
            return ""
        return results[0]

    async def _arun(self, query: str, max_results: int = 3):
        raise NotImplementedError("Async not supported for this tool.") 