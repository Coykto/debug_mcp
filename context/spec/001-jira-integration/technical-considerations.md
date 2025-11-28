# Technical Specification: Jira Ticket Search and Details

- **Functional Specification:** [functional-spec.md](./functional-spec.md)
- **Status:** Draft
- **Author(s):** Claude

---

## 1. High-Level Technical Approach

Add Jira Cloud integration to debug-mcp with two read-only tools for searching and viewing tickets. The implementation follows the established LangSmith pattern (Pattern B) with:

- **New module**: `src/debug_mcp/tools/jira.py` containing `JiraDebugger` class
- **Authentication**: CLI args for non-sensitive config + `JIRA_API_TOKEN` env var
- **SDK**: Official `jira` Python package for Jira Cloud REST API
- **Search**: Jira's native JQL search (no custom semantic search needed)
- **Registration**: Two tools added to `server.py` using `should_expose_tool()` pattern

**Systems affected:**
- `src/debug_mcp/__main__.py` - CLI argument parsing
- `src/debug_mcp/server.py` - Tool registration
- `src/debug_mcp/tools/jira.py` - New module
- `pyproject.toml` - New dependency
- `README.md` - Documentation update

---

## 2. Proposed Solution & Implementation Plan (The "How")

### 2.1 New Module: `src/debug_mcp/tools/jira.py`

Create a `JiraDebugger` class following the LangSmith pattern:

```python
"""Jira Cloud integration for debug-mcp."""

import os
from typing import Any

from jira import JIRA
from jira.exceptions import JIRAError
from pydantic import BaseModel


class JiraTicketSummary(BaseModel):
    """Summary view of a Jira ticket for search results."""
    key: str
    summary: str
    status: str
    assignee: str | None
    priority: str | None
    issue_type: str
    created: str
    updated: str


class JiraTicketDetails(BaseModel):
    """Full details of a Jira ticket."""
    key: str
    summary: str
    description: str | None
    status: str
    issue_type: str
    priority: str | None
    assignee: str | None
    reporter: str | None
    labels: list[str]
    created: str
    updated: str
    linked_issues: list[dict[str, str]]
    attachments: list[str]


class JiraDebugger:
    """Jira Cloud client for searching and retrieving ticket details."""

    def __init__(
        self,
        host: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        project: str | None = None,
    ):
        self._host = host
        self._email = email
        self._api_token = api_token
        self._project = project
        self._client: JIRA | None = None
        self._load_credentials()

    def _load_credentials(self) -> None:
        """Load credentials from environment variables if not provided."""
        if not self._host:
            self._host = os.getenv("JIRA_HOST")
        if not self._email:
            self._email = os.getenv("JIRA_EMAIL")
        if not self._api_token:
            self._api_token = os.getenv("JIRA_API_TOKEN")
        if not self._project:
            self._project = os.getenv("JIRA_PROJECT")

    @property
    def client(self) -> JIRA:
        """Lazy initialization of Jira client."""
        if self._client is None:
            if not all([self._host, self._email, self._api_token]):
                missing = []
                if not self._host:
                    missing.append("JIRA_HOST (or --jira-host)")
                if not self._email:
                    missing.append("JIRA_EMAIL (or --jira-email)")
                if not self._api_token:
                    missing.append("JIRA_API_TOKEN")
                raise ValueError(
                    f"Jira credentials not configured. Missing: {', '.join(missing)}"
                )
            self._client = JIRA(
                server=f"https://{self._host}",
                basic_auth=(self._email, self._api_token),
            )
        return self._client

    def search_tickets(
        self,
        query: str | None = None,
        issue_type: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        limit: int = 10,
    ) -> dict[str, Any]:
        """Search for Jira tickets using JQL."""
        # Validate at least one filter is provided
        if not any([query, issue_type, status, assignee]):
            return {
                "error": "At least one search parameter is required (query, issue_type, status, or assignee)"
            }

        # Build JQL query
        jql_parts = []
        if self._project:
            jql_parts.append(f'project = "{self._project}"')
        if query:
            # Use summary search for text matching
            jql_parts.append(f'summary ~ "{query}"')
        if issue_type:
            jql_parts.append(f'issuetype = "{issue_type}"')
        if status:
            jql_parts.append(f'status = "{status}"')
        if assignee:
            jql_parts.append(f'assignee = "{assignee}"')

        jql = " AND ".join(jql_parts) + " ORDER BY updated DESC"

        try:
            issues = self.client.search_issues(
                jql,
                maxResults=limit,
                fields="key,summary,status,assignee,priority,issuetype,created,updated",
            )

            results = []
            for issue in issues:
                ticket = JiraTicketSummary(
                    key=issue.key,
                    summary=issue.fields.summary,
                    status=str(issue.fields.status),
                    assignee=str(issue.fields.assignee) if issue.fields.assignee else None,
                    priority=str(issue.fields.priority) if issue.fields.priority else None,
                    issue_type=str(issue.fields.issuetype),
                    created=str(issue.fields.created),
                    updated=str(issue.fields.updated),
                )
                results.append(ticket.model_dump())

            return {"total": len(results), "results": results}

        except JIRAError as e:
            return {"error": f"Jira API error: {e.text}"}

    def get_ticket_details(self, issue_key: str) -> dict[str, Any]:
        """Get full details of a Jira ticket."""
        try:
            issue = self.client.issue(
                issue_key,
                fields="key,summary,description,status,issuetype,priority,"
                       "assignee,reporter,labels,created,updated,issuelinks,attachment",
            )

            # Extract linked issues
            linked_issues = []
            if hasattr(issue.fields, "issuelinks") and issue.fields.issuelinks:
                for link in issue.fields.issuelinks:
                    if hasattr(link, "outwardIssue"):
                        linked_issues.append({
                            "key": link.outwardIssue.key,
                            "type": link.type.outward,
                            "summary": link.outwardIssue.fields.summary,
                        })
                    elif hasattr(link, "inwardIssue"):
                        linked_issues.append({
                            "key": link.inwardIssue.key,
                            "type": link.type.inward,
                            "summary": link.inwardIssue.fields.summary,
                        })

            # Extract attachment filenames
            attachments = []
            if hasattr(issue.fields, "attachment") and issue.fields.attachment:
                attachments = [att.filename for att in issue.fields.attachment]

            # Extract labels
            labels = []
            if hasattr(issue.fields, "labels") and issue.fields.labels:
                labels = list(issue.fields.labels)

            ticket = JiraTicketDetails(
                key=issue.key,
                summary=issue.fields.summary,
                description=issue.fields.description,
                status=str(issue.fields.status),
                issue_type=str(issue.fields.issuetype),
                priority=str(issue.fields.priority) if issue.fields.priority else None,
                assignee=str(issue.fields.assignee) if issue.fields.assignee else None,
                reporter=str(issue.fields.reporter) if issue.fields.reporter else None,
                labels=labels,
                created=str(issue.fields.created),
                updated=str(issue.fields.updated),
                linked_issues=linked_issues,
                attachments=attachments,
            )

            return ticket.model_dump()

        except JIRAError as e:
            if "does not exist" in str(e.text).lower() or e.status_code == 404:
                return {"error": f"Issue {issue_key} not found"}
            if e.status_code == 403:
                return {"error": f"Permission denied: Cannot access issue {issue_key}"}
            return {"error": f"Jira API error: {e.text}"}
```

