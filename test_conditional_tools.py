#!/usr/bin/env python
"""Test script to verify conditional tool exposure based on credentials."""

import asyncio
import os
import sys


def test_credential_checks():
    """Test the credential checking functions."""
    from src.debug_mcp.server import is_aws_configured, is_jira_configured, is_langsmith_configured

    print("=" * 60)
    print("CREDENTIAL CONFIGURATION CHECK")
    print("=" * 60)

    # Check AWS
    aws_region = os.getenv("AWS_REGION")
    aws_profile = os.getenv("AWS_PROFILE")
    aws_configured = is_aws_configured()

    print("\n[AWS]")
    print(f"  AWS_REGION: {aws_region or '(not set)'}")
    print(f"  AWS_PROFILE: {aws_profile or '(not set)'}")
    print(f"  is_aws_configured(): {aws_configured}")

    # Check LangSmith
    langchain_key = os.getenv("LANGCHAIN_API_KEY")
    langsmith_configured = is_langsmith_configured()

    print("\n[LangSmith]")
    print(f"  LANGCHAIN_API_KEY: {'***' if langchain_key else '(not set)'}")
    print(f"  AWS_REGION (for secrets): {aws_region or '(not set)'}")
    print(f"  is_langsmith_configured(): {langsmith_configured}")

    # Check Jira
    jira_host = os.getenv("JIRA_HOST")
    jira_email = os.getenv("JIRA_EMAIL")
    jira_token = os.getenv("JIRA_API_TOKEN")
    jira_configured = is_jira_configured()

    print("\n[Jira]")
    print(f"  JIRA_HOST: {jira_host or '(not set)'}")
    print(f"  JIRA_EMAIL: {jira_email or '(not set)'}")
    print(f"  JIRA_API_TOKEN: {'***' if jira_token else '(not set)'}")
    print(f"  is_jira_configured(): {jira_configured}")

    print("\n" + "=" * 60)
    return aws_configured, langsmith_configured, jira_configured


def test_tool_initialization():
    """Test that tool classes are initialized conditionally."""
    from src.debug_mcp.server import cw_logs, jira_debugger, sf_debugger

    print("TOOL CLASS INITIALIZATION")
    print("=" * 60)

    print("\n[AWS Tools]")
    print(f"  cw_logs (CloudWatchLogsTools): {type(cw_logs).__name__ if cw_logs else 'None (not initialized)'}")
    print(
        "  sf_debugger (StepFunctionsDebugger):"
        f" {type(sf_debugger).__name__ if sf_debugger else 'None (not initialized)'}"
    )

    print("\n[Jira Tools]")
    print(
        f"  jira_debugger (JiraDebugger): {type(jira_debugger).__name__ if jira_debugger else 'None (not initialized)'}"
    )

    print("\n" + "=" * 60)


async def test_tool_exposure():
    """Test which tools are actually exposed by the MCP server."""
    from src.debug_mcp.server import mcp

    print("MCP TOOL EXPOSURE")
    print("=" * 60)

    # Get all registered tools from the FastMCP server
    tools = await mcp.get_tools()

    # Group tools by category
    aws_cloudwatch_tools = [t for t in tools if any(kw in t.name for kw in ["log", "insight", "cloudwatch"])]
    aws_stepfunctions_tools = [t for t in tools if any(kw in t.name for kw in ["state_machine", "step_function"])]
    langsmith_tools = [t for t in tools if "langsmith" in t.name or "run" in t.name]
    jira_tools = [t for t in tools if "jira" in t.name]

    print(f"\nTotal tools registered: {len(tools)}")
    print(f"\n[AWS CloudWatch Tools] ({len(aws_cloudwatch_tools)} tools)")
    for tool in aws_cloudwatch_tools:
        print(f"  - {tool.name}")

    print(f"\n[AWS Step Functions Tools] ({len(aws_stepfunctions_tools)} tools)")
    for tool in aws_stepfunctions_tools:
        print(f"  - {tool.name}")

    print(f"\n[LangSmith Tools] ({len(langsmith_tools)} tools)")
    for tool in langsmith_tools:
        print(f"  - {tool.name}")

    print(f"\n[Jira Tools] ({len(jira_tools)} tools)")
    for tool in jira_tools:
        print(f"  - {tool.name}")

    print("\n" + "=" * 60)
    return len(tools)


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MCP SERVER CONDITIONAL TOOLS TEST" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    try:
        # Test 1: Check credentials
        aws_ok, langsmith_ok, jira_ok = test_credential_checks()

        # Test 2: Check tool initialization
        print("\n")
        test_tool_initialization()

        # Test 3: Check tool exposure
        print("\n")
        total_tools = await test_tool_exposure()

        # Summary
        print("\nSUMMARY")
        print("=" * 60)
        print(f"✓ AWS configured: {aws_ok}")
        print(f"✓ LangSmith configured: {langsmith_ok}")
        print(f"✓ Jira configured: {jira_ok}")
        print(f"✓ Total tools exposed: {total_tools}")
        print("\n")

        # Expected tools count
        expected = 0
        if aws_ok:
            expected += 10  # 5 CloudWatch + 5 Step Functions
        if langsmith_ok:
            expected += 6  # 6 LangSmith tools
        if jira_ok:
            expected += 2  # 2 Jira tools

        # Check if DEBUG_MCP_TOOLS is filtering
        debug_tools = os.getenv("DEBUG_MCP_TOOLS")
        if debug_tools and debug_tools.lower() != "all":
            print(f"Note: DEBUG_MCP_TOOLS is set to filter tools: {debug_tools}")
            print(f"      Expected {expected} tools without filtering")
        else:
            if total_tools == expected:
                print(f"✅ SUCCESS: All expected tools are exposed ({total_tools}/{expected})")
            else:
                print(f"⚠️  WARNING: Tool count mismatch. Expected {expected}, got {total_tools}")

        print("=" * 60)
        print("\n")

        return 0 if total_tools > 0 or not any([aws_ok, langsmith_ok, jira_ok]) else 1

    except Exception as e:
        print(f"\n❌ ERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
