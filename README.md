# Debug MCP

MCP server for debugging distributed systems (AWS CloudWatch Logs, Step Functions, LangSmith, Jira) directly from Claude Code or any MCP client.

**Status**: ✅ Complete - Single gateway tool exposing 17 debugging tools
**Context Reduction**: ~95% token savings (13K → ~500 tokens)
**Repository**: https://github.com/Coykto/debug_mcp

## Quick Start

### Installation

**Option 1: Using Claude Code CLI (Recommended)**

```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-aws-profile-name
```

**Option 2: Manual configuration in `.mcp.json`**

```json
{
  "mcpServers": {
    "debug-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Coykto/debug_mcp",
        "debug-mcp",
        "--aws-region",
        "us-west-2",
        "--aws-profile",
        "your-aws-profile-name"
      ]
    }
  }
}
```

**Note**: AWS region and profile are passed as CLI arguments to work around a [known bug in Claude Code](https://github.com/anthropics/claude-code/issues/1254) where environment variables aren't reliably passed to MCP servers.

**Prerequisites:**
- Python 3.11+
- `uvx` installed ([installation guide](https://docs.astral.sh/uv/))
- AWS credentials configured (`aws configure`)

## How to Use

Debug MCP exposes a **single gateway tool** called `debug()` that provides discovery and execution of 17 debugging tools:

### Discovery Pattern

Ask Claude to discover available tools:

```
"What debugging tools are available?"
→ Claude calls: debug(tool="list")

"What CloudWatch tools are available?"
→ Claude calls: debug(tool="list:cloudwatch")

"List all Step Functions tools"
→ Claude calls: debug(tool="list:stepfunctions")
```

### Execution Pattern

Ask Claude natural language questions and it will use the appropriate tool:

**CloudWatch Logs:**
- "List all Lambda log groups"
- "Search for ERROR in /aws/lambda/my-function from the last hour"
- "Analyze /aws/lambda/my-function logs for patterns"
- "Run a CloudWatch Insights query on my Lambda logs"

**Step Functions Debugging:**
- "List all my Step Functions state machines"
- "Show me the workflow definition and Lambda functions for state machine X"
- "Show me failed executions for state machine X from the last 3 days"
- "Get execution details including the workflow definition"
- "Find executions where the Match state output contains 'company' and show me the Lambda ARNs"

**LangSmith Tracing:**
- "List my LangSmith projects in prod environment"
- "Show me errored runs from the last hour in production"
- "Get details for LangSmith run abc-123 in dev"
- "Search for conversations containing a specific error message"

**Jira Tickets:**
- "Search for bugs in To Do status"
- "Find tickets assigned to me"
- "Get details for ticket PROJ-123"
- "Show me all in-progress stories about authentication"

Claude automatically translates your questions into the appropriate `debug()` call with the right tool name and arguments.

## How It Works

This MCP server uses a **Tool Discovery Gateway** pattern:

1. **Single Tool Interface**: Exposes one `debug()` tool to Claude instead of 17 individual tools
2. **~95% Token Reduction**: Reduces context from ~13K tokens to ~500 tokens (tool list only)
3. **Category-based Discovery**: Tools organized by category (cloudwatch, stepfunctions, langsmith, jira)
4. **Direct Implementation**: Uses boto3 and SDKs directly (no AWS MCP proxies)

### Gateway Architecture

```
debug(tool="list")                     → List categories
debug(tool="list:cloudwatch")          → List CloudWatch tools
debug(tool="describe_log_groups", ...) → Execute tool
```

All 17 debugging tools remain available - they're just accessed through the gateway instead of being exposed individually.

## Available Tools (via Gateway)

### CloudWatch Logs (4 tools)

- `describe_log_groups` - List CloudWatch log groups
- `analyze_log_group` - Analyze logs for anomalies and patterns
- `execute_log_insights_query` - Run CloudWatch Insights queries
- `get_logs_insight_query_results` - Get query results

### Step Functions (5 tools)

**Debugging:**
- `list_state_machines` - List all state machines (get ARNs)
- `get_state_machine_definition` - Get ASL definition with extracted Lambda ARNs and resources
- `list_step_function_executions` - List executions with filtering
- `get_step_function_execution_details` - Get full execution details with state inputs/outputs
- `search_step_function_executions` - Advanced search with state/input/output pattern matching

**Definition & Resources:**
The `get_state_machine_definition` tool extracts:
- Full Amazon States Language (ASL) workflow definition
- Lambda function ARNs used in the workflow
- Other resources (SNS topics, SQS queues, DynamoDB tables, nested state machines)
- IAM role, logging, and tracing configuration

You can also include the definition with execution details using `include_definition=True` in:
- `get_step_function_execution_details` - See the workflow definition alongside execution data
- `search_step_function_executions` - See definitions with filtered execution results

### LangSmith (6 tools)

**Tracing & Debugging:**
- `list_langsmith_projects` - List available LangSmith projects
- `list_langsmith_runs` - List runs/traces with filtering (type, errors, time range)
- `get_langsmith_run_details` - Get full run details with inputs/outputs and child runs (stores in memory)
- `search_langsmith_runs` - Search for conversations containing specific text
- `search_run_content` - Semantic search within a stored run's content
- `get_run_field` - Get a specific field from a stored run

**Multi-Environment Support:**
Each LangSmith tool requires an `environment` parameter:
- `prod` - Uses `PRODUCTION/env/vars` from AWS Secrets Manager
- `dev` - Uses `DEV/env/vars` from AWS Secrets Manager
- `local` - Loads from `.env` file using python-dotenv

**Credentials in Secrets Manager:**
Your AWS Secrets Manager secret should contain:
- `LANGCHAIN_API_KEY` - Your LangSmith API key
- `LANGCHAIN_PROJECT` - Default project name (optional)

**Local Development (.env file):**
```env
LANGCHAIN_API_KEY=ls_your_api_key_here
LANGCHAIN_PROJECT=your-project-name
```

### Jira (2 tools)

- `search_jira_tickets` - Search tickets with filters (type, status, assignee) and text search
- `get_jira_ticket` - Get full ticket details including linked issues, attachments, subtasks, and Epic children

**Returned fields for `get_jira_ticket`:**
- Basic: key, summary, description, status, issue_type, priority, assignee, reporter, labels, created, updated
- Relationships: linked_issues, parent (for subtasks), subtasks, epic_children (for Epics)
- Attachments: list of filenames

## Configuration

### AWS Authentication

Pass AWS credentials as CLI arguments (recommended to work around [Claude Code env var bug](https://github.com/anthropics/claude-code/issues/1254)):

```bash
# Using Claude Code CLI
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-profile-name
```

Or in `.mcp.json`:
```json
"args": [
  "--from", "git+https://github.com/Coykto/debug_mcp",
  "debug-mcp",
  "--aws-region", "us-west-2",
  "--aws-profile", "your-profile-name"
]
```

**Alternative**: Set environment variables before launching Claude Code:
```bash
export AWS_REGION=us-west-2
export AWS_PROFILE=your-profile-name
# Then launch Claude Code
```

### Jira Configuration

Pass Jira credentials as CLI arguments:

| Source | Name | Required | Description |
|--------|------|----------|-------------|
| CLI arg | `--jira-host` | Yes | Jira Cloud hostname (e.g., `company.atlassian.net`) |
| CLI arg | `--jira-email` | Yes | Atlassian account email |
| CLI arg | `--jira-project` | Yes | Default Jira project key (e.g., `PROJ`) |
| CLI arg | `--jira-token` | Yes* | [Jira API token](https://id.atlassian.com/manage-profile/security/api-tokens) |
| Env var | `JIRA_API_TOKEN` | Yes* | Alternative to `--jira-token` CLI arg |

*Either `--jira-token` or `JIRA_API_TOKEN` env var is required.

**Example with Jira (all CLI args):**
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-profile-name \
    --jira-host yourcompany.atlassian.net \
    --jira-email your.email@company.com \
    --jira-project PROJ \
    --jira-token your-api-token
```

Or use `JIRA_API_TOKEN` environment variable if you prefer not to pass the token as CLI arg.

## Troubleshooting

### Server won't start
- Check AWS credentials: `aws sts get-caller-identity --profile YOUR_PROFILE`
- Verify uvx is installed: `uvx --version`
- Check Claude Code MCP logs in settings

### Wrong AWS region/account
- Update `--aws-region` and `--aws-profile` CLI arguments
- Make sure the profile exists in `~/.aws/credentials`
- Verify the region is correct: `aws configure get region --profile YOUR_PROFILE`

### Environment variables not working
Due to a [known bug in Claude Code](https://github.com/anthropics/claude-code/issues/1254), environment variables in the MCP `env` block aren't reliably passed to servers. **Use CLI arguments instead** (see installation examples above).

## Development

### Local Development

```bash
# Install dependencies
uv sync

# Run the server locally
uv run debug-mcp --aws-region us-west-2 --aws-profile your-profile

# Test
uv run pytest
```

### Architecture

The server uses a **Tool Discovery Gateway** pattern with direct boto3/SDK implementations:

**Gateway Layer** (`src/debug_mcp/server.py`):
- Single `debug()` tool exposed to Claude
- Handles discovery (`tool="list"`, `tool="list:cloudwatch"`)
- Routes execution to registered tools
- Validates arguments with Pydantic models

**Registry System** (`src/debug_mcp/registry.py`):
- Central registry for all tools with schemas
- Category-based organization
- `@debug_tool()` decorator for registration
- Validation and execution routing

**Tool Implementations**:
- **CloudWatch** (`cloudwatch_logs.py` + `cloudwatch_registry.py`): boto3 CloudWatch Logs client
- **Step Functions** (`stepfunctions.py` + `stepfunctions_registry.py`): boto3 Step Functions client
- **LangSmith** (`langsmith.py` + `langsmith_registry.py`): LangSmith SDK with multi-environment support
- **Jira** (`jira.py` + `jira_registry.py`): Jira SDK with lazy client initialization

Each `*_registry.py` file registers tools using the `@debug_tool()` decorator with schemas and handlers.

## Team Sharing

Share with your team:
1. They update `--aws-profile` with their own profile name
2. Optionally adjust `--aws-region` if different
3. All 17 debugging tools are available through the single `debug()` gateway - no tool filtering needed

## License

MIT License - See LICENSE file