### 2.2 CLI Arguments: `src/debug_mcp/__main__.py`

Add Jira-specific arguments following the AWS pattern:

```python
# Add to argument parser
parser.add_argument(
    "--jira-host",
    default="",
    help="Jira Cloud hostname (e.g., company.atlassian.net)",
)
parser.add_argument(
    "--jira-email",
    default="",
    help="Jira user email for authentication",
)
parser.add_argument(
    "--jira-project",
    default="",
    help="Default Jira project key (e.g., IGAL)",
)

# Set environment variables (before importing server)
if args.jira_host:
    os.environ["JIRA_HOST"] = args.jira_host
if args.jira_email:
    os.environ["JIRA_EMAIL"] = args.jira_email
if args.jira_project:
    os.environ["JIRA_PROJECT"] = args.jira_project
```

### 2.3 Tool Registration: `src/debug_mcp/server.py`

Add Jira tools following the existing pattern:

```python
# Import
from debug_mcp.tools.jira import JiraDebugger

# Initialize at module level
jira_debugger = JiraDebugger()

# Add to DEFAULT_TOOLS
DEFAULT_TOOLS = (
    # ... existing tools ...
    # Jira (2 tools)
    "search_jira_tickets,"
    "get_jira_ticket"
)

# Tool registrations
if should_expose_tool("search_jira_tickets"):
    @mcp.tool()
    async def search_jira_tickets(
        query: str = "",
        issue_type: str = "",
        status: str = "",
        assignee: str = "",
        limit: int = 10,
    ) -> dict:
        """
        Search for Jira tickets with filters and text search.

        Args:
            query: Text to search for in ticket summaries
            issue_type: Filter by issue type (e.g., Bug, Story, Task)
            status: Filter by status (e.g., To Do, In Progress, Done)
            assignee: Filter by assignee (username or display name)
            limit: Maximum results to return (default: 10)

        Note: At least one parameter must be provided.
        """
        return jira_debugger.search_tickets(
            query=query if query else None,
            issue_type=issue_type if issue_type else None,
            status=status if status else None,
            assignee=assignee if assignee else None,
            limit=limit,
        )


if should_expose_tool("get_jira_ticket"):
    @mcp.tool()
    async def get_jira_ticket(issue_key: str) -> dict:
        """
        Get full details of a Jira ticket.

        Args:
            issue_key: The Jira issue key (e.g., IGAL-123)

        Returns details including summary, description, status, assignee,
        linked issues, and attachment filenames.
        """
        return jira_debugger.get_ticket_details(issue_key)
```

