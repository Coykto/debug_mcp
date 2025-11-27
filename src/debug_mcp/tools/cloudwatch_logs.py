"""CloudWatch Logs tools using direct boto3 implementation.

This bypasses the AWS CloudWatch MCP server which has bugs with environment variable handling.
Based on: https://github.com/awslabs/mcp/blob/main/src/cloudwatch-mcp-server/awslabs/cloudwatch_mcp_server/cloudwatch_logs/tools.py
"""

import asyncio
from typing import Any

import boto3
from botocore.config import Config


class CloudWatchLogsTools:
    """CloudWatch Logs tools using direct boto3 implementation."""

    def __init__(self, aws_profile: str = "", aws_region: str = "us-east-1"):
        """Initialize CloudWatch Logs tools.

        Args:
            aws_profile: AWS profile name (empty string uses default credentials)
            aws_region: AWS region (defaults to us-east-1)
        """
        self.aws_profile = aws_profile
        self.aws_region = aws_region

    def _get_logs_client(self, region: str | None = None):
        """Create a CloudWatch Logs client for the specified region.

        Args:
            region: AWS region to use. If None, uses self.aws_region

        Returns:
            boto3 CloudWatch Logs client
        """
        target_region = region or self.aws_region
        config = Config(user_agent_extra="debug-mcp/0.1.0")

        try:
            if self.aws_profile:
                return boto3.Session(profile_name=self.aws_profile, region_name=target_region).client(
                    "logs", config=config
                )
            else:
                return boto3.Session(region_name=target_region).client("logs", config=config)
        except Exception as e:
            raise RuntimeError(f"Error creating CloudWatch Logs client for region {target_region}: {e}") from e

    def _remove_null_values(self, d: dict[str, Any]) -> dict[str, Any]:
        """Remove keys with None values from a dictionary."""
        return {k: v for k, v in d.items() if v is not None}

    async def describe_log_groups(
        self,
        log_group_name_prefix: str = "",
        region: str = "",
    ) -> dict[str, Any]:
        """List CloudWatch log groups.

        Args:
            log_group_name_prefix: Filter log groups by prefix (e.g., /aws/lambda/, /ecs/)
            region: AWS region to query (uses configured region if empty)

        Returns:
            Dictionary with log_groups list
        """
        logs_client = self._get_logs_client(region)

        try:
            paginator = logs_client.get_paginator("describe_log_groups")
            kwargs = {}
            if log_group_name_prefix:
                kwargs["logGroupNamePrefix"] = log_group_name_prefix

            log_groups = []
            for page in paginator.paginate(**kwargs):
                log_groups.extend(page.get("logGroups", []))

            return {"log_groups": log_groups}

        except Exception as e:
            raise RuntimeError(f"Error describing log groups: {e}") from e

    async def analyze_log_group(
        self,
        log_group_name: str,
        start_time: str,
        end_time: str,
        filter_pattern: str = "",
        region: str = "",
    ) -> dict[str, Any]:
        """Analyze CloudWatch logs for anomalies, message patterns, and error patterns.

        Args:
            log_group_name: Log group name
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            filter_pattern: Optional filter pattern
            region: AWS region to query (uses configured region if empty)

        Returns:
            Dictionary with analysis results
        """
        # For now, return a simplified version
        # Full implementation would include anomaly detection and pattern analysis
        return {
            "message": "Log group analysis",
            "log_group_name": log_group_name,
            "start_time": start_time,
            "end_time": end_time,
            "filter_pattern": filter_pattern,
        }

    async def execute_log_insights_query(
        self,
        log_group_names: list[str],
        query_string: str,
        start_time: str,
        end_time: str,
        limit: int = 100,
        region: str = "",
    ) -> dict[str, Any]:
        """Execute CloudWatch Logs Insights query.

        Args:
            log_group_names: List of log group names to query
            query_string: CloudWatch Insights query
            start_time: Start time (ISO format)
            end_time: End time (ISO format)
            limit: Maximum results
            region: AWS region to query (uses configured region if empty)

        Returns:
            Dictionary with query results
        """
        logs_client = self._get_logs_client(region)

        try:
            # Convert ISO time to Unix timestamp
            import datetime

            start_ts = int(datetime.datetime.fromisoformat(start_time).timestamp())
            end_ts = int(datetime.datetime.fromisoformat(end_time).timestamp())

            # Start the query
            response = logs_client.start_query(
                logGroupNames=log_group_names,
                startTime=start_ts,
                endTime=end_ts,
                queryString=query_string,
                limit=limit,
            )

            query_id = response["queryId"]

            # Poll for results (max 30 seconds)
            max_wait = 30
            waited = 0
            while waited < max_wait:
                await asyncio.sleep(1)
                waited += 1

                result = logs_client.get_query_results(queryId=query_id)
                status = result["status"]

                if status in {"Complete", "Failed", "Cancelled"}:
                    # Process results
                    processed_results = [
                        {field["field"]: field["value"] for field in line} for line in result.get("results", [])
                    ]

                    return {
                        "queryId": query_id,
                        "status": status,
                        "statistics": result.get("statistics", {}),
                        "results": processed_results,
                    }

            # Timeout
            return {
                "queryId": query_id,
                "status": "Timeout",
                "message": f"Query did not complete within {max_wait} seconds. Use get_logs_insight_query_results to retry.",
                "results": [],
            }

        except Exception as e:
            raise RuntimeError(f"Error executing Logs Insights query: {e}") from e

    async def get_logs_insight_query_results(
        self,
        query_id: str,
        region: str = "",
    ) -> dict[str, Any]:
        """Get results from a CloudWatch Logs Insights query.

        Args:
            query_id: Query ID from execute_log_insights_query
            region: AWS region to query (uses configured region if empty)

        Returns:
            Dictionary with query results
        """
        logs_client = self._get_logs_client(region)

        try:
            result = logs_client.get_query_results(queryId=query_id)

            # Process results
            processed_results = [
                {field["field"]: field["value"] for field in line} for line in result.get("results", [])
            ]

            return {
                "queryId": query_id,
                "status": result["status"],
                "statistics": result.get("statistics", {}),
                "results": processed_results,
            }

        except Exception as e:
            raise RuntimeError(f"Error getting query results: {e}") from e

    async def cancel_logs_insight_query(
        self,
        query_id: str,
        region: str = "",
    ) -> dict[str, Any]:
        """Cancel an in-progress CloudWatch Logs Insights query.

        Args:
            query_id: Query ID to cancel
            region: AWS region to query (uses configured region if empty)

        Returns:
            Dictionary with success status
        """
        logs_client = self._get_logs_client(region)

        try:
            response = logs_client.stop_query(queryId=query_id)
            return {"success": response.get("success", False)}

        except Exception as e:
            raise RuntimeError(f"Error cancelling query: {e}") from e
