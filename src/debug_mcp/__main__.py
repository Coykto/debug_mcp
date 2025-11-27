"""Entry point for debug-mcp."""

import argparse
import os

from .server import mcp


def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Debug MCP Server")
    parser.add_argument("--aws-region", help="AWS region (overrides AWS_REGION env var)")
    parser.add_argument("--aws-profile", help="AWS profile (overrides AWS_PROFILE env var)")

    args = parser.parse_args()

    # Set environment variables from CLI args if provided
    if args.aws_region:
        os.environ["AWS_REGION"] = args.aws_region
    if args.aws_profile:
        os.environ["AWS_PROFILE"] = args.aws_profile

    mcp.run()


if __name__ == "__main__":
    main()
