"""Test default tool configuration."""
import os
import pytest


def test_default_tools_list():
    """Test that DEFAULT_TOOLS contains expected tools."""
    # Import after clearing env var to test default behavior
    old_value = os.environ.get("AWS_DEBUG_MCP_TOOLS")
    if "AWS_DEBUG_MCP_TOOLS" in os.environ:
        del os.environ["AWS_DEBUG_MCP_TOOLS"]

    try:
        # Import dynamically to ensure we get fresh values
        import importlib
        import sys
        if "aws_debug_mcp.server" in sys.modules:
            del sys.modules["aws_debug_mcp.server"]

        from aws_debug_mcp.server import DEFAULT_TOOLS, configured_tools

        # Verify DEFAULT_TOOLS contains expected tools
        expected_tools = {
            # CloudWatch Logs (5)
            "describe_log_groups",
            "analyze_log_group",
            "execute_log_insights_query",
            "get_logs_insight_query_results",
            "cancel_logs_insight_query",
            # Step Functions (5)
            "list_state_machines",
            "get_state_machine_definition",
            "list_step_function_executions",
            "get_step_function_execution_details",
            "search_step_function_executions",
        }

        # Parse DEFAULT_TOOLS string
        default_tool_set = set(tool.strip() for tool in DEFAULT_TOOLS.split(",") if tool.strip())

        assert default_tool_set == expected_tools, (
            f"DEFAULT_TOOLS mismatch.\n"
            f"Expected: {sorted(expected_tools)}\n"
            f"Got: {sorted(default_tool_set)}"
        )

        # Verify configured_tools matches DEFAULT_TOOLS when env var not set
        assert configured_tools == expected_tools

    finally:
        # Restore original env var
        if old_value is not None:
            os.environ["AWS_DEBUG_MCP_TOOLS"] = old_value
        elif "AWS_DEBUG_MCP_TOOLS" in os.environ:
            del os.environ["AWS_DEBUG_MCP_TOOLS"]


def test_all_tools_configuration():
    """Test that setting AWS_DEBUG_MCP_TOOLS to 'all' exposes all tools."""
    old_value = os.environ.get("AWS_DEBUG_MCP_TOOLS")
    os.environ["AWS_DEBUG_MCP_TOOLS"] = "all"

    try:
        import importlib
        import sys
        if "aws_debug_mcp.server" in sys.modules:
            del sys.modules["aws_debug_mcp.server"]

        from aws_debug_mcp.server import configured_tools

        # When set to "all", configured_tools should be None
        assert configured_tools is None

    finally:
        if old_value is not None:
            os.environ["AWS_DEBUG_MCP_TOOLS"] = old_value
        else:
            del os.environ["AWS_DEBUG_MCP_TOOLS"]


def test_custom_tools_configuration():
    """Test that custom tool list is parsed correctly."""
    old_value = os.environ.get("AWS_DEBUG_MCP_TOOLS")
    os.environ["AWS_DEBUG_MCP_TOOLS"] = "describe_log_groups,list_state_machines"

    try:
        import importlib
        import sys
        if "aws_debug_mcp.server" in sys.modules:
            del sys.modules["aws_debug_mcp.server"]

        from aws_debug_mcp.server import configured_tools

        expected = {"describe_log_groups", "list_state_machines"}
        assert configured_tools == expected

    finally:
        if old_value is not None:
            os.environ["AWS_DEBUG_MCP_TOOLS"] = old_value
        else:
            del os.environ["AWS_DEBUG_MCP_TOOLS"]
