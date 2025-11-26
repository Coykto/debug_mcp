# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Debug MCP is an open-source MCP (Model Context Protocol) server for debugging distributed systems (starting with AWS: Lambda, Step Functions, ECS) directly from Claude Code or any MCP client. The project aims to eliminate context switching between console interfaces by bringing debugging capabilities into AI coding assistants.

**Current Status**: Phase 1 MVP Complete - CloudWatch Logs tools are implemented and working. The server is installable locally via `uv run debug-mcp` and can be used in other projects via `uvx --from git+https://github.com/Coykto/debug_mcp`.

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
The project follows src-layout with a simple proxy design:

```
src/debug_mcp/
├── server.py              # Main MCP server with proxied tool registrations
├── mcp_proxy.py           # MCP proxy client for connecting to AWS MCPs
├── __main__.py            # Entry point for CLI execution
└── tools/                 # Tool implementations (stepfunctions.py, langsmith.py)
```

**Key Files**:
- `server.py` - Defines which tools to expose using FastMCP decorators. Each tool forwards to the upstream AWS MCP.
- `mcp_proxy.py` - Manages subprocess connections to AWS MCP servers (CloudWatch, Step Functions, etc.) and forwards tool calls.
- `__main__.py` - CLI entry point that starts the FastMCP server.

### Key Architectural Decisions

**MCP Proxy Pattern**: This server acts as a **proxy/gateway** to AWS MCP servers, exposing only the tools you need while hiding the rest. It does NOT reimplement AWS functionality - it wraps existing AWS MCP servers.

**How It Works**:
1. Spawns AWS MCP servers (e.g., awslabs.cloudwatch-mcp-server) as subprocesses
2. Uses MCP client SDK to communicate with upstream servers
3. Exposes only selected tools through proxied calls
4. Hides all other tools from the client

**Why This Approach**:
- No need to reimplement AWS APIs with boto3
- AWS maintains the underlying functionality
- Easy to add/remove tools by simply adding/removing proxy functions
- Keeps tool list minimal and focused on debugging workflows

**AWS Authentication**: Environment-based using `AWS_PROFILE` and `AWS_REGION` variables passed through to upstream AWS MCP servers.

**Tool Filtering**: 26 tools available from three AWS MCPs. By default, exposes 10 core debugging tools (CloudWatch Logs + Step Functions). Filter via `DEBUG_MCP_TOOLS` environment variable.

**CloudWatch (11 tools):**
- Logs: `describe_log_groups`, `analyze_log_group`, `execute_log_insights_query`, `get_logs_insight_query_results`, `cancel_logs_insight_query`
- Metrics: `get_metric_data`, `get_metric_metadata`, `get_recommended_metric_alarms`, `analyze_metric`
- Alarms: `get_active_alarms`, `get_alarm_history`

**ECS (10 tools):**
- Deployment: `containerize_app`, `build_and_push_image_to_ecr`, `validate_ecs_express_mode_prerequisites`, `wait_for_service_ready`, `delete_app`
- Troubleshooting: `ecs_troubleshooting_tool`, `ecs_resource_management`
- Documentation: `aws_knowledge_aws___search_documentation`, `aws_knowledge_aws___read_documentation`, `aws_knowledge_aws___recommend`

**Step Functions (Dynamic):**
- Tools generated from your state machines (configure via `STATE_MACHINE_LIST` or `STATE_MACHINE_PREFIX`)

**Read-Only Design**: All tools are read-only debugging operations. No CRUD or write operations to maintain safety and simplicity.

### Installation Model

Designed to be installable via uvx directly from GitHub:
```bash
uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp
```

This pattern mimics the "serena" MCP server, making it easy for teams to install without package registry publishing.

### Configuration in Claude Code

Users add the server to their MCP configuration with optional tool filtering:
```json
{
  "mcpServers": {
    "debug-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/Coykto/debug_mcp", "debug-mcp"],
      "env": {
        "AWS_PROFILE": "your-profile-name",
        "AWS_REGION": "us-east-1",
        "DEBUG_MCP_TOOLS": "describe_log_groups,execute_log_insights_query"
      }
    }
  }
}
```

