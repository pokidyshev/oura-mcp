# Comprehensive Guide: Building & Publishing MCP Servers

**Using Python, FastMCP, and uv**

This guide outlines the standardized process for creating a Model Context Protocol (MCP) server using Python, managing it with uv, and publishing it to PyPI for easy consumption via uvx.

---

## Phase 1: Project Initialization

### Install uv (if not present)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Initialize the Project

Create a standard Python project structure:

```bash
uv init my-mcp-server
cd my-mcp-server
```

### Add Dependencies

Install the official MCP SDK with CLI tools (which includes FastMCP):

```bash
uv add "mcp[cli]"
```

---

## Phase 2: Server Implementation

Create the core server file. This uses FastMCP for minimal boilerplate.

**File:** `src/my_mcp_server/server.py` (or just `server.py` in root for simple scripts)

```python
from mcp.server.fastmcp import FastMCP

# Initialize the server
mcp = FastMCP("My Demo Server")

# Tool: Capabilities exposed to the LLM (e.g., calculations, API fetches)
@mcp.tool()
def calculate_growth(start: int, rate: float, years: int) -> str:
    """Calculates compound interest growth."""
    final_amount = start * ((1 + rate) ** years)
    return f"After {years} years, the amount will be {final_amount:.2f}"

# Resource: Read-only data exposed to the LLM
@mcp.resource("config://app-settings")
def get_settings() -> str:
    """Returns application settings."""
    return "Theme: Dark, Notifications: On"

# Entry point for execution
def main():
    mcp.run()

if __name__ == "__main__":
    main()
```

---

## Phase 3: Configuration for PyPI

To allow users to run your server via `uvx` (e.g., `uvx my-mcp-server`), you must configure the entry point in `pyproject.toml`.

**Edit:** `pyproject.toml`

```toml
[project]
name = "my-mcp-server"
version = "0.1.0"
description = "A demo MCP server"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.0.0",
]

# CRITICAL: This allows 'uvx my-mcp-server' to work
[project.scripts]
my-mcp-server = "my_mcp_server.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

---

## Phase 4: Local Testing

Before publishing, verify the server works using the MCP Inspector.

```bash
# Run the Inspector against your server file
uv run mcp dev src/my_mcp_server/server.py
```

Access the web interface at the URL provided (usually `localhost:5173`) to interact with your tools.

---

## Phase 5: Publishing to PyPI

### Build the Package

```bash
uv build
```

### Publish

_(Requires a PyPI account and token)_

```bash
uv publish
```

---

## Phase 6: Consumption (Client Config)

Once published, any user can run your server without manually installing dependencies by using `uvx` in their client configuration.

**Example:** `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-demo-server": {
      "command": "uvx",
      "args": ["my-mcp-server"]
    }
  }
}
```
