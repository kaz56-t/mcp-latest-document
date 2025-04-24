import pytest
import asyncio
import httpx
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from src.mcp_latest_document.server import Scraper


@pytest.fixture
def sample_html():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
    </head>
    <body>
        <h1>Hello World</h1>
        <p>This is a <strong>test</strong> paragraph.</p>
        <a href="/relative-link">Relative Link</a>
        <a href="https://example.com/absolute-link">Absolute Link</a>
        <a>Link without href</a>
    </body>
    </html>
    """


@pytest.mark.asyncio
async def test_get_html():
    # Mock the httpx.AsyncClient to avoid actual HTTP requests
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = MagicMock()
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await Scraper.get_html("https://example.com")
        
        assert result == "<html>Test content</html>"
        mock_client.return_value.__aenter__.return_value.get.assert_called_once_with(
            "https://example.com", timeout=30
        )


def test_get_html_sync():
    # Mock the httpx.Client to avoid actual HTTP requests
    with patch('httpx.Client') as mock_client:
        mock_response = MagicMock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = MagicMock()
        
        mock_client.return_value.__enter__.return_value.get.return_value = mock_response
        
        result = Scraper.get_html_sync("https://example.com")
        
        assert result == "<html>Test content</html>"
        mock_client.return_value.__enter__.return_value.get.assert_called_once_with(
            "https://example.com", timeout=30
        )


def test_convert_to_markdown():
    html = "<h1>Title</h1><p>This is <strong>bold</strong> text.</p>"
    expected_markdown = "Title\n=====\n\nThis is **bold** text."
    
    result = Scraper.convert_to_markdown(html)
    
    assert result == expected_markdown


def test_get_base_url():
    test_cases = [
        ("https://example.com/path/to/page", "https://example.com"),
        ("http://test.org/index.html?param=value", "http://test.org"),
        ("https://subdomain.example.com/path", "https://subdomain.example.com"),
    ]
    
    for url, expected in test_cases:
        result = Scraper.get_base_url(url)
        assert result == expected


def test_findout_links(sample_html):
    # Mock the get_html_sync method to return our sample HTML
    with patch('src.mcp_latest_document.scraper.Scraper.get_html_sync') as mock_get_html:
        mock_get_html.return_value = sample_html
        
        # Mock BeautifulSoup to use our sample HTML
        with patch('src.mcp_latest_document.scraper.BeautifulSoup') as mock_bs:
            soup = BeautifulSoup(sample_html, 'lxml')
            mock_bs.return_value = soup
            
            result = Scraper.findout_links("https://example.com")
            
            assert isinstance(result, dict)
            assert "Relative Link" in result
            assert result["Relative Link"] == "https://example.com/relative-link"
            assert "Absolute Link" in result
            assert result["Absolute Link"] == "https://example.com/absolute-link"
            assert len(result) == 2  # Should not include the link without href


def test_findout_links_error_handling():
    # Test error handling when get_html_sync raises an exception
    with patch('src.mcp_latest_document.scraper.Scraper.get_html_sync') as mock_get_html:
        mock_get_html.side_effect = httpx.HTTPError("Error fetching URL")
        
        with pytest.raises(httpx.HTTPError):
            Scraper.findout_links("https://example.com")


@pytest.mark.asyncio
async def test_get_html_error_handling():
    # Test error handling when the HTTP request fails
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("HTTP Error")
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        with pytest.raises(httpx.HTTPError):
            await Scraper.get_html("https://example.com")