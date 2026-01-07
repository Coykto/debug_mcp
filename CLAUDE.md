# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Debug MCP is an open-source MCP (Model Context Protocol) server for debugging distributed systems (starting with AWS: Lambda, Step Functions, ECS) directly from Claude Code or any MCP client. The project aims to eliminate context switching between console interfaces by bringing debugging capabilities into AI coding assistants.

**Current Status**: Direct Tool Registration - Tools are exposed directly to MCP clients (no gateway). Only tools for configured services are registered, allowing selective tool exposure based on provided credentials.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --dev

# Run the MCP server locally
uv run debug-mcp

# Run in development mode from project root
uv run python -m debug_mcp
```

### Testing
```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/debug_mcp

# Run specific test file
uv run pytest tests/test_cloudwatch_logs.py
```

### Code Quality
Pre-commit handles linting and formatting automatically. Setup:
```bash
uv sync --dev
uv run pre-commit install
```

### Manual Testing
```bash
# Test AWS client factory in Python REPL
uv run python
>>> from debug_mcp.aws.client_factory import AWSClientFactory
>>> from debug_mcp.tools.cloudwatch_logs import CloudWatchLogsTools
>>> factory = AWSClientFactory()
>>> tools = CloudWatchLogsTools(factory)
>>> tools.describe_log_groups(prefix="/aws/lambda/")
```

## Architecture

### Project Structure
The project uses **direct tool registration** with conditional loading based on credentials:

```
src/debug_mcp/
├── server.py              # Main MCP server, conditional tool registration
├── __main__.py            # Entry point, CLI argument parsing
└── tools/
    ├── cloudwatch_logs.py         # CloudWatch implementation (boto3)
    ├── cloudwatch_registry.py     # CloudWatch tool registration
    ├── stepfunctions.py           # Step Functions implementation (boto3)
    ├── stepfunctions_registry.py  # Step Functions tool registration
    ├── langsmith.py               # LangSmith implementation (SDK)
    ├── langsmith_registry.py      # LangSmith tool registration
    ├── jira.py                    # Jira implementation (SDK)
    └── jira_registry.py           # Jira tool registration
```

**Key Files**:
- `server.py` - Conditionally imports and registers tools based on configuration
- `__main__.py` - CLI entry point that parses args and sets environment variables
- `*_registry.py` - Each exports `register_tools(mcp: FastMCP)` function
- `*.py` (non-registry) - Actual tool implementations using boto3/SDKs

### Key Architectural Decisions

**Direct Tool Registration**: Tools are registered directly with FastMCP using `@mcp.tool()` decorator. Only tools for configured services are exposed.

**Conditional Registration**: Tools are only registered when their service is configured:
- **AWS tools** (CloudWatch, Step Functions): Registered when `AWS_REGION` is set
- **Jira tools**: Registered when `JIRA_HOST`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` are all set
- **LangSmith tools**: Registered when `LANGCHAIN_API_KEY` or `LANGSMITH_API_KEY` is set

**Why This Approach**:
- Users only see tools relevant to their configuration
- No need for discovery/gateway - tools are directly available
- Cleaner tool list in Claude Code
- Faster startup (no unused service initialization)

**AWS Authentication**: CLI argument-based (`--aws-profile`, `--aws-region`) passed to `__main__.py`, which sets environment variables before tool registration. This approach works around a [known bug in Claude Code](https://github.com/anthropics/claude-code/issues/1254) where MCP `env` block variables aren't reliably passed to MCP servers.

**Available Tools (17 total across 4 categories)**:

**CloudWatch (4 tools)** - requires `--aws-region`:
- `describe_log_groups`, `analyze_log_group`, `execute_log_insights_query`, `get_logs_insight_query_results`

**Step Functions (5 tools)** - requires `--aws-region`:
- `list_state_machines`, `get_state_machine_definition`, `list_step_function_executions`, `get_step_function_execution_details`, `search_step_function_executions`

**LangSmith (6 tools)** - requires `--langsmith-api-key`:
- `list_langsmith_projects`, `list_langsmith_runs`, `get_langsmith_run_details`, `search_langsmith_runs`, `search_run_content`, `get_run_field`

**Jira (2 tools)** - requires `--jira-host`, `--jira-email`, `--jira-token`:
- `search_jira_tickets`, `get_jira_ticket`

**Read-Only Design**: All tools are read-only debugging operations. No CRUD or write operations to maintain safety and simplicity.

### Installation Model

Designed to be installable via uvx directly from GitHub:
```bash
uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp
```

This pattern mimics the "serena" MCP server, making it easy for teams to install without package registry publishing.

### Configuration in Claude Code

Users add the server via Claude Code CLI (recommended). Configure only the services you need:

**AWS only:**
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-profile-name
```

**Jira only:**
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --jira-host yourcompany.atlassian.net \
    --jira-email your@email.com \
    --jira-token YOUR_API_TOKEN
```

**All services:**
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-profile-name \
    --jira-host yourcompany.atlassian.net \
    --jira-email your@email.com \
    --jira-token YOUR_API_TOKEN \
    --langsmith-api-key YOUR_LANGSMITH_KEY
```

Or manually in `.mcp.json`:
```json
{
  "mcpServers": {
    "debug-mcp": {
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/Coykto/debug_mcp",
        "debug-mcp",
        "--jira-host", "yourcompany.atlassian.net",
        "--jira-email", "your@email.com",
        "--jira-token", "YOUR_API_TOKEN"
      ]
    }
  }
}
```

**CLI Arguments** (passed to `__main__.py`):
- `--aws-region` - AWS region (enables AWS tools)
- `--aws-profile` - AWS profile name
- `--jira-host`, `--jira-email`, `--jira-project`, `--jira-token` - Jira configuration
- `--langsmith-api-key` - LangSmith API key (enables LangSmith tools)

**Why CLI args instead of env vars?** Claude Code has a [known bug](https://github.com/anthropics/claude-code/issues/1254) where env variables aren't reliably passed to MCP servers. CLI args work around this by setting the env vars in `__main__.py` before tool registration.

## Adding New Tools

Adding tools is straightforward using the `register_tools(mcp: FastMCP)` pattern.

### Steps to Add a New Tool

1. **Implement the tool logic** in the appropriate file (e.g., `tools/cloudwatch_logs.py`):
```python
async def my_new_tool(self, arg1: str, arg2: int) -> dict:
    """Implementation of the tool logic using boto3/SDK."""
    # Your implementation here
    return {"result": "data"}
