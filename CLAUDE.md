# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Debug MCP is an open-source MCP (Model Context Protocol) server for debugging distributed systems (starting with AWS: Lambda, Step Functions, ECS) directly from Claude Code or any MCP client. The project aims to eliminate context switching between console interfaces by bringing debugging capabilities into AI coding assistants.

**Current Status**: Tool Discovery Gateway Complete - All 17 debugging tools available through a single `debug()` gateway tool. Token usage reduced by ~95% (13K → ~500 tokens). The server is installable locally via `uv run debug-mcp` and can be used in other projects via `uvx --from git+https://github.com/Coykto/debug_mcp`.

## Development Commands

### Environment Setup
```bash
# Install dependencies (when implemented)
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
The project uses a **Tool Discovery Gateway** pattern with category-based tool organization:

```
src/debug_mcp/
├── server.py              # Main MCP server with single debug() gateway tool
├── registry.py            # Central tool registry with @debug_tool decorator
├── __main__.py            # Entry point for CLI execution
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
- `server.py` - Exposes single `debug()` gateway tool using FastMCP
- `registry.py` - Central registry system with ToolRegistry class and @debug_tool decorator
- `*_registry.py` - Register tools for each category with schemas and handlers
- `*.py` (non-registry) - Actual tool implementations using boto3/SDKs
- `__main__.py` - CLI entry point that starts the FastMCP server

### Key Architectural Decisions

**Tool Discovery Gateway Pattern**: This server exposes a **single gateway tool** instead of 17 individual tools, reducing token usage by ~95% while maintaining full functionality.

**How It Works**:
1. Single `debug()` tool exposed to Claude with two modes: discovery and execution
2. Discovery mode (`tool="list"` or `tool="list:category"`) returns tool schemas
3. Execution mode (`tool="tool_name"`) routes to registered handlers
4. Central registry validates arguments and manages execution

**Token Optimization**:
- **Before**: 17 tools × ~750 tokens/tool = ~13,000 tokens
- **After**: 1 gateway tool × ~500 tokens = ~500 tokens
- **Savings**: ~95% reduction in context usage

**Why This Approach**:
- Dramatically reduced token usage for tool definitions
- Claude can discover tools on-demand instead of loading all upfront
- Easy to add new tools without increasing base context
- Category-based organization makes discovery intuitive
- Same safety and functionality as individual tools

**AWS Authentication**: CLI argument-based (`--aws-profile`, `--aws-region`) passed to `__main__.py`, which sets environment variables before tool execution. This approach works around a [known bug in Claude Code](https://github.com/anthropics/claude-code/issues/1254) where MCP `env` block variables aren't reliably passed to MCP servers.

**Available Tools (17 total across 4 categories)**:

**CloudWatch (4 tools):**
- `describe_log_groups`, `analyze_log_group`, `execute_log_insights_query`, `get_logs_insight_query_results`

**Step Functions (5 tools):**
- `list_state_machines`, `get_state_machine_definition`, `list_step_function_executions`, `get_step_function_execution_details`, `search_step_function_executions`

**LangSmith (6 tools):**
- `list_langsmith_projects`, `list_langsmith_runs`, `get_langsmith_run_details`, `search_langsmith_runs`, `search_run_content`, `get_run_field`

**Jira (2 tools):**
- `search_jira_tickets`, `get_jira_ticket`

**Read-Only Design**: All tools are read-only debugging operations. No CRUD or write operations to maintain safety and simplicity.

### Installation Model

Designed to be installable via uvx directly from GitHub:
```bash
uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp
```

This pattern mimics the "serena" MCP server, making it easy for teams to install without package registry publishing.

### Configuration in Claude Code

Users add the server via Claude Code CLI (recommended):
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-profile-name
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
        "--aws-region", "us-west-2",
        "--aws-profile", "your-profile-name"
      ]
    }
  }
}
```

**CLI Arguments** (passed to `__main__.py`):
- `--aws-profile` - AWS profile name (overrides AWS_PROFILE env var)
- `--aws-region` - AWS region (overrides AWS_REGION env var)
- `--jira-host`, `--jira-email`, `--jira-project`, `--jira-token` - Jira configuration (optional)

**Why CLI args instead of env vars?** Claude Code has a [known bug](https://github.com/anthropics/claude-code/issues/1254) where env variables aren't reliably passed to MCP servers. CLI args work around this by setting the env vars in `__main__.py` before tool execution.

## Implementation Phases

### Phase 1: Core Tools - ✅ COMPLETE
Implemented direct boto3/SDK tools for all major debugging workflows:
- CloudWatch Logs (4 tools) - Log querying and analysis
- Step Functions (5 tools) - Execution debugging and search
- LangSmith (6 tools) - LLM tracing and debugging
- Jira (2 tools) - Ticket search and retrieval

### Phase 2: Tool Discovery Gateway - ✅ COMPLETE
Optimized token usage by introducing gateway pattern:
- Single `debug()` tool instead of 17 individual tools
- Category-based discovery system
- ~95% reduction in token usage (13K → ~500 tokens)
- Central registry with @debug_tool decorator

### Phase 3: Future Enhancements
Potential improvements based on user feedback:
- Additional AWS services (ECS, Lambda direct integration)
- Cross-service correlation tools
- Enhanced error handling and retry logic
- Community documentation and examples

## Adding New Tools

Adding tools to the gateway is straightforward using the `@debug_tool()` decorator pattern.

### Steps to Add a New Tool

1. **Implement the tool logic** in the appropriate file (e.g., `tools/cloudwatch_logs.py`):
```python
async def my_new_tool(self, arg1: str, arg2: int) -> dict:
    """Implementation of the tool logic using boto3/SDK."""
    # Your implementation here
    return {"result": "data"}
```

2. **Create a Pydantic model** for arguments in the registry file (e.g., `tools/cloudwatch_registry.py`):
```python
class MyNewToolArgs(BaseModel):
    """Arguments for my_new_tool."""
    arg1: str = Field(description="Description of arg1")
    arg2: int = Field(default=100, description="Description of arg2")
```

3. **Register the tool** using the `@debug_tool` decorator:
```python
@debug_tool(
    name="my_new_tool",
    description="What this tool does for the user",
    category="cloudwatch",  # or "stepfunctions", "langsmith", "jira"
    parameters=[
        ToolParameter(
            name="arg1",
            type="string",
            description="Description of arg1",
            required=True
        ),
        ToolParameter(
            name="arg2",
            type="integer",
            description="Description of arg2",
            required=False,
            default=100
        ),
    ],
    arg_model=MyNewToolArgs,
)
async def my_new_tool(arg1: str, arg2: int = 100) -> dict:
    """Tool handler that calls the implementation."""
    if not is_aws_configured():
        return {"error": True, "message": "AWS credentials not configured"}

    tools = CloudWatchLogsTools()
    return await tools.my_new_tool(arg1, arg2)
```

4. **Test the tool** via the gateway:
```python
# Discovery
debug(tool="list:cloudwatch")  # Should show your new tool

# Execution
debug(tool="my_new_tool", arguments='{"arg1": "value", "arg2": 200}')
```

### Example: Adding a New Category

To add a completely new category (e.g., "ecs"):

1. Update `registry.py` to add the category:
```python
self._categories["ecs"] = "ECS tools for debugging container tasks"
```

2. Create `tools/ecs.py` with implementation
3. Create `tools/ecs_registry.py` with registrations
4. Import in `server.py`:
```python
from .tools import ecs_registry  # noqa: F401
```

The gateway automatically exposes all registered tools - no changes needed to `server.py`'s `debug()` function.

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