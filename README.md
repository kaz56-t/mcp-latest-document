# MCP Latest Document

A Model Context Protocol server that provides access to the latest documentation for various services.

## Requirements
1. Python 3.10 or higher

## Installation

### Step 1. Install uv
- MacOS/Linux:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
- Windows:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 2. Install the package
You can install the package directly using pip:
```bash
pip install mcp-latest-document
```

Or use uv:
```bash
uv pip install mcp-latest-document
```

## Configuration

### Configure for Claude Desktop
1. Download [Claude Desktop](https://claude.ai/download).
2. Launch Claude and go to Settings > Developer > Edit Config.
3. Modify `claude_desktop_config.json` with:

```json
{
    "mcpServers": {
        "latest_document": {
            "command": "uv",
            "args": [
                "--directory",
                "E:/src/agent/mcp-latest-document",
                "run",
                "src/mcp_latest_document/server.py"
            ],
            "env": {
                "TOOLS": "React, ChakraUI",
                "URLS":"https://api.openai.com/v1"
            }
        }
    }
}
```

4. Relaunch Claude Desktop.

### For others
```json
{
  "mcpServers": {
    "latest_document": {
      "command": "uvx",
      "args": [
        "mcp_latest_document"
      ],
      "env": {
        "TOOLS": "React, ChakraUI",
        "URLS":"https://api.openai.com/v1"
      }
    }
  }
}
```

## Available Tools

- `get_html_content` - Get the HTML content as markdown of a URL
  - Required arguments:
    - `url` (string): The URL to fetch content from

- `find_link_by_keyword` - Find URL links by keyword
  - Required arguments:
    - `keyword` (string): Keyword to search for in links and URLs

## Available Resources

- `links://` - Get all available document links


## Debugging

You can use the MCP inspector to debug the server:

```bash
uv run mcp dev ./src/mcp_latest_document/server.py
```

## For developer
## How to test
1. `uv run mcp dev src/mcp_latest_document/server.py`

### How to deploy (To be automated)
1. `uv run -m build`
2. `uv run -m twine upload dist/*`

## Contributing

We encourage contributions to help expand and improve mcp-latest-document. Whether you want to add new documentation sources, enhance existing functionality, or improve documentation, your input is valuable.

Pull requests are welcome! Feel free to contribute new ideas, bug fixes, or enhancements.

## License

mcp-latest-document is licensed under the MIT License. This means you are free to use, modify, and distribute the software, subject to the terms and conditions of the MIT License.
