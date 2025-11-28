# MCP Tool Verification Tests

**Purpose:** This file contains test calls to verify all MCP tools are working correctly via actual MCP tool calls.

**Testing Approach:**
- Tests run via MCP tool calls (using `mcp__debug-mcp__*` tools), NOT Python directly
- Credentials are read from user's shell and passed to subagent
- Never store tokens in memory files (they get committed)

**For Main Agent - Before Running Tests:**
```bash
# Read these values from user's shell:
echo "AWS_PROFILE=$AWS_PROFILE"
echo "JIRA_API_TOKEN=$JIRA_API_TOKEN"
```

Then pass the values explicitly to the subagent prompt.

**For Subagents - Testing Approach:**
1. Run tools directly via `uv run python -c "..."` with inline code
2. Do NOT create test files - just run commands and observe output
3. Make one tool call, print result, move to next
4. Compile report from outputs at the end

**Example test pattern:**
```bash
uv run python -c "
import os
os.environ['JIRA_HOST'] = 'provectus-dev.atlassian.net'
os.environ['JIRA_EMAIL'] = 'ebasmov@provectus.com'
os.environ['JIRA_PROJECT'] = 'IGAL'
os.environ['JIRA_API_TOKEN'] = '<token>'

from debug_mcp.tools.jira import JiraDebugger
jira = JiraDebugger()
result = jira.search_tickets(query='graph', limit=5)
print(f'Search graph: {result[\"total\"]} results')
for t in result['results'][:3]:
    print(f'  {t[\"key\"]}: {t[\"summary\"]}')
"
```

Repeat for each tool, then compile results into a report table.

**MCP Server Configuration:**
The MCP server must be started with proper arguments for Jira tools to be exposed:
- `--jira-host provectus-dev.atlassian.net`
- `--jira-email ebasmov@provectus.com`
- `--jira-project IGAL`
- `--jira-token <token>` (or `JIRA_API_TOKEN` env var)

**For subagents to run MCP with all credentials:**
```bash
uv run debug-mcp \
    --aws-region us-west-2 \
    --aws-profile <profile> \
    --jira-host provectus-dev.atlassian.net \
    --jira-email ebasmov@provectus.com \
    --jira-project IGAL \
    --jira-token <token>
```

---

## CloudWatch Logs Tools (5 tools)
Test via MCP:

### describe_log_groups
```
mcp__debug-mcp__describe_log_groups(log_group_name_prefix="/aws/lambda/")
```
Expected: List of Lambda log groups

### analyze_log_group
```
mcp__debug-mcp__analyze_log_group(
    log_group_name="/aws/lambda/<pick-from-list>",
    start_time="<1-hour-ago-ISO>",
    end_time="<now-ISO>"
)
```
Expected: Log analysis with patterns and anomalies

### execute_log_insights_query
```
mcp__debug-mcp__execute_log_insights_query(
    log_group_names=["/aws/lambda/<pick-from-list>"],
    query_string="fields @timestamp, @message | sort @timestamp desc | limit 20",
    start_time="<1-hour-ago-ISO>",
    end_time="<now-ISO>"
)
```
Expected: Query ID for async results

### get_logs_insight_query_results
```
mcp__debug-mcp__get_logs_insight_query_results(query_id="<from-execute-query>")
```
Expected: Query results or status

### cancel_logs_insight_query
```
mcp__debug-mcp__cancel_logs_insight_query(query_id="<from-execute-query>")
```
Expected: Cancellation confirmation

---

## Step Functions Tools (5 tools)
Test via MCP:

### list_state_machines
```
mcp__debug-mcp__list_state_machines(max_results=10)
```
Expected: List of state machines with ARNs

### get_state_machine_definition
```
mcp__debug-mcp__get_state_machine_definition(state_machine_arn="<from-list>")
```
Expected: ASL definition with Lambda ARNs

### list_step_function_executions
```
mcp__debug-mcp__list_step_function_executions(
    state_machine_arn="<from-list>",
    max_results=10
)
```
Expected: List of executions

### get_step_function_execution_details
```
mcp__debug-mcp__get_step_function_execution_details(execution_arn="<from-list>")
```
Expected: Full execution details with state history

### search_step_function_executions
```
mcp__debug-mcp__search_step_function_executions(
    state_machine_arn="<from-list>",
    max_results=10
)
```
Expected: Filtered executions

---

## LangSmith Tools (6 tools)
Test via MCP:

### list_langsmith_projects
```
mcp__debug-mcp__list_langsmith_projects(environment="prod", limit=10)
```
Expected: List of LangSmith projects

