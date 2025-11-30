# Technical Specification: Tool Discovery Gateway

- **Functional Specification:** `context/spec/002-tool-discovery-gateway/functional-spec.md`
- **Status:** Draft
- **Author(s):** Claude (with python-expert analysis)

---

## 1. High-Level Technical Approach

Replace 17 individual `@mcp.tool()` functions with a single `debug` gateway tool backed by a registry system.

**Key Components:**
1. **`ToolRegistry`** - Central registry mapping tool names → handlers + schemas
2. **`@debug_tool()` decorator** - Registers tools with inline schema definitions
3. **Pydantic argument models** - Per-tool validation
4. **`debug()` gateway** - Single MCP tool that routes to registered handlers

**Systems Affected:**
- `server.py` - Simplified to only expose `debug()` gateway
- New `registry.py` - Contains registry, schemas, decorator, and tool registrations

---

## 2. Proposed Solution & Implementation Plan

### 2.1 New File: `src/debug_mcp/registry.py`

Contains all registry infrastructure and tool registrations.

**Core Classes:**

```python
# Pydantic models for schema definition
class ToolParameter(BaseModel):
    name: str
    type: str  # "string", "integer", "boolean", "list[str]"
    description: str
    required: bool = True
    default: Any = None

class ToolSchema(BaseModel):
    name: str
    description: str
    category: str  # "cloudwatch", "stepfunctions", "langsmith", "jira"
    parameters: list[ToolParameter]

# Registry entry combining schema + handler
@dataclass
class ToolRegistryEntry:
    schema: ToolSchema
    handler: Callable[..., Awaitable[dict]]
    arg_model: type[BaseModel] | None = None

# Central registry
class ToolRegistry:
    _tools: dict[str, ToolRegistryEntry]

    def register(schema, handler, arg_model=None)
    def list_categories() -> list[dict]
    def list_tools(category: str | None) -> list[dict]
    def execute(tool_name: str, arguments: dict) -> dict
```

**Decorator for registration:**

```python
def debug_tool(
    name: str,
    description: str,
    category: str,
    parameters: list[ToolParameter],
    arg_model: type[BaseModel] | None = None
) -> Callable
```

### 2.2 Argument Models (Pydantic)

One model per tool for validation:

```python
# CloudWatch tools
class DescribeLogGroupsArgs(BaseModel):
    log_group_name_prefix: str = ""
    region: str = ""

class AnalyzeLogGroupArgs(BaseModel):
    log_group_name: str
    start_time: str
    end_time: str
    filter_pattern: str = ""
    region: str = ""

class ExecuteLogInsightsQueryArgs(BaseModel):
    log_group_names: list[str]
    query_string: str
    start_time: str
    end_time: str
    limit: int = 100
    region: str = ""

class GetLogsInsightQueryResultsArgs(BaseModel):
    query_id: str
    region: str = ""

# Step Functions tools (5 models)
# LangSmith tools (6 models)
# Jira tools (2 models)
```

### 2.3 Tool Registrations

Each tool registered with decorator:

```python
@debug_tool(
    name="describe_log_groups",
    description="List CloudWatch log groups",
    category="cloudwatch",
    parameters=[
        ToolParameter(name="log_group_name_prefix", type="string",
                     description="Filter by prefix", required=False, default=""),
        ToolParameter(name="region", type="string",
                     description="AWS region", required=False, default="")
    ],
    arg_model=DescribeLogGroupsArgs
)
async def describe_log_groups(log_group_name_prefix: str = "", region: str = "") -> dict:
    return await cw_logs.describe_log_groups(
        log_group_name_prefix=log_group_name_prefix, region=region
    )
```

### 2.4 Modified: `src/debug_mcp/server.py`

Simplified to only expose the gateway:

```python
from fastmcp import FastMCP
from .registry import registry

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

    # Parse arguments
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError as e:
        return {"error": True, "message": f"Invalid JSON: {e}"}

    # Discovery mode
    if tool == "list":
        return {"categories": registry.list_categories()}

    if tool.startswith("list:"):
        category = tool.split(":", 1)[1]
        return {"tools": registry.list_tools(category)}

    # Execution mode
    try:
        return await registry.execute(tool, args)
    except ValueError as e:
        return {"error": True, "message": str(e)}
    except Exception as e:
        return {"error": True, "message": f"Execution failed: {e}"}
```

