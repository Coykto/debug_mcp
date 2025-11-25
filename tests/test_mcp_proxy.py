"""Tests for MCP proxy content extraction."""
import pytest
from aws_debug_mcp.mcp_proxy import MCPProxy


class MockContentBlock:
    """Mock MCP content block with text attribute."""
    def __init__(self, text):
        self.text = text


def test_extract_content_from_dict_content_block():
    """Test extracting JSON from dict-like content block (actual MCP format)."""
    proxy = MCPProxy()

    # This is the format we see in the error - list with dict containing 'text' key
    content = [{'type': 'text', 'text': '{"queryId": "test123", "status": "Complete"}'}]
    result = proxy._extract_content(content)

    assert isinstance(result, dict)
    assert result == {"queryId": "test123", "status": "Complete"}


def test_extract_content_from_object_with_text_attr():
    """Test extracting JSON from object with text attribute."""
    proxy = MCPProxy()

    content = [MockContentBlock('{"key": "value", "count": 42}')]
    result = proxy._extract_content(content)

    assert isinstance(result, dict)
    assert result == {"key": "value", "count": 42}


def test_extract_content_plain_text():
    """Test extracting plain text (not JSON)."""
    proxy = MCPProxy()

    content = [{'type': 'text', 'text': 'Plain text response'}]
    result = proxy._extract_content(content)

    assert isinstance(result, str)
    assert result == 'Plain text response'


def test_extract_content_empty_list():
    """Test handling empty content list."""
    proxy = MCPProxy()

    result = proxy._extract_content([])

    assert isinstance(result, dict)
    assert result == {}


def test_extract_content_malformed_json():
    """Test handling malformed JSON - should return as string."""
    proxy = MCPProxy()

    content = [{'type': 'text', 'text': '{invalid json}'}]
    result = proxy._extract_content(content)

    assert isinstance(result, str)
    assert result == '{invalid json}'


def test_extract_content_error_response():
    """Test extracting error response (as seen in the user's error)."""
    proxy = MCPProxy()

    error_text = '''{
  "queryId": "",
  "status": "Error",
  "message": "Error executing CloudWatch Logs Insights query",
  "results": []
}'''

    content = [{'type': 'text', 'text': error_text}]
    result = proxy._extract_content(content)

    assert isinstance(result, dict)
    assert result["status"] == "Error"
    assert result["queryId"] == ""
    assert result["results"] == []
