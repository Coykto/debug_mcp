---
title: Test MCP Server Tools
description: Verify that all MCP server tools are working correctly
tags: [testing, verification]
---

# Test MCP Server Tools

This command provides a comprehensive test suite to verify all MCP server tools are working correctly.

## Test Checklist

### 1. AWS CloudWatch Logs Tools (5 tools)
Requires: `AWS_REGION` environment variable

- [ ] `describe_log_groups()` - List all log groups
- [ ] `analyze_log_group()` - Analyze logs (need log group name and time range)
- [ ] `execute_log_insights_query()` - Execute insights query
- [ ] `get_logs_insight_query_results()` - Get query results
- [ ] `cancel_logs_insight_query()` - Cancel a query

**Quick Test:**
```python
# List log groups with Lambda prefix
await describe_log_groups(log_group_name_prefix="/aws/lambda/")
```

### 2. AWS Step Functions Tools (5 tools)
Requires: `AWS_REGION` environment variable

- [ ] `list_state_machines()` - List all state machines
- [ ] `get_state_machine_definition()` - Get state machine ASL
- [ ] `list_step_function_executions()` - List executions
- [ ] `get_step_function_execution_details()` - Get execution details
- [ ] `search_step_function_executions()` - Search executions

**Quick Test:**
```python
# List state machines
await list_state_machines(max_results=10)
```

### 3. LangSmith Tools (6 tools)
Requires: `LANGCHAIN_API_KEY` or `AWS_REGION` (for secrets)

- [ ] `list_langsmith_projects()` - List projects
- [ ] `list_langsmith_runs()` - List runs/traces
- [ ] `get_langsmith_run_details()` - Get run details
- [ ] `search_langsmith_runs()` - Search runs by content
- [ ] `search_run_content()` - Search within a run
- [ ] `get_run_field()` - Get specific field from run

**Quick Test:**
```python
# List projects in local environment
await list_langsmith_projects(environment="local", limit=10)
```

### 4. Jira Tools (2 tools)
Requires: `JIRA_HOST`, `JIRA_EMAIL`, `JIRA_API_TOKEN`

- [ ] `get_jira_ticket()` - Get ticket details
- [ ] `search_jira_tickets()` - Search for tickets

**Quick Test:**
```python
# Search for tickets
await search_jira_tickets(query="bug", limit=5)
```

## Automated Test Commands

Run these to verify each service:

### Test AWS Tools (if AWS_REGION is set)
```bash
# Test CloudWatch
python -c "from debug_mcp.tools.cloudwatch_logs import CloudWatchLogsTools; import asyncio; tools = CloudWatchLogsTools(aws_region='us-east-1'); print(asyncio.run(tools.describe_log_groups()))"

# Test Step Functions
python -c "from debug_mcp.tools.stepfunctions import StepFunctionsDebugger; debugger = StepFunctionsDebugger(); print(debugger.list_state_machines(max_results=5))"
```

### Test LangSmith Tools (if configured)
```bash
python -c "from debug_mcp.tools.langsmith import get_langsmith_debugger; debugger = get_langsmith_debugger('local'); print(debugger.list_projects(limit=5))"
```

### Test Jira Tools (if configured)
```bash
python -c "from debug_mcp.tools.jira import JiraDebugger; debugger = JiraDebugger(); print(debugger.search_tickets(limit=5))"
```

## Expected Behavior

### When Credentials ARE Configured
- Tools should be registered and visible in MCP server
- Tool calls should execute successfully
- Should return proper data or meaningful errors

### When Credentials ARE NOT Configured
- Tools should NOT be registered
- Tools should NOT appear in `list_tools()` response
- No errors should occur on server startup

## Verification Steps

1. **Check server starts without errors:**
   ```bash
   uv run debug-mcp
   ```

2. **List available tools:**
   Use MCP inspector or check tool list to verify only configured tools are exposed

3. **Test each tool category:**
   - AWS: Set `AWS_REGION`, verify AWS tools appear
   - LangSmith: Set `LANGCHAIN_API_KEY` or AWS credentials, verify LangSmith tools appear
   - Jira: Set `JIRA_*` vars, verify Jira tools appear

4. **Test missing credentials:**
   - Unset credentials, verify tools do NOT appear
   - Server should start successfully with 0 tools if no credentials

## Common Issues

### AWS Tools Not Appearing
- Check: `echo $AWS_REGION` - must be set
- Check: AWS credentials are valid (via `aws sts get-caller-identity`)

### LangSmith Tools Not Appearing
- Check: `echo $LANGCHAIN_API_KEY` OR `echo $AWS_REGION`
- Verify secrets in AWS Secrets Manager if using AWS

### Jira Tools Not Appearing
- Check: All three env vars set: `JIRA_HOST`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
