import logging
import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, List
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("brofessor")


@dataclass
class WebSearchResult:
    """Represents a clean web search result item."""
    title: str
    snippet: str
    url: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "snippet": self.snippet,
            "url": self.url,
        }


class WebSearchService:
    """
    Zero-config external web search service using DuckDuckGo HTML endpoint.
    No API key required; operates as an external search tool for Corrective RAG.
    """

    SEARCH_URL = "https://html.duckduckgo.com/html/"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )

    @classmethod
    def search(cls, query: str, max_results: int = 5) -> List[WebSearchResult]:
        """
        Executes web search for query and returns parsed titles, snippets, and URLs.
        """
        if not query or not query.strip():
            return []

        clean_query = query.strip()
        headers = {
            "User-Agent": cls.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        data = {"q": clean_query}

        try:
            resp = requests.post(cls.SEARCH_URL, data=data, headers=headers, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"DuckDuckGo search returned status {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            results: List[WebSearchResult] = []

            # DuckDuckGo HTML format: results are in div.result or div.web-result
            items = soup.find_all("div", class_=lambda c: c and ("result" in c.split() or "web-result" in c.split()))
            for item in items:
                title_elem = item.find("a", class_="result__a")
                snippet_elem = item.find("a", class_="result__snippet")

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                raw_href = title_elem.get("href", "")

                # DuckDuckGo redirect wrapper: /l/?kh=-1&uddg=https%3A%2F%2F...
                url = raw_href
                if "uddg=" in raw_href:
                    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_href).query)
                    if "uddg" in parsed_qs:
                        url = parsed_qs["uddg"][0]

                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if title and url and url.startswith("http"):
                    results.append(WebSearchResult(title=title, snippet=snippet, url=url))

                if len(results) >= max_results:
                    break

            return results

        except Exception as e:
            logger.error(f"Error during DuckDuckGo web search for '{query}': {e}")
            return []