### list_langsmith_runs
```
mcp__debug-mcp__list_langsmith_runs(
    environment="prod",
    project_name="<from-list>",
    limit=10
)
```
Expected: List of runs/traces

### get_langsmith_run_details
```
mcp__debug-mcp__get_langsmith_run_details(
    environment="prod",
    run_id="<from-list>"
)
```
Expected: Run details with reference_id for further queries

### search_langsmith_runs
```
mcp__debug-mcp__search_langsmith_runs(
    environment="prod",
    search_text="<specific-text>",
    limit=10
)
```
Expected: Matching runs

### search_run_content
```
mcp__debug-mcp__search_run_content(
    reference_id="<from-get-details>",
    query="<search-query>"
)
```
Expected: Matching content chunks

### get_run_field
```
mcp__debug-mcp__get_run_field(
    reference_id="<from-get-details>",
    field_path="outputs"
)
```
Expected: Field value

---

## Jira Tools (2 tools)
**Requires:** MCP server started with `--jira-host`, `--jira-email`, `--jira-project` and `JIRA_API_TOKEN` env var

**Known test issues:**
- `IGAL-1064` - Epic with 5 children (Graph introduction)
- `IGAL-1067` - Task with attachments (Graph Schema: Entities & Features)
- `IGAL-1488` - Sub-task with parent IGAL-1487 (Test MCP integration with Context 7)
- `IGAL-1487` - Task with 2 linked issues (Implement AgentCore Gateway client)
- `IGAL-1421` - Task with 2 linked issues, cloned (Implement automatic update of Barley's self-awareness)
- `IGAL-1533` - Bug, In Progress (L.Tawfic - Missing recap)
- `IGAL-1542` - Bug, To Do (Barley fails to request clarification)

Test via MCP:

### search_jira_tickets
```
# Search by text query - finds IGAL-1067, IGAL-1064, IGAL-1410, etc.
mcp__debug-mcp__search_jira_tickets(query="graph", limit=5)

# Search by status - finds IGAL-1064, IGAL-1542, IGAL-1541, etc.
mcp__debug-mcp__search_jira_tickets(status="To Do", limit=5)

# Search by assignee
mcp__debug-mcp__search_jira_tickets(assignee="Evgenii Basmov", limit=5)

# Search by issue type - finds IGAL-1533, IGAL-1542, IGAL-1541, etc.
mcp__debug-mcp__search_jira_tickets(issue_type="Bug", limit=5)

# Search for Sub-tasks - finds IGAL-1488, IGAL-1490, etc.
mcp__debug-mcp__search_jira_tickets(issue_type="Sub-task", limit=5)

# No parameters (should return error)
mcp__debug-mcp__search_jira_tickets()
# Expected: {"error": "At least one search parameter is required..."}
```

### get_jira_ticket
```
# Task with attachments (3 files)
mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-1067")
# Expected: attachments list with 3 filenames

# Epic with children (5 child issues)
mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-1064")
# Expected: epic_children list with 5 issues (IGAL-1065, IGAL-1067, IGAL-1068, IGAL-1069, IGAL-1070)

# Sub-task with parent
mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-1488")
# Expected: parent = {"key": "IGAL-1487", "summary": "Implement AgentCore Gateway client..."}

# Task with linked issues (2 links)
mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-1487")
# Expected: linked_issues with "blocks" and "relates to" links

# Bug
mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-1533")
# Expected: issue_type = "Bug", status = "In Progress"

# Invalid ticket (should return error)
mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-99999")
# Expected: {"error": "Issue IGAL-99999 not found"}
```

---

## Quick Verification via MCP

Run these MCP tool calls in sequence to verify all services:

1. **CloudWatch Logs:**
   ```
   mcp__debug-mcp__describe_log_groups(log_group_name_prefix="/aws/lambda/")
   ```
   Expected: List of log groups

2. **Step Functions:**
   ```
   mcp__debug-mcp__list_state_machines(max_results=5)
   ```
   Expected: List of state machines

3. **LangSmith:**
   ```
   mcp__debug-mcp__list_langsmith_projects(environment="prod", limit=5)
   ```
   Expected: List of projects

4. **Jira:**
   ```
   mcp__debug-mcp__search_jira_tickets(status="To Do", limit=3)
   mcp__debug-mcp__get_jira_ticket(issue_key="IGAL-1064")
   ```
   Expected: Search results and Epic with children

---

## When to Update This File

- **Adding new tools**: Add MCP test cases for the new tool
- **Modifying tool parameters**: Update test cases to reflect changes
- **Adding new services**: Add a new section with MCP test cases
- **Fixing bugs**: Add test case that covers the bug scenario
- **Finding good test data**: Update known test issues (like IGAL-1064)