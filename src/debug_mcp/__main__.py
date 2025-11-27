"""Entry point for debug-mcp."""

import argparse
import os


def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Debug MCP Server")
    parser.add_argument("--aws-region", default="us-east-1", help="AWS region (default: us-east-1)")
    parser.add_argument("--aws-profile", default="", help="AWS profile (default: empty)")

    args = parser.parse_args()

    # Set environment variables for boto3 clients
    os.environ["AWS_REGION"] = args.aws_region
    if args.aws_profile:
        os.environ["AWS_PROFILE"] = args.aws_profile

    # Import server AFTER environment variables are set
    from .server import mcp

    mcp.run()


if __name__ == "__main__":
    main()
