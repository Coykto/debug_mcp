# Functional Specification: Jira Ticket Search and Details

- **Roadmap Item:** Add Jira integration with search and ticket details tools
- **Status:** Approved
- **Author:** Claude (with user input)

---

## 1. Overview and Rationale (The "Why")

### Problem Statement

Developers debugging distributed systems frequently need to reference Jira tickets to understand requirements, acceptance criteria, bug reports, or identify patterns across related issues. Currently, this requires context-switching between the terminal/IDE and the Jira web interface, breaking the debugging flow.

### Desired Outcome

Integrate Jira into debug-mcp so developers can:
1. **Search for tickets** directly from Claude Code using filters and semantic search - finding relevant tickets without remembering exact issue numbers
2. **Get full ticket details** for a known issue number - pulling requirements, descriptions, and linked issues into the debugging context

### Success Metrics

- Users can find relevant Jira tickets without leaving their terminal
- Users can retrieve ticket details (including linked issues) with a single command
- Search returns relevant results even with partial or fuzzy queries

---

## 2. Functional Requirements (The "What")

### Tool 1: Search Jira Tickets (`search_jira_tickets`)

**As a** developer, **I want to** search for Jira tickets using filters and text search, **so that** I can quickly find relevant issues without leaving my terminal.

#### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `query` | No | Text to search for (semantic/fuzzy match against ticket summaries) |
| `issue_type` | No | Filter by issue type (discovered dynamically from project) |
| `status` | No | Filter by status (discovered dynamically from project) |
| `assignee` | No | Filter by assignee (username or display name) |
| `limit` | No | Maximum results to return (default: 10) |

**Note:** At least one of `query`, `issue_type`, `status`, or `assignee` must be provided.

#### Acceptance Criteria

- [ ] When I provide a `query`, the tool returns tickets whose summaries semantically match the query text
- [ ] When I provide `issue_type`, only tickets of that type are returned (e.g., "Bug", "Story", "Task")
- [ ] When I provide `status`, only tickets with that status are returned (e.g., "To Do", "In Progress", "Done")
- [ ] When I provide `assignee`, only tickets assigned to that person are returned
- [ ] Filters can be combined (e.g., `query="login error"` + `status="In Progress"`)
- [ ] Results are ranked by relevance to the search query
- [ ] Results are limited to the `limit` parameter (default 10)
- [ ] Each result includes: **key**, **summary**, **status**, **assignee**, **priority**, **type**, **created date**, **updated date**
- [ ] If no results match, the tool returns an empty list with a clear message
- [ ] If the Jira project is inaccessible or credentials are invalid, a clear error message is returned

#### Dynamic Discovery

- [ ] Available `issue_type` values are discovered from the Jira project configuration
- [ ] Available `status` values are discovered from the Jira project workflow

---

### Tool 2: Get Jira Ticket Details (`get_jira_ticket`)

**As a** developer, **I want to** retrieve full details of a Jira ticket by its issue key, **so that** I can understand the requirements, context, and related issues while debugging.

#### Input Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `issue_key` | Yes | The Jira issue key (e.g., "IGAL-123") |

#### Acceptance Criteria

- [ ] When I provide a valid `issue_key`, the tool returns the full ticket details
- [ ] Returned details include:
  - **Key** (e.g., "IGAL-123")
  - **Summary** (title)
  - **Description** (full text)
  - **Status**
  - **Issue type**
  - **Priority**
  - **Assignee** (display name)
  - **Reporter** (display name)
  - **Labels** (list)
  - **Created date**
  - **Updated date**
  - **Linked issues** (list with issue key, link type, and summary for each)
  - **Attachments** (list of filenames only)
- [ ] If the issue key does not exist, a clear error message is returned: "Issue [KEY] not found"
- [ ] If the user lacks permission to view the issue, a clear error message is returned

---

### Authentication Configuration

**As a** user, **I want to** configure Jira credentials via CLI arguments and environment variables, **so that** authentication follows the same pattern as AWS credentials.

#### Configuration

| Source | Name | Required | Description |
|--------|------|----------|-------------|
| CLI arg | `--jira-host` | Yes | Jira Cloud hostname (e.g., `provectus-dev.atlassian.net`) |
| CLI arg | `--jira-email` | Yes | Atlassian account email |
| CLI arg | `--jira-project` | Yes | Default Jira project key (e.g., `IGAL`) |
| Env var | `JIRA_API_TOKEN` | Yes | [Jira API token](https://id.atlassian.com/manage-profile/security/api-tokens) |

#### Acceptance Criteria

- [ ] CLI arguments are parsed in `__main__.py` and set as environment variables (following AWS pattern)
- [ ] `JIRA_API_TOKEN` is read from the environment (not passed as CLI argument for security)
- [ ] If Jira tools are called without required credentials configured, a clear error message is returned
- [ ] Credentials are never logged or exposed in error messages

---

## 3. Scope and Boundaries

### In-Scope

- Search Jira tickets with filters (type, status, assignee) and semantic text search on summaries
- Get full ticket details including linked issues and attachment filenames
- Dynamic discovery of issue types and statuses from project configuration
- Jira Cloud authentication via API token (basic auth)
- CLI argument-based credential configuration (host, email, project)
- Environment variable for API token (`JIRA_API_TOKEN`)

### Out-of-Scope

- **Comments retrieval** - May be added in future iteration
- **Attachment content retrieval** - Only filenames are listed
- **Creating, updating, or transitioning tickets** - Read-only tools only
- **Jira Server/Data Center support** - Jira Cloud only
- **Multi-project search** - Search is scoped to the configured `--jira-project`
- **Watching/subscribing to tickets**
- **Sprint or board-level operations**
- **Other debug-mcp tools** (CloudWatch, Step Functions, LangSmith)