# Debug MCP

MCP server for debugging distributed systems (AWS CloudWatch Logs, Step Functions, LangSmith, Jira) directly from Claude Code or any MCP client.

**Status**: ✅ Complete - Single gateway tool exposing 17 debugging tools
**Context Reduction**: ~95% token savings (13K → ~500 tokens)
**Repository**: https://github.com/Coykto/debug_mcp

## Quick Start

### Installation

**Option 1: Using Claude Code CLI (Recommended)**

AWS only:
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-aws-profile-name
```

AWS + Jira:
```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --aws-profile your-aws-profile-name \
    --jira-host yourcompany.atlassian.net \
    --jira-email your.email@company.com \
    --jira-project PROJ \
    --jira-token your-api-token
```

**Option 2: Manual configuration in `.mcp.json`**

AWS only:
```json
{
  "mcpServers": {
    "debug-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/Coykto/debug_mcp",
        "debug-mcp",
        "--aws-region", "us-west-2",
        "--aws-profile", "your-aws-profile-name"
      ]
    }
  }
}
```

AWS + Jira:
```json
{
  "mcpServers": {
    "debug-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/Coykto/debug_mcp",
        "debug-mcp",
        "--aws-region", "us-west-2",
        "--aws-profile", "your-aws-profile-name",
        "--jira-host", "yourcompany.atlassian.net",
        "--jira-email", "your.email@company.com",
        "--jira-project", "PROJ",
        "--jira-token", "your-api-token"
      ]
    }
  }
}
```

**Note**: Configuration is passed as CLI arguments to work around a [known bug in Claude Code](https://github.com/anthropics/claude-code/issues/1254) where environment variables aren't reliably passed to MCP servers.

**Prerequisites:**
- Python 3.11+
- `uvx` installed ([installation guide](https://docs.astral.sh/uv/))
- AWS credentials configured (`aws configure`)
- For Jira: API token from [Atlassian](https://id.atlassian.com/manage-profile/security/api-tokens) (see [Jira Configuration](#jira-configuration))

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

> **Note**: LangSmith integration currently requires AWS Secrets Manager for `prod`/`dev` environments (this is how our team stores credentials). If you'd like to use LangSmith with direct CLI token arguments (similar to Jira), PRs are welcome!

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

Jira integration allows you to search tickets and get full ticket details directly from Claude Code.

#### Step 1: Create a Jira API Token

1. Go to [Atlassian API Token Management](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Click **Create API token**
3. Give it a descriptive label (e.g., "Debug MCP")
4. Copy the generated token (you won't see it again)

#### Step 2: Gather Your Jira Details

You'll need:
- **Host**: Your Jira Cloud hostname (e.g., `yourcompany.atlassian.net`)
- **Email**: The email address associated with your Atlassian account
- **Project**: The project key for your default project (e.g., `PROJ`, `DEV`, `CORE`)
- **Token**: The API token from Step 1

#### Step 3: Configure Debug MCP

**Option A: Claude Code CLI (Recommended)**

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

**Option B: Manual `.mcp.json` Configuration**

```json
{
  "mcpServers": {
    "debug-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from", "git+https://github.com/Coykto/debug_mcp",
        "debug-mcp",
        "--aws-region", "us-west-2",
        "--aws-profile", "your-profile-name",
        "--jira-host", "yourcompany.atlassian.net",
        "--jira-email", "your.email@company.com",
        "--jira-project", "PROJ",
        "--jira-token", "your-api-token"
      ]
    }
  }
}
```

**Option C: Use Environment Variable for Token**

If you prefer not to store the token in your config, set `JIRA_API_TOKEN` as an environment variable before launching Claude Code:

```bash
export JIRA_API_TOKEN=your-api-token
```

Then omit `--jira-token` from the CLI args (other Jira args are still required).

#### Configuration Reference

| Source | Name | Required | Description |
|--------|------|----------|-------------|
| CLI arg | `--jira-host` | Yes | Jira Cloud hostname (e.g., `company.atlassian.net`) |
| CLI arg | `--jira-email` | Yes | Atlassian account email |
| CLI arg | `--jira-project` | Yes | Default Jira project key (e.g., `PROJ`) |
| CLI arg | `--jira-token` | Yes* | Jira API token |
| Env var | `JIRA_API_TOKEN` | Yes* | Alternative to `--jira-token` CLI arg |

*Either `--jira-token` or `JIRA_API_TOKEN` is required.

#### Jira Troubleshooting

**"Jira credentials not configured" error:**
- Verify all required args are provided: `--jira-host`, `--jira-email`, `--jira-project`, and token
- Check that your API token is valid at [Atlassian API Tokens](https://id.atlassian.com/manage-profile/security/api-tokens)

**"401 Unauthorized" error:**
- Your API token may have expired - create a new one
- Verify the email matches your Atlassian account exactly

**"Project not found" error:**
- Check the project key (not name) - it's the prefix in ticket IDs (e.g., `PROJ` in `PROJ-123`)
- Ensure your account has access to the project

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

## Contributing

Contributions are welcome! Some areas where PRs would be appreciated:

- **LangSmith CLI token support**: Currently LangSmith credentials are loaded from AWS Secrets Manager (for `prod`/`dev`) or `.env` files (for `local`). Adding `--langsmith-api-key` CLI argument support (similar to Jira) would make setup easier for teams not using Secrets Manager.
- **Additional debugging tools**: New tools for other AWS services (ECS, Lambda logs, X-Ray traces)
- **Bug fixes and improvements**: Error handling, documentation, tests

To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes (see [Adding New Tools](CLAUDE.md#adding-new-tools) in CLAUDE.md)
4. Submit a PR

## License

MIT License - See LICENSE file