### 2.5 Code Removal

Delete from `server.py`:
- `DEFAULT_TOOLS` constant
- `configured_tools_str` / `configured_tools` variables
- `should_expose_tool()` function
- `is_jira_configured()`, `is_aws_configured()`, `is_langsmith_configured()` - move to registry
- All 17 individual `@mcp.tool()` decorated functions
- `_extract_run_summary()` helper - move to registry

### 2.6 Documentation Updates

**README.md:**
- Remove `DEBUG_MCP_TOOLS` documentation
- Add new usage pattern with `debug()` gateway
- Update examples

**CLAUDE.md:**
- Remove tool filtering section
- Update architecture description

---

## 3. Impact and Risk Analysis

### System Dependencies

| Component | Impact |
|-----------|--------|
| `tools/*.py` | None - implementations unchanged |
| `server.py` | Major rewrite - only gateway remains |
| `__main__.py` | None - CLI unchanged |
| MCP clients | Breaking change - tool names change |

### Potential Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| **Breaking change for existing users** | Document migration path; version bump |
| **JSON parsing errors** | Rich error messages with schema hints |
| **Performance overhead** | Registry is in-memory; negligible impact |
| **Lost IDE autocomplete** | Tool schemas returned in discovery response |
| **Complex nested arguments** | Pydantic handles list/dict types automatically |

---

## 4. Testing Strategy

### Integration Tests via MCP Client

Tests run via actual MCP tool calls using the MCP client SDK, NOT Python unit tests.

**Test Pattern:**
```bash
uv run python -c "
import asyncio
import json
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test():
    server_params = StdioServerParameters(
        command='uv',
        args=['run', '--directory', '/Users/eb/PycharmProjects/debug_mcp', 'debug-mcp',
              '--aws-region', 'us-west-2',
              '--aws-profile', '<AWS_PROFILE>']
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Test discovery
            result = await session.call_tool('debug', {'tool': 'list'})
            print(f'list categories: {result.content[0].text}')

            # Test category listing
            result = await session.call_tool('debug', {'tool': 'list:cloudwatch'})
            print(f'cloudwatch tools: {result.content[0].text}')

            # Test execution
            result = await session.call_tool('debug', {
                'tool': 'describe_log_groups',
                'arguments': '{\"log_group_name_prefix\": \"/aws/lambda/\"}'
            })
            print(f'describe_log_groups: {result.content[0].text}')

asyncio.run(test())
"
```

### Test Cases

**Discovery Mode:**
```
debug(tool="list")
# Expected: All 4 categories with descriptions

debug(tool="list:cloudwatch")
# Expected: 4 CloudWatch tools with full schemas

debug(tool="list:stepfunctions")
# Expected: 5 Step Functions tools with full schemas

debug(tool="list:langsmith")
# Expected: 6 LangSmith tools with full schemas

debug(tool="list:jira")
# Expected: 2 Jira tools with full schemas
```

**Execution Mode:**
```
debug(tool="describe_log_groups", arguments='{"log_group_name_prefix": "/aws/lambda/"}')
# Expected: List of Lambda log groups

debug(tool="list_state_machines", arguments='{"max_results": 5}')
# Expected: List of state machines

debug(tool="list_langsmith_projects", arguments='{"environment": "prod", "limit": 5}')
# Expected: List of LangSmith projects

debug(tool="search_jira_tickets", arguments='{"status": "To Do", "limit": 3}')
# Expected: Jira search results
```

**Error Handling:**
```
debug(tool="unknown_tool", arguments='{}')
# Expected: {"error": true, "message": "Unknown tool: unknown_tool", "available_tools": [...]}

debug(tool="describe_log_groups", arguments='invalid json')
# Expected: {"error": true, "message": "Invalid JSON: ..."}

debug(tool="execute_log_insights_query", arguments='{}')
# Expected: {"error": true, "message": "Missing required parameter: log_group_names"}
```

### Update Memory File

After implementation, update `tool-verification-tests` memory to reflect new gateway pattern.
