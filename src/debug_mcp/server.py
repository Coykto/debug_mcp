"""Main MCP server for debugging distributed systems using boto3 and SDKs."""

import os

from fastmcp import FastMCP

# Initialize MCP server
mcp = FastMCP("debug-mcp")


def is_aws_configured() -> bool:
    """Check if AWS credentials are configured (region is required)."""
    return bool(os.getenv("AWS_REGION"))


def is_jira_configured() -> bool:
    """Check if Jira credentials are configured."""
    return bool(os.getenv("JIRA_HOST") and os.getenv("JIRA_EMAIL") and os.getenv("JIRA_API_TOKEN"))


def is_langsmith_configured() -> bool:
    """Check if LangSmith credentials are configured."""
    return bool(os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY"))


def _register_with_error_handling(name: str, register_fn: callable) -> None:
    """Register tools with error handling for initialization failures."""
    try:
        register_fn(mcp)
    except Exception as e:
        import sys

        print(f"Warning: Failed to initialize {name} tools: {e}", file=sys.stderr)


# Conditionally register tools based on configuration
if is_aws_configured():
    from .tools import cloudwatch_registry, stepfunctions_registry

    _register_with_error_handling("CloudWatch", cloudwatch_registry.register_tools)
    _register_with_error_handling("Step Functions", stepfunctions_registry.register_tools)

if is_jira_configured():
    from .tools import jira_registry

    _register_with_error_handling("Jira", jira_registry.register_tools)

if is_langsmith_configured():
    from .tools import langsmith_registry

    _register_with_error_handling("LangSmith", langsmith_registry.register_tools)