```

2. **Register the tool** in the registry file (e.g., `tools/cloudwatch_registry.py`):
```python
def register_tools(mcp: FastMCP) -> None:
    """Register CloudWatch tools with the MCP server."""
    cw_logs = CloudWatchLogsTools(...)

    @mcp.tool()
    async def my_new_tool(arg1: str, arg2: int = 100) -> dict:
        """Tool description shown to users.

        Args:
            arg1: Description of arg1
            arg2: Description of arg2 (default: 100)
        """
        return await cw_logs.my_new_tool(arg1, arg2)
```

3. **Test the tool**:
```python
# Verify tool is registered
AWS_REGION=us-west-2 uv run python -c "
from debug_mcp.server import mcp
print(list(mcp._tool_manager._tools.keys()))
"
```

### Adding a New Service Category

To add a completely new category (e.g., "ecs"):

1. **Create implementation** `tools/ecs.py` with the service client
2. **Create registry** `tools/ecs_registry.py`:
```python
from fastmcp import FastMCP
from .ecs import ECSDebugger

def register_tools(mcp: FastMCP) -> None:
    """Register ECS tools with the MCP server."""
    debugger = ECSDebugger()

    @mcp.tool()
    async def list_ecs_services(...) -> dict:
        ...
```

3. **Add config check** in `server.py`:
```python
def is_ecs_configured() -> bool:
    """Check if ECS-specific config is available."""
    return bool(os.getenv("AWS_REGION"))  # or specific ECS config

if is_ecs_configured():
    from .tools import ecs_registry
    _register_with_error_handling("ECS", ecs_registry.register_tools)
```

4. **Add CLI args** in `__main__.py` if needed

## Dependencies

**Core**:
- `fastmcp>=0.2.0` - MCP server framework (provides tool decoration and server hosting)
- `pydantic>=2.0.0` - Data validation and argument models
- `boto3>=1.28.0` - AWS SDK for CloudWatch and Step Functions tools

**SDKs**:
- `langsmith>=0.1.0` - LangSmith SDK for LLM tracing
- `jira>=3.5.0` - Jira SDK for ticket management
- `sentence-transformers>=2.0.0` - Semantic search for LangSmith run content

**Development**:
- `pytest>=7.0.0` - Testing framework
- `pytest-cov>=4.0.0` - Coverage reporting
- `ruff>=0.1.0` - Linting and formatting
- `mypy>=1.0.0` - Static type checking
- `pre-commit>=3.0.0` - Git hooks for automated linting/formatting

**Package Management**: uv (modern Python package manager)

## Testing Strategy

### Unit Tests
Mock boto3 clients to test tool logic without AWS API calls. Focus on:
- Time range parsing edge cases
- Response formatting
- Error handling

### Integration Tests (Manual)
Run against real AWS account (dev/test) to verify:
- Actual API responses match expectations
- Authentication works with profiles
- Time ranges produce correct results

Test locally before pushing by configuring in Claude Code with local path:
```json
{
  "mcpServers": {
    "debug-mcp-local": {
      "command": "uv",
      "args": ["run", "debug-mcp"],
      "cwd": "/full/path/to/debug_mcp"
    }
  }
}
```

## Important Context

### Related Files
- **README.md** - Complete user-facing documentation with installation, configuration, available tools, and development guide

### Design Philosophy
- **Tight scope**: Start minimal, expand based on real usage
- **Team-friendly**: Easy installation, environment-based auth
- **Debugging-focused**: Read-only tools, no infrastructure changes
- **Learning project**: Also serves to deepen MCP development expertise

### AWS Credentials
Never commit credentials. Always use:
- AWS profiles (`~/.aws/credentials`)
- Environment variables (`AWS_PROFILE`, `AWS_REGION`)
- IAM roles when running in AWS environments

### Common Pitfalls
- CloudWatch Insights queries are asynchronous - must poll `get_query_results()` until status is "Complete"
- AWS timestamps are in milliseconds, not seconds
- Log group names must be exact matches (case-sensitive)
- Time parsing requires careful handling of timezones (default to UTC)
- Don't run ruff or any other linter on your own. We have pre-commit. It will handle that.
