import math
import os
import re
from collections import Counter, defaultdict
from enum import Enum
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from markdownify import markdownify
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

load_dotenv()


class ToolURLS(Enum):
    # FrontEnd
    react = "https://react.dev/reference/react-dom"
    reactnative = "https://reactnative.dev/docs/components-and-apis"
    chakraui = "https://chakra-ui.com/docs/components/concepts/overview"
    # Backend
    python = "https://docs.python.org/3/"
    go = "https://go.dev/doc/"


class Page(BaseModel):
    title: str
    url: str
    content: Optional[str] = None


def setup_urls() -> list[str]:
    env_urls = os.environ.get("URLS", "").split(",")
    tools = os.environ.get("TOOLS", "React").split(",")
    tool_urls = []
    for tool in tools:
        tool = tool.lower().replace("_", "").replace(".", "").strip()
        if tool in ToolURLS.__members__:
            tool_urls.append(ToolURLS[tool].value)
    return tool_urls + env_urls


URLS = setup_urls()


class Scraper:
    @staticmethod
    async def get_html(url: str, timeout: int = 30) -> str:
        """
        Fetches HTML content from a specified URL using httpx.

        Args:
            url (str): The URL to fetch HTML content from
            timeout (int, optional): Request timeout in seconds. Defaults to 30.

        Returns:
            str: The HTML content as a string

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            return response.text

    @staticmethod
    def get_html_sync(url: str, timeout: int = 30) -> str:
        """
        Synchronous version of get_html function.
        Fetches HTML content from a specified URL using httpx.

        Args:
            url (str): The URL to fetch HTML content from
            timeout (int, optional): Request timeout in seconds. Defaults to 30.

        Returns:
            str: The HTML content as a string

        Raises:
            httpx.HTTPError: If the HTTP request fails
        """
        with httpx.Client() as client:
            response = client.get(url, timeout=timeout)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            return response.text

    @staticmethod
    def convert_to_markdown(html: str) -> str:
        """
        Converts HTML to Markdown using markdownify library.

        Args:
            html (str): The HTML content to convert

        Returns:
            str: The Markdown content as a string
        """
        return markdownify(html)

    @staticmethod
    def get_base_url(url: str) -> str:
        """
        Extracts the base URL from a given URL.

        Args:
            url (str): The full URL

        Returns:
            str: The base URL (scheme + netloc)
        """
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url

    @staticmethod
    def findout_links(url: str) -> dict[str, str]:
        """
        Finds all links in an HTML document.

        Args:
            url (str): The URL to fetch HTML content from

        Returns:
            list[str]: A list of links found in the HTML content
        """
        html = Scraper.get_html_sync(url)
        soup = BeautifulSoup(html, "lxml")
        links = [link for link in soup.find_all("a")]
        base_url = Scraper.get_base_url(url)
        links_dict = {}
        for link in links:
            url = link.get("href")
            if not url:
                continue
            if url.startswith("/"):
                links_dict[link.text] = base_url + url
            else:
                links_dict[link.text] = url
        return links_dict


class DocumentSearchEngine:
    def __init__(self):
        """Initialize an empty search engine.

        Creates an empty search engine with no documents and an empty inverted index.
        """
        self.documents = {}
        self.inverted_index = defaultdict(list)
        self.document_lengths = {}
        self.idf = {}

    def set_documents(self, pages: List[Page]):
        """Set documents from a list of Page objects.

        Args:
            pages: List of Page objects containing title, url, and optional content.

        Returns:
            None

        Note:
            This method will not update documents if they already exist.
        """
        # Skip if documents already exist
        if len(self.documents) > 0:
            return

        # Store documents using URL as the document ID
        for page in pages:
            # Use title as the indexable content if no content is provided
            content = page.content if page.content is not None else ""
            self.documents[page.url] = {"title": page.title, "content": content}

        # Build the index with the new documents
        self.build_index()

    def preprocess_text(self, text: str) -> List[str]:
        """Clean and tokenize text into words.

        Args:
            text: The input text to be processed.

        Returns:
            List[str]: A list of tokenized words.

        Note:
            Words shorter than 2 characters are filtered out.
        """
        if not text:
            return []

        # Convert to lowercase and split on non-alphanumeric characters
        words = re.findall(r"\w+", text.lower())
        # Filter out very short words (optional)
        words = [word for word in words if len(word) > 1]
        return words

    def build_index(self) -> None:
        """Build the inverted index and calculate IDF values.

        Processes all documents to create an inverted index and calculate
        inverse document frequency (IDF) values for each term.

        Returns:
            None
        """
        # Count document frequency for each term
        doc_freq = defaultdict(int)

        # Process each document
        for doc_id, doc_data in self.documents.items():
            content = doc_data["content"] or ""  # Use empty string if content is None

            # Add title to indexable content to give it more weight
            indexable_text = f"{doc_data['title']} {content}"

            # Tokenize and count terms in the document
            terms = self.preprocess_text(indexable_text)
            term_freq = Counter(terms)

            # Skip documents with no terms
            if not terms:
                continue

            # Store document length (for normalization)
            self.document_lengths[doc_id] = math.sqrt(sum(tf * tf for tf in term_freq.values()))

            # Update the inverted index with term frequencies
            for term, freq in term_freq.items():
                self.inverted_index[term].append((doc_id, freq))
                doc_freq[term] += 1

        # Calculate IDF for each term
        num_docs = max(1, len(self.documents))  # Avoid division by zero
        self.idf = {term: math.log(num_docs / freq) for term, freq in doc_freq.items()}

    def search(self, query, top_k=5) -> list[tuple[str, float]]:
        """Search for documents matching the query.

        Args:
            query: Search query (English).
            top_k: Number of top results to return.

        Returns:
            list[tuple[str, float]]: List of (document_id, score) tuples.
        """
        query_terms = self.preprocess_text(query)

        # If no valid terms in query, return empty results
        if not query_terms:
            return []

        # Count query terms
        query_term_freq = Counter(query_terms)

        # Calculate query vector length for normalization
        query_length = math.sqrt(sum((tf * self.idf.get(term, 0)) ** 2 for term, tf in query_term_freq.items()))

        # Initialize scores
        scores = defaultdict(float)

        # Calculate TF-IDF scores using cosine similarity
        for term, query_tf in query_term_freq.items():
            if term in self.inverted_index:
                query_weight = query_tf * self.idf.get(term, 0)

                # For each document containing this term
                for doc_id, doc_tf in self.inverted_index[term]:
                    doc_weight = doc_tf
                    scores[doc_id] += query_weight * doc_weight

        # Normalize scores by document length
        for doc_id in scores:
            if query_length > 0 and self.document_lengths.get(doc_id, 0) > 0:
                scores[doc_id] = scores[doc_id] / (query_length * self.document_lengths[doc_id])

        # Return top k results
        results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return results

    def get_search_results_with_metadata(self, query, top_k=5) -> list[Page]:
        """Get search results with document metadata and snippets.

        Args:
            query: Search query.
            top_k: Number of top results to return.

        Returns:
            list[dict[str, str | float]]: List of dictionaries with document metadata and snippets.
            Each dictionary contains 'url', 'title', and optionally 'content'.
        """
        search_results = self.search(query, top_k)
        results_with_metadata = []

        for doc_id, _ in search_results:
            content = self.documents[doc_id].get("content", "")
            result = {
                "url": doc_id,
                "title": self.documents[doc_id]["title"],
            }
            if content:
                result["content"] = content
            results_with_metadata.append(Page(**result))
        return results_with_metadata


search_engine = DocumentSearchEngine()

# Create an MCP server
mcp = FastMCP("Provide infroamtion based on specified Document")


# Add an addition tool
@mcp.tool()
def get_html_content(url: str) -> str:
    """Get the HTML content as markdown of a URL"""
    html = Scraper.get_html_sync(url)
    return Scraper.convert_to_markdown(html)


@mcp.tool()
def find_link_by_keyword(
    keyword: str,  # The keyword in English to search for in link text or URLs
) -> list[str]:
    """Find URL links by keyword"""
    all_pages = []
    for url in URLS:
        links = Scraper.findout_links(url)
        for link, url in links.items():
            all_pages.append(Page(title=link, url=url))
    search_engine.set_documents(all_pages)
    return search_engine.get_search_results_with_metadata(keyword)


@mcp.tool()
def get_document_links() -> str:
    """Get the page titles of the documents"""
    all_links = {}
    for url in URLS:
        links = Scraper.findout_links(url)
        all_links.update(links)
    return all_links


@mcp.resource("metadata://titles")
def get_document_links_resoure() -> list[Page]:
    """Get the page titles of the documents"""
    pages = []
    for url in URLS:
        links = Scraper.findout_links(url)
        for title, url in links.items():
            pages.append(Page(title=title, url=url))

    return pages


if __name__ == "__main__":
    # Initialize and run the server for local claude
    mcp.run(transport="stdio")
