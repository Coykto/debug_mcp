"""Registry for Jira tools - registers directly with FastMCP."""

from fastmcp import FastMCP

from .jira import JiraDebugger


def register_tools(mcp: FastMCP) -> None:
    """Register Jira tools with the MCP server."""
    jira_debugger = JiraDebugger()

    @mcp.tool()
    async def get_jira_ticket(issue_key: str) -> dict:
        """Get full details of a Jira ticket by issue key.

        Args:
            issue_key: The Jira issue key (e.g., IGAL-123)
        """
        return jira_debugger.get_ticket_details(issue_key)

    @mcp.tool()
    async def search_jira_tickets(
        query: str = "",
        issue_type: str = "",
        status: str = "",
        assignee: str = "",
        limit: int = 10,
    ) -> dict:
        """Search for Jira tickets with filters and text search.

        Args:
            query: Text to search for in ticket summaries
            issue_type: Filter by issue type (e.g., Bug, Story, Task, Epic)
            status: Filter by status (e.g., To Do, In Progress, Done)
            assignee: Filter by assignee (username or display name)
            limit: Maximum results to return (default: 10)
        """
        return jira_debugger.search_tickets(
            query=query if query else None,
            issue_type=issue_type if issue_type else None,
            status=status if status else None,
            assignee=assignee if assignee else None,
            limit=limit,
        )
