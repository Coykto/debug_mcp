# Tasks: Tool Discovery Gateway

## Slice 1: Gateway with Discovery Mode (No Execution)
Create the basic infrastructure and verify the gateway tool appears in MCP with discovery working.

- [x] **Slice 1: Basic gateway with category discovery**
  - [x] Create `src/debug_mcp/registry.py` with core classes:
    - `ToolParameter` (Pydantic model)
    - `ToolSchema` (Pydantic model)
    - `ToolRegistryEntry` (dataclass)
    - `ToolRegistry` class with `list_categories()` and `list_tools(category)` methods
  - [x] Add category definitions with brief descriptions (cloudwatch, stepfunctions, langsmith, jira)
  - [x] Create `debug()` gateway function in `server.py` (discovery mode only)
  - [x] **Test:** MCP server starts, `debug(tool="list")` returns 4 categories

---

## Slice 2: First Executable Tool (CloudWatch)
Add execution capability with one tool to validate the full flow.

- [x] **Slice 2: Execute `describe_log_groups` via gateway**
  - [x] Add `DescribeLogGroupsArgs` Pydantic model
  - [x] Create `@debug_tool()` decorator for registration
  - [x] Register `describe_log_groups` with schema and handler
  - [x] Add `execute()` method to `ToolRegistry`
  - [x] Update `debug()` gateway to handle execution mode
  - [x] **Test:** `debug(tool="describe_log_groups", arguments='{}')` returns log groups

---

## Slice 3: Complete CloudWatch Category
Add remaining CloudWatch tools.

- [x] **Slice 3: All CloudWatch tools via gateway**
  - [x] Add `AnalyzeLogGroupArgs` model and register `analyze_log_group`
  - [x] Add `ExecuteLogInsightsQueryArgs` model and register `execute_log_insights_query`
  - [x] Add `GetLogsInsightQueryResultsArgs` model and register `get_logs_insight_query_results`
  - [x] **Test:** `debug(tool="list:cloudwatch")` shows 4 tools, all execute correctly

---

## Slice 4: Step Functions Category
Add all Step Functions tools.

- [x] **Slice 4: All Step Functions tools via gateway**
  - [x] Add Pydantic models for 5 Step Functions tools
  - [x] Register all Step Functions handlers with schemas
  - [x] **Test:** `debug(tool="list:stepfunctions")` shows 5 tools, all execute correctly

---

## Slice 5: LangSmith Category
Add all LangSmith tools.

- [x] **Slice 5: All LangSmith tools via gateway**
  - [x] Add Pydantic models for 6 LangSmith tools
  - [x] Register all LangSmith handlers with schemas
  - [x] Move `_extract_run_summary()` helper to registry
  - [x] **Test:** `debug(tool="list:langsmith")` shows 6 tools, all execute correctly

---

## Slice 6: Jira Category
Add all Jira tools.

- [x] **Slice 6: All Jira tools via gateway**
  - [x] Add Pydantic models for 2 Jira tools
  - [x] Register all Jira handlers with schemas
  - [x] **Test:** `debug(tool="list:jira")` shows 2 tools, all execute correctly

---

## Slice 7: Cleanup Legacy Code
Remove old code now that gateway handles everything.

- [x] **Slice 7: Remove legacy tool exports and config**
  - [x] Remove `DEFAULT_TOOLS` constant from `server.py`
  - [x] Remove `configured_tools_str` / `configured_tools` variables
  - [x] Remove `should_expose_tool()` function
  - [x] Remove `is_jira_configured()`, `is_aws_configured()`, `is_langsmith_configured()` (move checks to registry if needed)
  - [x] Remove all 17 individual `@mcp.tool()` decorated functions
  - [x] **Test:** MCP server starts with only `debug` tool visible

---

## Slice 8: Documentation Updates
Update docs to reflect new pattern.

- [x] **Slice 8: Update documentation**
  - [x] Update `README.md`:
    - Remove `DEBUG_MCP_TOOLS` documentation
    - Add new usage pattern with `debug()` gateway
    - Update examples
  - [x] Update `CLAUDE.md`:
    - Remove tool filtering section
    - Update architecture description
  - [x] Update `tool-verification-tests` memory with new test patterns
  - [x] **Test:** Documentation accurately describes current behavior
