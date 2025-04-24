import os
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx
from markdownify import markdownify
from .scraper import Scraper
load_dotenv()

URLS = os.environ.get("URLS", "https://react.dev/reference/react-dom").split(",")

# Create an MCP server
mcp = FastMCP("Provide infroamtion based on specified Document")

# Add an addition tool
@mcp.tool()
def get_html_content(url: str) -> str:
    """Get the HTML content as markdown of a URL"""
    html = Scraper.get_html_sync(url)
    return Scraper.convert_to_markdown(html)


@mcp.tool()
def find_link_by_keyword(keyword: str) -> list[str]:
    """Find URL links by keyword"""
    matched_links = {}
    for url in URLS:
        links = Scraper.findout_links(url)
        for link, url in links.items():
            if keyword in link or keyword in url:
                matched_links[link] = url
    return matched_links


@mcp.resource("links://")
def get_documents() -> str:
    """Get the links of the documents"""
    all_links = {}
    for url in URLS:
        links = Scraper.findout_links(url)
        all_links.update(links)
    return all_links



if __name__ == "__main__":
    # Initialize and run the server for local claude
    mcp.run(transport='stdio')