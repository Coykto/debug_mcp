"""Entry point for debug-mcp."""

import argparse
import os


def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Debug MCP Server")
    parser.add_argument("--aws-region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--aws-profile", default="", help="AWS profile (default: empty)")
    parser.add_argument("--jira-host", default="", help="Jira host (e.g., yourcompany.atlassian.net)")
    parser.add_argument("--jira-email", default="", help="Jira email for authentication")
    parser.add_argument("--jira-project", default="", help="Default Jira project key (optional)")

    args = parser.parse_args()

    # Set environment variables for boto3 clients
    os.environ["AWS_REGION"] = args.aws_region
    if args.aws_profile:
        os.environ["AWS_PROFILE"] = args.aws_profile

    # Set environment variables for Jira
    if args.jira_host:
        os.environ["JIRA_HOST"] = args.jira_host
    if args.jira_email:
        os.environ["JIRA_EMAIL"] = args.jira_email
    if args.jira_project:
        os.environ["JIRA_PROJECT"] = args.jira_project

    # Import server AFTER environment variables are set
    from .server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