### 2.4 Dependencies: `pyproject.toml`

Add the Jira SDK:

```toml
dependencies = [
    # ... existing dependencies ...
    "jira>=3.5.0",
]
```

### 2.5 Documentation: `README.md`

Add Jira section to README:

**Configuration section:**
```markdown
### Jira Configuration

| Source | Name | Required | Description |
|--------|------|----------|-------------|
| CLI arg | `--jira-host` | Yes | Jira Cloud hostname (e.g., `company.atlassian.net`) |
| CLI arg | `--jira-email` | Yes | Atlassian account email |
| CLI arg | `--jira-project` | Yes | Default Jira project key |
| Env var | `JIRA_API_TOKEN` | Yes | [Jira API token](https://id.atlassian.com/manage-profile/security/api-tokens) |
```

**Tools section:**
```markdown
### Jira Tools (2 tools)
- `search_jira_tickets` - Search tickets with filters (type, status, assignee) and text search
- `get_jira_ticket` - Get full ticket details including linked issues and attachments
```

**Example configuration:**
```markdown
### Example: Claude Code with Jira

```bash
claude mcp add --scope user --transport stdio debug-mcp \
    -- uvx --from git+https://github.com/Coykto/debug_mcp debug-mcp \
    --aws-region us-west-2 \
    --jira-host yourcompany.atlassian.net \
    --jira-email your.email@company.com \
    --jira-project PROJ
```

Ensure `JIRA_API_TOKEN` is set in your environment.
```

---

## 3. Impact and Risk Analysis

### System Dependencies

| Dependency | Impact |
|------------|--------|
| Jira Cloud API | External service - requires network access and valid credentials |
| `jira` Python package | New dependency (~3.5.0) |
| Existing tool infrastructure | Minimal - follows established patterns |

### Potential Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Invalid credentials** | Medium | Tool errors | Clear error messages listing missing credentials |
| **Rate limiting** | Low | Slow/failed requests | Jira Cloud has generous limits; no special handling needed initially |
| **Large result sets** | Low | Performance | Default limit of 10; max handled by Jira API |
| **Network failures** | Low | Tool errors | Jira SDK handles retries; errors surfaced clearly |
| **Permission issues** | Medium | Partial data | Clear error messages for 403 responses |

### Security Considerations

- **API token in environment**: Token never passed as CLI arg, never logged
- **Credentials validation**: Lazy client init means errors only on first use
- **Read-only operations**: No risk of data modification

---

## 4. Testing Strategy

### Unit Tests

Create `tests/test_jira.py`:

1. **Credential loading tests**
   - Test loading from environment variables
   - Test error messages when credentials missing
   - Test CLI arg override of env vars

2. **JQL building tests**
   - Test query generation with various filter combinations
   - Test empty query validation
   - Test escaping of special characters in search terms

3. **Response formatting tests**
   - Test `JiraTicketSummary` model validation
   - Test `JiraTicketDetails` model validation
   - Test linked issues extraction
   - Test attachment filename extraction

4. **Error handling tests**
   - Test 404 (issue not found) handling
   - Test 403 (permission denied) handling
   - Test generic Jira API error handling

### Integration Tests (Manual)

Test against real Jira Cloud instance:

1. **Search tool**
   - Search by text query
   - Search by status filter
   - Search by assignee filter
   - Combined filters
   - Empty results handling

2. **Details tool**
   - Get ticket with all fields populated
   - Get ticket with minimal fields
   - Get ticket with linked issues
   - Get ticket with attachments
   - Invalid issue key

### Local Testing Setup

```json
{
  "mcpServers": {
    "debug-mcp-local": {
      "command": "uv",
      "args": [
        "run", "debug-mcp",
        "--jira-host", "provectus-dev.atlassian.net",
        "--jira-email", "your.email@company.com",
        "--jira-project", "IGAL"
      ],
      "cwd": "/path/to/debug_mcp"
    }
  }
}
```

---

## 5. Implementation Checklist

- [ ] Add `jira>=3.5.0` to `pyproject.toml`
- [ ] Create `src/debug_mcp/tools/jira.py` with `JiraDebugger` class
- [ ] Update `src/debug_mcp/__main__.py` with Jira CLI arguments
- [ ] Update `src/debug_mcp/server.py` with tool registrations
- [ ] Update `DEFAULT_TOOLS` to include Jira tools
- [ ] Update `README.md` with Jira configuration and tools
- [ ] Create `tests/test_jira.py` with unit tests
- [ ] Manual integration testing with real Jira instance