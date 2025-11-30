"""Registry for Jira tools using the @debug_tool decorator."""

import os

from pydantic import BaseModel, Field

from ..registry import ToolParameter, debug_tool
from .jira import JiraDebugger


class GetJiraTicketArgs(BaseModel):
    """Arguments for get_jira_ticket tool."""

    issue_key: str = Field(description="The Jira issue key (e.g., IGAL-123)")


class SearchJiraTicketsArgs(BaseModel):
    """Arguments for search_jira_tickets tool."""

    query: str = Field(default="", description="Text to search for in ticket summaries")
    issue_type: str = Field(default="", description="Filter by issue type (e.g., Bug, Story, Task, Epic)")
    status: str = Field(default="", description="Filter by status (e.g., To Do, In Progress, Done)")
    assignee: str = Field(default="", description="Filter by assignee (username or display name)")
    limit: int = Field(default=10, description="Maximum results to return (default: 10)")


def is_jira_configured() -> bool:
    """Check if Jira credentials are configured."""
    return bool(os.getenv("JIRA_HOST") and os.getenv("JIRA_EMAIL") and os.getenv("JIRA_API_TOKEN"))


# Initialize Jira debugger only if credentials are configured
_jira_debugger: JiraDebugger | None = None
if is_jira_configured():
    _jira_debugger = JiraDebugger()


# Register get_jira_ticket tool
if is_jira_configured():

    @debug_tool(
        name="get_jira_ticket",
        description="Get full details of a Jira ticket by issue key",
        category="jira",
        parameters=[
            ToolParameter(
                name="issue_key",
                type="string",
                description="The Jira issue key (e.g., IGAL-123)",
                required=True,
            ),
        ],
        arg_model=GetJiraTicketArgs,
    )
    async def get_jira_ticket_registry(issue_key: str) -> dict:
        """Get full details of a Jira ticket.

        Returns details including summary, description, status, assignee,
        reporter, labels, created and updated dates.
        """
        return _jira_debugger.get_ticket_details(issue_key)


# Register search_jira_tickets tool
if is_jira_configured():

    @debug_tool(
        name="search_jira_tickets",
        description="Search for Jira tickets with filters and text search",
        category="jira",
        parameters=[
            ToolParameter(
                name="query",
                type="string",
                description="Text to search for in ticket summaries",
                required=False,
                default="",
            ),
            ToolParameter(
                name="issue_type",
                type="string",
                description="Filter by issue type (e.g., Bug, Story, Task, Epic)",
                required=False,
                default="",
            ),
            ToolParameter(
                name="status",
                type="string",
                description="Filter by status (e.g., To Do, In Progress, Done)",
                required=False,
                default="",
            ),
            ToolParameter(
                name="assignee",
                type="string",
                description="Filter by assignee (username or display name)",
                required=False,
                default="",
            ),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum results to return (default: 10)",
                required=False,
                default=10,
            ),
        ],
        arg_model=SearchJiraTicketsArgs,
    )
    async def search_jira_tickets_registry(
        query: str = "",
        issue_type: str = "",
        status: str = "",
        assignee: str = "",
        limit: int = 10,
    ) -> dict:
        """Search for Jira tickets with filters and text search.

        Note: At least one parameter must be provided.
        """
        return _jira_debugger.search_tickets(
            query=query if query else None,
            issue_type=issue_type if issue_type else None,
            status=status if status else None,
            assignee=assignee if assignee else None,
            limit=limit,
        )
