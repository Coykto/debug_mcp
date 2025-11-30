"""Registry for CloudWatch tools using the @debug_tool decorator."""

import os

from pydantic import BaseModel, Field

from ..registry import ToolParameter, debug_tool
from .cloudwatch_logs import CloudWatchLogsTools


class DescribeLogGroupsArgs(BaseModel):
    """Arguments for describe_log_groups tool."""

    log_group_name_prefix: str = Field(
        default="", description="Filter log groups by prefix (e.g., /aws/lambda/, /ecs/)"
    )
    region: str = Field(default="", description="AWS region to query (uses configured region if empty)")


class AnalyzeLogGroupArgs(BaseModel):
    """Arguments for analyze_log_group tool."""

    log_group_name: str = Field(description="Log group name")
    start_time: str = Field(description="Start time (ISO format)")
    end_time: str = Field(description="End time (ISO format)")
    filter_pattern: str = Field(default="", description="Optional filter pattern")
    region: str = Field(default="", description="AWS region to query (uses configured region if empty)")


class ExecuteLogInsightsQueryArgs(BaseModel):
    """Arguments for execute_log_insights_query tool."""

    log_group_names: list[str] = Field(description="List of log group names to query")
    query_string: str = Field(description="CloudWatch Insights query")
    start_time: str = Field(description="Start time (ISO format)")
    end_time: str = Field(description="End time (ISO format)")
    limit: int = Field(default=100, description="Maximum results")
    region: str = Field(default="", description="AWS region to query (uses configured region if empty)")


class GetLogsInsightQueryResultsArgs(BaseModel):
    """Arguments for get_logs_insight_query_results tool."""

    query_id: str = Field(description="Query ID from execute_log_insights_query")
    region: str = Field(default="", description="AWS region to query (uses configured region if empty)")


def is_aws_configured() -> bool:
    """Check if AWS credentials are configured (region is required, profile is optional)."""
    return bool(os.getenv("AWS_REGION"))


# Initialize CloudWatch Logs tools only if AWS is configured
_cw_logs: CloudWatchLogsTools | None = None
if is_aws_configured():
    _cw_logs = CloudWatchLogsTools(
        aws_profile=os.getenv("AWS_PROFILE", ""),
        aws_region=os.getenv("AWS_REGION", "us-east-1"),
    )


# Register describe_log_groups tool
if is_aws_configured():

    @debug_tool(
        name="describe_log_groups",
        description="List CloudWatch log groups with optional prefix filtering",
        category="cloudwatch",
        parameters=[
            ToolParameter(
                name="log_group_name_prefix",
                type="string",
                description="Filter log groups by prefix (e.g., /aws/lambda/, /ecs/)",
                required=False,
                default="",
            ),
            ToolParameter(
                name="region",
                type="string",
                description="AWS region to query (uses configured region if empty)",
                required=False,
                default="",
            ),
        ],
        arg_model=DescribeLogGroupsArgs,
    )
    async def describe_log_groups_registry(log_group_name_prefix: str = "", region: str = "") -> dict:
        """List CloudWatch log groups."""
        return await _cw_logs.describe_log_groups(log_group_name_prefix=log_group_name_prefix, region=region)


# Register analyze_log_group tool
if is_aws_configured():

    @debug_tool(
        name="analyze_log_group",
        description="Analyze CloudWatch logs for anomalies, message patterns, and error patterns",
        category="cloudwatch",
        parameters=[
            ToolParameter(
                name="log_group_name",
                type="string",
                description="Log group name",
                required=True,
            ),
            ToolParameter(
                name="start_time",
                type="string",
                description="Start time (ISO format)",
                required=True,
            ),
            ToolParameter(
                name="end_time",
                type="string",
                description="End time (ISO format)",
                required=True,
            ),
            ToolParameter(
                name="filter_pattern",
                type="string",
                description="Optional filter pattern",
                required=False,
                default="",
            ),
            ToolParameter(
                name="region",
                type="string",
                description="AWS region to query (uses configured region if empty)",
                required=False,
                default="",
            ),
        ],
        arg_model=AnalyzeLogGroupArgs,
    )
    async def analyze_log_group_registry(
        log_group_name: str,
        start_time: str,
        end_time: str,
        filter_pattern: str = "",
        region: str = "",
    ) -> dict:
        """Analyze CloudWatch logs for anomalies, message patterns, and error patterns."""
        return await _cw_logs.analyze_log_group(
            log_group_name=log_group_name,
            start_time=start_time,
            end_time=end_time,
            filter_pattern=filter_pattern,
            region=region,
        )


# Register execute_log_insights_query tool
if is_aws_configured():

    @debug_tool(
        name="execute_log_insights_query",
        description="Execute CloudWatch Logs Insights query",
        category="cloudwatch",
        parameters=[
            ToolParameter(
                name="log_group_names",
                type="array",
                description="List of log group names to query",
                required=True,
            ),
            ToolParameter(
                name="query_string",
                type="string",
                description="CloudWatch Insights query",
                required=True,
            ),
            ToolParameter(
                name="start_time",
                type="string",
                description="Start time (ISO format)",
                required=True,
            ),
            ToolParameter(
                name="end_time",
                type="string",
                description="End time (ISO format)",
                required=True,
            ),
            ToolParameter(
                name="limit",
                type="number",
                description="Maximum results",
                required=False,
                default=100,
            ),
            ToolParameter(
                name="region",
                type="string",
                description="AWS region to query (uses configured region if empty)",
                required=False,
                default="",
            ),
        ],
        arg_model=ExecuteLogInsightsQueryArgs,
    )
    async def execute_log_insights_query_registry(
        log_group_names: list[str],
        query_string: str,
        start_time: str,
        end_time: str,
        limit: int = 100,
        region: str = "",
    ) -> dict:
        """Execute CloudWatch Logs Insights query."""
        return await _cw_logs.execute_log_insights_query(
            log_group_names=log_group_names,
            query_string=query_string,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            region=region,
        )


# Register get_logs_insight_query_results tool
if is_aws_configured():

    @debug_tool(
        name="get_logs_insight_query_results",
        description="Get results from a CloudWatch Logs Insights query",
        category="cloudwatch",
        parameters=[
            ToolParameter(
                name="query_id",
                type="string",
                description="Query ID from execute_log_insights_query",
                required=True,
            ),
            ToolParameter(
                name="region",
                type="string",
                description="AWS region to query (uses configured region if empty)",
                required=False,
                default="",
            ),
        ],
        arg_model=GetLogsInsightQueryResultsArgs,
    )
    async def get_logs_insight_query_results_registry(query_id: str, region: str = "") -> dict:
        """Get results from a CloudWatch Logs Insights query."""
        return await _cw_logs.get_logs_insight_query_results(query_id=query_id, region=region)
