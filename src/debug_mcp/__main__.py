"""Entry point for debug-mcp."""

import argparse
import os


def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Debug MCP Server")
    # AWS args - no defaults, only set if explicitly provided
    parser.add_argument("--aws-region", default="", help="AWS region (enables AWS tools)")
    parser.add_argument("--aws-profile", default="", help="AWS profile name")
    # Jira args
    parser.add_argument("--jira-host", default="", help="Jira host (e.g., yourcompany.atlassian.net)")
    parser.add_argument("--jira-email", default="", help="Jira email for authentication")
    parser.add_argument("--jira-project", default="", help="Default Jira project key (optional)")
    parser.add_argument("--jira-token", default="", help="Jira API token (alternative to JIRA_API_TOKEN env var)")
    # LangSmith args
    parser.add_argument("--langsmith-api-key", default="", help="LangSmith API key (enables LangSmith tools)")

    args = parser.parse_args()

    # Set environment variables for AWS (only if provided)
    if args.aws_region:
        os.environ["AWS_REGION"] = args.aws_region
    if args.aws_profile:
        os.environ["AWS_PROFILE"] = args.aws_profile

    # Set environment variables for Jira (only if provided)
    if args.jira_host:
        os.environ["JIRA_HOST"] = args.jira_host
    if args.jira_email:
        os.environ["JIRA_EMAIL"] = args.jira_email
    if args.jira_project:
        os.environ["JIRA_PROJECT"] = args.jira_project
    if args.jira_token:
        os.environ["JIRA_API_TOKEN"] = args.jira_token

    # Set environment variables for LangSmith (only if provided)
    if args.langsmith_api_key:
        os.environ["LANGCHAIN_API_KEY"] = args.langsmith_api_key

    # Import server AFTER environment variables are set
    from .server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
