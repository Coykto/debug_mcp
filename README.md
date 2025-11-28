# Debug MCP

MCP server for debugging distributed systems (AWS CloudWatch Logs, Step Functions, LangSmith, Jira) directly from Claude Code or any MCP client.

**Status**: ✅ Complete - 18 debugging tools using boto3, LangSmith SDK, and Jira SDK
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

### What You Can Ask Claude

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

## How It Works

This MCP server implements debugging tools using **boto3 and SDKs directly**:
- CloudWatch Logs tools use boto3 client
- Step Functions tools use boto3 client
- LangSmith tools use LangSmith SDK

No AWS MCP servers are used - everything is implemented directly for better reliability and region handling.

## Available Tools

### CloudWatch Logs (5 tools)

- `describe_log_groups` - List CloudWatch log groups
- `analyze_log_group` - Analyze logs for anomalies and patterns
- `execute_log_insights_query` - Run CloudWatch Insights queries
- `get_logs_insight_query_results` - Get query results
- `cancel_logs_insight_query` - Cancel running query

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

### Tool Selection

Filter which tools to expose using `DEBUG_MCP_TOOLS`:

```json
// Default (if not set) - all 18 debugging tools
// CloudWatch Logs (5) + Step Functions (5) + LangSmith (6) + Jira (2)
// Omit DEBUG_MCP_TOOLS to use this default

// Minimal - only logs
"DEBUG_MCP_TOOLS": "describe_log_groups,execute_log_insights_query,get_logs_insight_query_results"

// Logs and Step Functions only
"DEBUG_MCP_TOOLS": "describe_log_groups,analyze_log_group,execute_log_insights_query,list_state_machines,get_step_function_execution_details"
```

**Default tools** (when `DEBUG_MCP_TOOLS` is not set):
- CloudWatch Logs: `describe_log_groups`, `analyze_log_group`, `execute_log_insights_query`, `get_logs_insight_query_results`, `cancel_logs_insight_query`
- Step Functions: `list_state_machines`, `get_state_machine_definition`, `list_step_function_executions`, `get_step_function_execution_details`, `search_step_function_executions`
- LangSmith: `list_langsmith_projects`, `list_langsmith_runs`, `get_langsmith_run_details`, `search_langsmith_runs`, `search_run_content`, `get_run_field`
- Jira: `search_jira_tickets`, `get_jira_ticket`

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

### Too many tools in the list
- Set `DEBUG_MCP_TOOLS` environment variable to filter tools
- See available tool names above
- Example: `"env": {"DEBUG_MCP_TOOLS": "describe_log_groups,list_state_machines"}`

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

The server uses direct boto3/SDK implementations:

**CloudWatch Logs** (`src/debug_mcp/tools/cloudwatch_logs.py`):
- Uses boto3 CloudWatch Logs client
- Handles region configuration via constructor
- Each tool method creates a client for the requested region

**Step Functions** (`src/debug_mcp/tools/stepfunctions.py`):
- Uses boto3 Step Functions client
- Implements execution search and filtering

**LangSmith** (`src/debug_mcp/tools/langsmith.py`):
- Uses LangSmith SDK directly
- Multi-environment support via AWS Secrets Manager

**Jira** (`src/debug_mcp/tools/jira.py`):
- Uses Jira SDK directly
- Supports Jira Cloud authentication via API token
- Lazy client initialization

**Main Server** (`src/debug_mcp/server.py`):
- FastMCP framework for MCP server hosting
- Tool registration and exposure filtering
- Initializes all tool classes with AWS credentials from environment variables

## Team Sharing

Share with your team:
1. They update `AWS_PROFILE` with their own profile name
2. Optionally adjust `AWS_REGION` if different
3. Optionally customize `DEBUG_MCP_TOOLS` to their preference

## License

MIT License - See LICENSE file