**Environment Variables:**
- `AWS_PROFILE` - AWS profile name
- `AWS_REGION` - AWS region (default: us-east-1)
- `DEBUG_MCP_TOOLS` - Comma-separated list of tools to expose (default: 10 core debugging tools)
  - Default (if not set): CloudWatch Logs (5 tools) + Step Functions (5 tools)
  - Set to "all" to expose all 26 tools
  - Set to comma-separated list to expose only specific tools
  - See available tool names in README.md

**Step Functions Configuration** (optional):
- `STATE_MACHINE_LIST` - Comma-separated list of state machine names to expose
- `STATE_MACHINE_PREFIX` - Auto-include state machines with this prefix
- `STATE_MACHINE_TAG_KEY` + `STATE_MACHINE_TAG_VALUE` - Filter state machines by AWS tags

## Implementation Phases

### Phase 1: MVP (CloudWatch Logs) - ✅ COMPLETE
The MVP proxies selected CloudWatch Logs tools from awslabs.cloudwatch-mcp-server:
- `describe_log_groups` - List available log groups with optional prefix filtering
- `analyze_log_group` - Analyze logs for anomalies and patterns
- `execute_log_insights_query` - Execute CloudWatch Insights queries
- `get_logs_insight_query_results` - Get query results

Implementation pattern (to add more tools):
1. Identify the tool you want from the upstream AWS MCP server
2. Add a proxy function in `server.py` with `@mcp.tool()` decorator
3. Call `await proxy.call_cloudwatch_tool(tool_name, arguments)`
4. The proxy handles subprocess spawning and communication

### Phase 2: Expand Services
- Step Functions execution details and history
- ECS task logs and failures
- Lambda invocation logs
- Time-based correlation across services

### Phase 3: Polish
- Comprehensive test coverage
- Enhanced error handling and validation
- Community documentation and examples

## Adding New Tools

See the "Development" section in README.md for a guide on adding new AWS MCPs and tools.

Quick summary for adding tools from existing AWS MCP servers:

### For CloudWatch (already connected):
1. Add proxy function in `server.py`:
```python
if should_expose_tool("new_tool_name"):
    @mcp.tool()
    async def new_tool_name(arg1: str) -> dict:
        """Tool description for Claude."""
        return await proxy.call_cloudwatch_tool("upstream_tool_name", {"arg1": arg1})
```

### For new AWS services (Step Functions, ECS, Lambda):
1. Add connection method in `mcp_proxy.py`:
```python
@asynccontextmanager
async def _connect_to_stepfunctions(self):
    server_params = StdioServerParameters(
        command="uvx",
        args=["awslabs.step-functions-mcp-server@latest"],
        env={"AWS_PROFILE": self.aws_profile, "AWS_REGION": self.aws_region}
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

async def call_stepfunctions_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
    async with self._connect_to_stepfunctions() as session:
        result = await session.call_tool(tool_name, arguments)
        return result.content
```

2. Add proxy functions in `server.py`:
```python
if should_expose_tool("describe_execution"):
    @mcp.tool()
    async def describe_execution(execution_arn: str) -> dict:
        """Get Step Functions execution details."""
        return await proxy.call_stepfunctions_tool("describe_execution", {"execution_arn": execution_arn})
```

**Resources**:
- [AWS MCP Servers](https://awslabs.github.io/mcp/) - Find available MCPs and their tools
- README.md - Step-by-step examples with Step Functions, ECS, Lambda (see Development section)

## Dependencies

**Core**:
- `fastmcp>=0.2.0` - MCP server framework (provides tool decoration and server hosting)
- `mcp>=1.0.0` - MCP SDK (provides client for connecting to upstream AWS MCPs)
- `pydantic>=2.0.0` - Data validation

**Upstream AWS MCPs** (spawned as subprocesses):
- `awslabs.cloudwatch-mcp-server` - CloudWatch Logs, Metrics, Alarms
- `awslabs.step-functions-mcp-server` - Step Functions (Phase 2)
- `awslabs.ecs-mcp-server` - ECS tasks and services (Phase 2)

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