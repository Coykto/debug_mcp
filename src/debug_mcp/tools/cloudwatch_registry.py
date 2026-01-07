"""Registry for CloudWatch tools - registers directly with FastMCP."""

import os

from fastmcp import FastMCP

from .cloudwatch_logs import CloudWatchLogsTools


def register_tools(mcp: FastMCP) -> None:
    """Register CloudWatch tools with the MCP server."""
    cw_logs = CloudWatchLogsTools(
        aws_profile=os.getenv("AWS_PROFILE", ""),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
    )

    @mcp.tool()
    async def describe_log_groups(log_group_name_prefix: str = "", region: str = "") -> dict:
        """List CloudWatch log groups with optional prefix filtering.

        Args:
            log_group_name_prefix: Filter log groups by prefix (e.g., /aws/lambda/, /ecs/)
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.describe_log_groups(log_group_name_prefix=log_group_name_prefix, region=region)

    @mcp.tool()
    async def analyze_log_group(
        log_group_name: str,
        start_time: str,
        end_time: str,
        filter_pattern: str = "",
        region: str = "",
    ) -> dict:
        """Analyze CloudWatch logs for anomalies, message patterns, and error patterns.

        Args:
            log_group_name: Log group name
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            filter_pattern: Optional filter pattern
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.analyze_log_group(
            log_group_name=log_group_name,
            start_time=start_time,
            end_time=end_time,
            filter_pattern=filter_pattern,
            region=region,
        )

    @mcp.tool()
    async def execute_log_insights_query(
        log_group_names: list[str],
        query_string: str,
        start_time: str,
        end_time: str,
        limit: int = 100,
        region: str = "",
    ) -> dict:
        """Execute CloudWatch Logs Insights query.

        Args:
            log_group_names: List of log group names to query
            query_string: CloudWatch Insights query
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            limit: Maximum results
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.execute_log_insights_query(
            log_group_names=log_group_names,
            query_string=query_string,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            region=region,
        )

    @mcp.tool()
    async def get_logs_insight_query_results(query_id: str, region: str = "") -> dict:
        """Get results from a CloudWatch Logs Insights query.

        Args:
            query_id: Query ID from execute_log_insights_query
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.get_logs_insight_query_results(query_id=query_id, region=region)
