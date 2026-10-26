from typing import Any
import requests
from bs4 import BeautifulSoup
from .base import BaseExtractor, ExtractionResult, ContentSegment


class ArticleExtractor(BaseExtractor):
    """Extractor for web articles and blog posts from URL."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def extract(self, source: Any) -> ExtractionResult:
        url = source.uri
        if not url:
            raise ValueError(f"Source '{source.name}' ({source.id}) has no URI specified.")

        headers = {
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except Exception as e:
            raise ConnectionError(f"Failed to fetch web article from {url}: {str(e)}") from e

        soup = BeautifulSoup(response.text, "html.parser")

        # Extract title
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title["content"].strip()
        elif soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        else:
            title = source.name or url

        # Remove boilerplates, scripts, navigations, footers
        for tag in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "svg", "iframe"]):
            tag.decompose()

        # Identify primary content container
        content_container = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", {"role": "main"})
            or soup.find("div", class_=lambda c: c and any(k in c.lower() for k in ["post-content", "article-content", "entry-content", "content-body"]))
            or soup.body
        )

        if not content_container:
            raise ValueError(f"Could not locate main article content in HTML for {url}")

        # Extract meaningful blocks (headings, paragraphs, lists)
        paragraphs = []
        for element in content_container.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "blockquote"]):
            text = element.get_text(separator=" ", strip=True)
            if len(text) > 10:  # Skip tiny noise snippets
                paragraphs.append(text)

        article_text = "\n\n".join(paragraphs)
        if not article_text.strip():
            # Fallback to text extraction of container
            article_text = content_container.get_text(separator="\n", strip=True)

        if not article_text.strip():
            raise ValueError(f"No readable article text could be extracted from {url}")

        meta_info = {
            "url": url,
            "final_url": response.url,
            "status_code": response.status_code,
            "content_type": response.headers.get("Content-Type", ""),
        }

        # Optional author & description metadata
        og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
        if og_desc and og_desc.get("content"):
            meta_info["description"] = og_desc["content"].strip()

        meta_author = soup.find("meta", attrs={"name": "author"})
        if meta_author and meta_author.get("content"):
            meta_info["author"] = meta_author["content"].strip()

        return ExtractionResult(
            title=title,
            text=article_text,
            metadata=meta_info,
            segments=[
                ContentSegment(
                    text=article_text,
                    metadata={"url": url},
                )
            ],
        )
