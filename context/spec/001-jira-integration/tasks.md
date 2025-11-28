# Tasks: Jira Ticket Search and Details

- **Functional Spec:** [functional-spec.md](./functional-spec.md)
- **Technical Spec:** [technical-considerations.md](./technical-considerations.md)

---

## Slice 1: Get Jira Ticket Details (Minimal End-to-End)

- [x] **Slice 1: Implement `get_jira_ticket` tool - simplest path to working Jira connection**
  - [x] Add `jira>=3.5.0` dependency to `pyproject.toml` and run `uv sync`
  - [x] Create `src/debug_mcp/tools/jira.py` with:
    - `JiraDebugger` class with credential loading from env vars
    - Lazy `client` property for Jira connection
    - `get_ticket_details()` method (returns basic fields: key, summary, description, status, type, priority, assignee, reporter, labels, created, updated)
    - Pydantic model `JiraTicketDetails` for validation
  - [x] Update `src/debug_mcp/__main__.py`:
    - Add `--jira-host`, `--jira-email`, `--jira-project` CLI arguments
    - Set corresponding `JIRA_HOST`, `JIRA_EMAIL`, `JIRA_PROJECT` env vars
  - [x] Update `src/debug_mcp/server.py`:
    - Import `JiraDebugger`
    - Initialize `jira_debugger` at module level
    - Add `"get_jira_ticket"` to `DEFAULT_TOOLS`
    - Register `get_jira_ticket` tool with `@mcp.tool()` decorator
  - [x] **VERIFY**: Run MCP server locally and test `get_jira_ticket`:
    ```bash
    # Start the server
    JIRA_API_TOKEN=<your-token> uv run debug-mcp \
      --jira-host provectus-dev.atlassian.net \
      --jira-email <your-email> \
      --jira-project IGAL

    # In Claude Code, call the tool with a known ticket (e.g., IGAL-1)
    # Verify output contains: key, summary, description, status, type, etc.
    ```

---

## Slice 2: Add Linked Issues and Attachments to Details

- [x] **Slice 2: Enhance `get_jira_ticket` with linked issues and attachments**
  - [x] Add linked issues extraction to `get_ticket_details()`:
    - Parse `issuelinks` field
    - Return list of `{key, type, summary}` for each linked issue
  - [x] Add attachment filenames extraction:
    - Parse `attachment` field
    - Return list of filenames only
  - [x] Add error handling for 404 (not found) and 403 (permission denied)
  - [x] **VERIFY**: Run MCP server and test:
    ```bash
    # Test with a ticket that has linked issues
    # Test with a ticket that has attachments
    # Test with an invalid issue key (should return clear error)
    # Test Epic with children (epic_children field)
    # Test subtask (parent field)
    ```

---

## Slice 3: Search Jira Tickets

- [x] **Slice 3: Implement `search_jira_tickets` tool**
  - [x] Add `JiraTicketSummary` Pydantic model to `jira.py`
  - [x] Implement `search_tickets()` method in `JiraDebugger`:
    - Build JQL query from parameters (query, issue_type, status, assignee)
    - Validate at least one parameter is provided
    - Return `{total, results}` with list of ticket summaries
  - [x] Update `server.py`:
    - Add `"search_jira_tickets"` to `DEFAULT_TOOLS`
    - Register `search_jira_tickets` tool with all parameters
  - [x] **VERIFY**: Run MCP server and test various searches:
    ```bash
    # Test: search by text query - PASSED
    search_jira_tickets(query="graph")

    # Test: search by status - PASSED
    search_jira_tickets(status="To Do")

    # Test: search by assignee - PASSED
    search_jira_tickets(assignee="Evgenii Basmov")

    # Test: no parameters (should return clear error) - PASSED
    search_jira_tickets()
    ```

---

## Slice 4: Documentation

- [x] **Slice 4: Update README.md with Jira documentation**
  - [x] Add "Jira Configuration" section with CLI args and env var table
  - [x] Add "Jira Tools (2 tools)" to the tools list section
  - [x] Add example Claude Code configuration with Jira parameters
  - [x] **VERIFY**: Review README renders correctly (check markdown formatting)


