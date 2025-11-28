# MCP Tool Verification Tests

**Purpose:** This file contains test calls to verify all MCP tools are working correctly. Agents should run these tests after implementing or modifying tools.

**Important:** 
- All credentials are assumed to be correctly configured
- If a tool fails or isn't exposed, it's a credentials/configuration issue
- Keep this list updated when adding/modifying tools

---

## CloudWatch Logs Tools (5 tools)
Requires: `AWS_REGION`

### describe_log_groups
```python
# List Lambda log groups
describe_log_groups(log_group_name_prefix="/aws/lambda/")

# List all log groups (no filter)
describe_log_groups()
```

### analyze_log_group
```python
# Analyze a specific log group (adjust log group name as needed)
analyze_log_group(log_group_name="/aws/lambda/your-function", hours=1)
```

### execute_log_insights_query
```python
# Run a simple query
execute_log_insights_query(
    log_group_names=["/aws/lambda/your-function"],
    query="fields @timestamp, @message | sort @timestamp desc | limit 20",
    hours=1
)
```

### get_logs_insight_query_results
```python
# Get results for a query (need query_id from execute_log_insights_query)
get_logs_insight_query_results(query_id="your-query-id")
```

### cancel_logs_insight_query
```python
# Cancel a running query
cancel_logs_insight_query(query_id="your-query-id")
```

---

## Step Functions Tools (5 tools)
Requires: `AWS_REGION`

### list_state_machines
```python
# List all state machines
list_state_machines(max_results=10)
```

### get_state_machine_definition
```python
# Get definition (need ARN from list_state_machines)
get_state_machine_definition(state_machine_arn="arn:aws:states:...")
```

### list_step_function_executions
```python
# List executions for a state machine
list_step_function_executions(state_machine_arn="arn:aws:states:...", max_results=10)

# List only failed executions
list_step_function_executions(state_machine_arn="arn:aws:states:...", status_filter="FAILED")
```

### get_step_function_execution_details
```python
# Get execution details (need execution ARN)
get_step_function_execution_details(execution_arn="arn:aws:states:...execution...")

# With workflow definition included
get_step_function_execution_details(execution_arn="arn:aws:states:...", include_definition=True)
```

### search_step_function_executions
```python
# Search executions by pattern
search_step_function_executions(
    state_machine_arn="arn:aws:states:...",
    search_pattern="error",
    max_results=10
)
```

---

## LangSmith Tools (6 tools)
Requires: `LANGCHAIN_API_KEY` or `AWS_REGION` (for Secrets Manager)

### list_langsmith_projects
```python
# List projects in local environment
list_langsmith_projects(environment="local", limit=10)

# List projects in prod
list_langsmith_projects(environment="prod", limit=10)
```

### list_langsmith_runs
```python
# List recent runs
list_langsmith_runs(environment="local", project_name="your-project", limit=10)

# List only errored runs
list_langsmith_runs(environment="local", project_name="your-project", is_error=True)
```

### get_langsmith_run_details
```python
# Get run details (need run_id from list_langsmith_runs)
get_langsmith_run_details(environment="local", run_id="your-run-id")
```

### search_langsmith_runs
```python
# Search for runs containing specific text
search_langsmith_runs(environment="local", project_name="your-project", query="error message")
```

### search_run_content
```python
# Search within a stored run (after calling get_langsmith_run_details)
search_run_content(reference_id="your-run-id", query="specific content")
```

### get_run_field
```python
# Get specific field from stored run
get_run_field(reference_id="your-run-id", field_path="outputs.result")
```

---

## Jira Tools (2 tools)
Requires: `JIRA_HOST`, `JIRA_EMAIL`, `JIRA_API_TOKEN`

### search_jira_tickets
```python
# Search by text query
search_jira_tickets(query="bug", limit=5)

# Search by status
search_jira_tickets(status="To Do", limit=5)

# Search by assignee
search_jira_tickets(assignee="Your Name", limit=5)

# Search by issue type
search_jira_tickets(issue_type="Bug", limit=5)

# Combined filters
search_jira_tickets(query="login", status="In Progress", limit=5)

# No parameters (should return error)
search_jira_tickets()
```

### get_jira_ticket
```python
# Get ticket details
get_jira_ticket(issue_key="PROJ-123")

# Test with Epic (should show epic_children)
get_jira_ticket(issue_key="PROJ-100")  # Use a known Epic

# Test with subtask (should show parent)
get_jira_ticket(issue_key="PROJ-101")  # Use a known subtask

# Test invalid ticket (should return error)
get_jira_ticket(issue_key="INVALID-99999")
```

---

## Quick Verification Script

Run this Python script to verify basic connectivity for each service:

```python
import os
import json

# Test AWS (CloudWatch)
if os.getenv("AWS_REGION"):
    from debug_mcp.tools.cloudwatch_logs import CloudWatchLogsTools
    cw = CloudWatchLogsTools()
    result = cw.describe_log_groups(log_group_name_prefix="/aws/lambda/")
    print(f"CloudWatch: {len(result.get('log_groups', []))} log groups found")

# Test AWS (Step Functions)
if os.getenv("AWS_REGION"):
    from debug_mcp.tools.stepfunctions import StepFunctionsDebugger
    sfn = StepFunctionsDebugger()
    result = sfn.list_state_machines(max_results=5)
    print(f"Step Functions: {len(result)} state machines found")

# Test Jira
if os.getenv("JIRA_HOST") and os.getenv("JIRA_EMAIL") and os.getenv("JIRA_API_TOKEN"):
    from debug_mcp.tools.jira import JiraDebugger
    jira = JiraDebugger()
    result = jira.search_tickets(status="To Do", limit=5)
    print(f"Jira: {result.get('total', 0)} tickets found")

# Test LangSmith
if os.getenv("LANGCHAIN_API_KEY"):
    from debug_mcp.tools.langsmith import get_langsmith_debugger
    ls = get_langsmith_debugger("local")
    result = ls.list_projects(limit=5)
    print(f"LangSmith: {len(result)} projects found")
```

---

## When to Update This File

- **Adding new tools**: Add test cases for the new tool
- **Modifying tool parameters**: Update test cases to reflect changes
- **Adding new services**: Add a new section with test cases
- **Fixing bugs**: Add test case that covers the bug scenario
