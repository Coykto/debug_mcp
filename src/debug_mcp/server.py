"""Main MCP server for debugging distributed systems using boto3 and SDKs."""

from fastmcp import FastMCP

from .registry import registry

# Import registry modules to trigger tool registration
from .tools import (
    cloudwatch_registry,  # noqa: F401
    jira_registry,  # noqa: F401
    langsmith_registry,  # noqa: F401
    stepfunctions_registry,  # noqa: F401
)

# Initialize MCP server
mcp = FastMCP("debug-mcp")


@mcp.tool()
async def debug(tool: str = "list", arguments: str = "{}") -> dict:
    """Execute debugging tools or discover available ones.

    Categories: cloudwatch, stepfunctions, langsmith, jira

    Args:
        tool: Tool name to execute, or "list" / "list:<category>" for discovery
        arguments: JSON string of tool arguments
    """
    import json

    # Validate and parse arguments
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError as e:
        return {"error": True, "message": f"Invalid JSON: {e}"}

    # Discovery mode
    if tool == "list":
        return {"categories": registry.list_categories()}

    if tool.startswith("list:"):
        category = tool.split(":", 1)[1]
        tools = registry.list_tools(category)
        if not tools:
            return {
                "error": True,
                "message": f"Unknown category: {category}",
                "available_categories": list(registry._categories.keys()),
            }
        return {"tools": tools}

    # Execution mode
    try:
        result = await registry.execute(tool, args)
        return result
    except ValueError as e:
        return {"error": True, "message": str(e)}
    except Exception as e:
        return {"error": True, "message": f"Execution failed: {e}"}
