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
    linked_issues: list[dict[str, str]]  # list of {key, type, summary}
    attachments: list[str]  # list of filenames
    parent: dict[str, str] | None  # {key, summary} if this is a subtask or Epic child
    subtasks: list[dict[str, str]]  # list of {key, summary, status} for subtasks
    epic_children: list[dict[str, str]]  # list of {key, summary, status} for issues in this Epic


class JiraDebugger:
    """Jira Cloud client for searching and retrieving ticket details."""

    def __init__(
        self,
        host: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        project: str | None = None,
    ):
        """
        Initialize the Jira debugger.

        Credentials are loaded in the following order:
        1. Direct parameters (host, email, api_token, project)
        2. Environment variables (JIRA_HOST, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PROJECT)

        Args:
            host: Jira host (e.g., 'yourcompany.atlassian.net') without https://
            email: Email address for authentication
            api_token: API token for authentication
            project: Default project key (optional)
        """
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
                raise ValueError(f"Jira credentials not configured. Missing: {', '.join(missing)}")
            self._client = JIRA(
                server=f"https://{self._host}",
                basic_auth=(self._email, self._api_token),
            )
        return self._client

    def get_ticket_details(self, issue_key: str) -> dict[str, Any]:
        """
        Get full details of a Jira ticket.

        Args:
            issue_key: The Jira issue key (e.g., IGAL-123)

        Returns:
            Dictionary containing ticket details or error information
        """
        try:
            issue = self.client.issue(
                issue_key,
                fields="key,summary,description,status,issuetype,priority,"
                "assignee,reporter,labels,created,updated,issuelinks,attachment,parent,subtasks",
            )

            # Extract labels
            labels = []
            if hasattr(issue.fields, "labels") and issue.fields.labels:
                labels = list(issue.fields.labels)

            # Extract linked issues
            linked_issues = []
            if hasattr(issue.fields, "issuelinks") and issue.fields.issuelinks:
                for link in issue.fields.issuelinks:
                    if hasattr(link, "outwardIssue"):
                        linked_issues.append(
                            {
                                "key": link.outwardIssue.key,
                                "type": link.type.outward,
                                "summary": link.outwardIssue.fields.summary,
                            }
                        )
                    elif hasattr(link, "inwardIssue"):
                        linked_issues.append(
                            {
                                "key": link.inwardIssue.key,
                                "type": link.type.inward,
                                "summary": link.inwardIssue.fields.summary,
                            }
                        )

            # Extract attachment filenames
            attachments = []
            if hasattr(issue.fields, "attachment") and issue.fields.attachment:
                attachments = [att.filename for att in issue.fields.attachment]

            # Extract parent info (if this issue has a parent)
            parent = None
            if hasattr(issue.fields, "parent") and issue.fields.parent:
                parent = {
                    "key": issue.fields.parent.key,
                    "summary": issue.fields.parent.fields.summary,
                }

            # Extract subtasks (if this issue has subtasks)
            subtasks = []
            if hasattr(issue.fields, "subtasks") and issue.fields.subtasks:
                for subtask in issue.fields.subtasks:
                    subtasks.append(
                        {
                            "key": subtask.key,
                            "summary": subtask.fields.summary,
                            "status": str(subtask.fields.status),
                        }
                    )

            # Extract epic children (if this is an Epic)
            epic_children = []
            if str(issue.fields.issuetype).lower() == "epic":
                # Query for issues that belong to this Epic
                # In modern Jira, children have parent=Epic. In older Jira, they have "Epic Link" custom field.
                # Try parent first (works in most Jira Cloud setups)
                try:
                    epic_jql = f'parent = "{issue.key}" ORDER BY created ASC'
                    children = self.client.search_issues(
                        epic_jql,
                        maxResults=50,
                        fields="key,summary,status",
                    )
                    for child in children:
                        epic_children.append(
                            {
                                "key": child.key,
                                "summary": child.fields.summary,
                                "status": str(child.fields.status),
                            }
                        )
                except JIRAError:
                    # If parent query fails, try Epic Link (older Jira)
                    try:
                        epic_jql = f'"Epic Link" = "{issue.key}" ORDER BY created ASC'
                        children = self.client.search_issues(
                            epic_jql,
                            maxResults=50,
                            fields="key,summary,status",
                        )
                        for child in children:
                            epic_children.append(
                                {
                                    "key": child.key,
                                    "summary": child.fields.summary,
                                    "status": str(child.fields.status),
                                }
                            )
                    except JIRAError:
                        pass  # No epic children found or field doesn't exist

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
                parent=parent,
                subtasks=subtasks,
                epic_children=epic_children,
            )

            return ticket.model_dump()

        except JIRAError as e:
            if "does not exist" in str(e.text).lower() or e.status_code == 404:
                return {"error": f"Issue {issue_key} not found"}
            if e.status_code == 403:
                return {"error": f"Permission denied: Cannot access issue {issue_key}"}
            return {"error": f"Jira API error: {e.text}"}

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
            return {"error": "At least one search parameter is required (query, issue_type, status, or assignee)"}

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
