# Functional Specification: Tool Discovery Gateway

- **Roadmap Item:** Implement tool discovery pattern to reduce context token usage
- **Status:** Draft
- **Author:** Claude (with user input)

---

## 1. Overview and Rationale (The "Why")

### Problem Statement

debug-mcp currently exposes 17 tools by default, consuming ~13K tokens of context. This bloats Claude's context window even when the user doesn't need debugging capabilities, reducing effectiveness on other tasks.

### Desired Outcome

Replace all individual tool exports with a single gateway tool (`debug`) that can:
1. **Discover** available debugging tools and their schemas on-demand
2. **Execute** any debugging tool without requiring restart or reconfiguration

### Success Metrics

- Context usage reduced from ~13K tokens to ~500 tokens (~95% reduction)
- All existing debugging functionality remains accessible
- No restart or reconfiguration required to use any tool
- Claude can discover and use appropriate tools within a single session

---

## 2. Functional Requirements (The "What")

### Tool: `debug`

**As a** developer using Claude Code, **I want to** access debugging tools through a single gateway, **so that** my context isn't bloated when I'm not debugging, but I can instantly debug when needed.

#### Input Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `tool` | No | `"list"` | Tool name to execute, or `"list"` / `"list:<category>"` for discovery |
| `arguments` | No | `"{}"` | JSON string of arguments for the tool |

**Categories:** `cloudwatch`, `stepfunctions`, `langsmith`, `jira`

#### Discovery Mode Acceptance Criteria

- [ ] `debug()` or `debug(tool="list")` returns all categories with brief descriptions
- [ ] `debug(tool="list:cloudwatch")` returns CloudWatch tools with full argument schemas
- [ ] `debug(tool="list:stepfunctions")` returns Step Functions tools with full argument schemas
- [ ] `debug(tool="list:langsmith")` returns LangSmith tools with full argument schemas
- [ ] `debug(tool="list:jira")` returns Jira tools with full argument schemas
- [ ] Each tool listing includes: name, description, required arguments, optional arguments with defaults

#### Execution Mode Acceptance Criteria

- [ ] `debug(tool="<tool_name>", arguments='<json>')` executes the tool and returns results
- [ ] If required arguments are missing, returns clear error with the expected schema
- [ ] If tool name is invalid, returns error listing similar/available tools
- [ ] All existing tool functionality is preserved (just accessed through gateway)

#### Error Handling Acceptance Criteria

- [ ] Invalid JSON in `arguments` returns parse error with guidance
- [ ] Missing credentials (AWS, Jira, LangSmith) returns clear configuration instructions
- [ ] Tool-specific errors are passed through with context

---

### Removal: `DEBUG_MCP_TOOLS` Environment Variable

**As a** maintainer, **I want to** remove the `DEBUG_MCP_TOOLS` filtering mechanism, **so that** the codebase is simpler and the gateway pattern is the single way to access tools.

#### Acceptance Criteria

- [ ] `DEBUG_MCP_TOOLS` environment variable is no longer read or used
- [ ] `DEFAULT_TOOLS` constant is removed
- [ ] `should_expose_tool()` function is removed
- [ ] All individual `@mcp.tool()` decorated functions are removed from `server.py`
- [ ] Documentation (README, CLAUDE.md) updated to reflect new pattern

---

## 3. Scope and Boundaries

### In-Scope

- New `debug` gateway tool with list and execute modes
- Category-based tool discovery with full argument schemas
- JSON argument passing for tool execution
- Removal of `DEBUG_MCP_TOOLS` environment variable and related code
- Removal of individual tool exports (all accessed via gateway)
- Documentation updates

### Out-of-Scope

- Changes to underlying tool implementations (`cloudwatch_logs.py`, `stepfunctions.py`, `langsmith.py`, `jira.py`)
- New debugging capabilities
- Other MCP server integrations (CloudWatch, Step Functions, LangSmith, Jira implementations unchanged)
