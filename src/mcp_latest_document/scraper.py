from dotenv import load_dotenv
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import httpx
from markdownify import markdownify
load_dotenv()

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
    def findout_links(url: str) -> list[str]:
        """
        Finds all links in an HTML document.
        
        Args:
            url (str): The URL to fetch HTML content from
            
        Returns:
            list[str]: A list of links found in the HTML content
        """
        html = Scraper.get_html_sync(url)
        soup = BeautifulSoup(html, 'lxml')
        links = [link for link in soup.find_all("a")]
        base_url = Scraper.get_base_url(url)
        links_dict= {}
        for link in links:
            url = link.get("href")
            if not url:
                continue
            if url.startswith("/"):
                links_dict[link.text] = base_url + url
            else:
                links_dict[link.text] = url
        return links_dict

