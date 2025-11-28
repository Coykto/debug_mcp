"""Main MCP server for debugging distributed systems using boto3 and SDKs."""

import os
from datetime import UTC

from fastmcp import FastMCP

from .tools.cloudwatch_logs import CloudWatchLogsTools
from .tools.jira import JiraDebugger
from .tools.langsmith import get_langsmith_debugger
from .tools.stepfunctions import StepFunctionsDebugger
from .utils.run_memory import get_memory_store

# Initialize MCP server
mcp = FastMCP("debug-mcp")


# Get configured tools from environment variable
# Format: comma-separated list like "describe_log_groups,analyze_log_group"
# If not set, expose core debugging tools by default
# Set to "all" to expose all 26 tools
DEFAULT_TOOLS = (
    # CloudWatch Logs (5 tools)
    "describe_log_groups,"
    "analyze_log_group,"
    "execute_log_insights_query,"
    "get_logs_insight_query_results,"
    "cancel_logs_insight_query,"
    # Step Functions (5 tools)
    "list_state_machines,"
    "get_state_machine_definition,"
    "list_step_function_executions,"
    "get_step_function_execution_details,"
    "search_step_function_executions,"
    # LangSmith (6 tools)
    "list_langsmith_projects,"
    "list_langsmith_runs,"
    "get_langsmith_run_details,"
    "search_langsmith_runs,"
    "search_run_content,"
    "get_run_field,"
    # Jira (2 tools)
    "get_jira_ticket,"
    "search_jira_tickets"
)

configured_tools_str = os.getenv("DEBUG_MCP_TOOLS", DEFAULT_TOOLS)
if configured_tools_str.lower() == "all":
    configured_tools = None  # None means expose all
else:
    configured_tools = set(tool.strip() for tool in configured_tools_str.split(",") if tool.strip())


def should_expose_tool(tool_name: str) -> bool:
    """Check if a tool should be exposed based on configuration."""
    if configured_tools is None:
        return True  # Expose all
    return tool_name in configured_tools


def is_jira_configured() -> bool:
    """Check if Jira credentials are configured."""
    return bool(os.getenv("JIRA_HOST") and os.getenv("JIRA_EMAIL") and os.getenv("JIRA_API_TOKEN"))


def is_aws_configured() -> bool:
    """Check if AWS credentials are configured (region is required, profile is optional)."""
    return bool(os.getenv("AWS_REGION"))


def is_langsmith_configured() -> bool:
    """Check if LangSmith credentials are available (API key in env or will be loaded from secrets)."""
    # LangSmith can load credentials from AWS Secrets Manager or .env file,
    # so we just check if AWS is configured (for secrets) or local key exists
    return bool(
        os.getenv("LANGCHAIN_API_KEY")  # Direct env var
        or os.getenv("AWS_REGION")  # Can load from AWS Secrets Manager
    )


# Initialize tool classes only if credentials are configured
cw_logs = (
    CloudWatchLogsTools(aws_profile=os.getenv("AWS_PROFILE", ""), aws_region=os.getenv("AWS_REGION", "us-east-1"))
    if is_aws_configured()
    else None
)

sf_debugger = StepFunctionsDebugger() if is_aws_configured() else None

jira_debugger = JiraDebugger() if is_jira_configured() else None


# CloudWatch Logs Tools - using direct boto3 implementation
if is_aws_configured() and should_expose_tool("describe_log_groups"):

    @mcp.tool()
    async def describe_log_groups(log_group_name_prefix: str = "", region: str = "") -> dict:
        """
        List CloudWatch log groups.

        Args:
            log_group_name_prefix: Filter log groups by prefix (e.g., /aws/lambda/, /ecs/)
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.describe_log_groups(log_group_name_prefix=log_group_name_prefix, region=region)


if is_aws_configured() and should_expose_tool("analyze_log_group"):

    @mcp.tool()
    async def analyze_log_group(
        log_group_name: str, start_time: str, end_time: str, filter_pattern: str = "", region: str = ""
    ) -> dict:
        """
        Analyze CloudWatch logs for anomalies, message patterns, and error patterns.

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


if is_aws_configured() and should_expose_tool("execute_log_insights_query"):

    @mcp.tool()
    async def execute_log_insights_query(
        log_group_names: list[str],
        query_string: str,
        start_time: str,
        end_time: str,
        limit: int = 100,
        region: str = "",
    ) -> dict:
        """
        Execute CloudWatch Logs Insights query.

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


if is_aws_configured() and should_expose_tool("get_logs_insight_query_results"):

    @mcp.tool()
    async def get_logs_insight_query_results(query_id: str, region: str = "") -> dict:
        """
        Get results from a CloudWatch Logs Insights query.

        Args:
            query_id: Query ID from execute_log_insights_query
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.get_logs_insight_query_results(query_id=query_id, region=region)


if is_aws_configured() and should_expose_tool("cancel_logs_insight_query"):

    @mcp.tool()
    async def cancel_logs_insight_query(query_id: str, region: str = "") -> dict:
        """
        Cancel an in-progress CloudWatch Logs Insights query.

        Args:
            query_id: Query ID to cancel
            region: AWS region to query (uses configured region if empty)
        """
        return await cw_logs.cancel_logs_insight_query(query_id=query_id, region=region)


# Step Functions Debugging Tools - using boto3 directly
# These tools provide comprehensive debugging capabilities for Step Functions executions
# Debugger initialized above with conditional check for AWS credentials


if is_aws_configured() and should_expose_tool("list_state_machines"):

    @mcp.tool()
    async def list_state_machines(max_results: int = 100) -> dict:
        """
        List all Step Functions state machines in the account.

        Args:
            max_results: Maximum number of state machines to return (default: 100)
        """
        state_machines = sf_debugger.list_state_machines(max_results=max_results)
        return {"state_machines": state_machines, "count": len(state_machines)}


if is_aws_configured() and should_expose_tool("list_step_function_executions"):

    @mcp.tool()
    async def list_step_function_executions(
        state_machine_arn: str,
        status_filter: str = "",
        max_results: int = 100,
        hours_back: int = 168,
    ) -> dict:
        """
        List executions for a Step Functions state machine.

        Args:
            state_machine_arn: ARN of the state machine
            status_filter: Optional status filter (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)
            max_results: Maximum number of executions to return (default: 100)
            hours_back: Number of hours to look back (default: 168 = 7 days)
        """
        executions = sf_debugger.list_executions(
            state_machine_arn=state_machine_arn,
            status_filter=status_filter if status_filter else None,
            max_results=max_results,
            hours_back=hours_back,
        )
        return {
            "executions": executions,
            "count": len(executions),
            "state_machine_arn": state_machine_arn,
        }


if is_aws_configured() and should_expose_tool("get_state_machine_definition"):

    @mcp.tool()
    async def get_state_machine_definition(state_machine_arn: str) -> dict:
        """
        Get the state machine definition including ASL and extracted resources.

        Returns the full Amazon States Language (ASL) definition along with
        extracted Lambda ARNs and other resource ARNs used in the workflow.

        Args:
            state_machine_arn: ARN of the state machine
        """
        return sf_debugger.get_state_machine_definition(state_machine_arn)


if is_aws_configured() and should_expose_tool("get_step_function_execution_details"):

    @mcp.tool()
    async def get_step_function_execution_details(execution_arn: str, include_definition: bool = False) -> dict:
        """
        Get detailed information about a specific Step Functions execution.

        Includes full execution history with state-level inputs and outputs.
        Only Step Functions states are included (Lambda task events are filtered out).

        Args:
            execution_arn: ARN of the execution
            include_definition: If True, includes the state machine definition with Lambda ARNs (default: False)
        """
        if include_definition:
            return sf_debugger.get_execution_details_with_definition(execution_arn)
        return sf_debugger.get_execution_details(execution_arn)


if is_aws_configured() and should_expose_tool("search_step_function_executions"):

    @mcp.tool()
    async def search_step_function_executions(
        state_machine_arn: str,
        state_name: str = "",
        input_pattern: str = "",
        output_pattern: str = "",
        status_filter: str = "",
        max_results: int = 50,
        hours_back: int = 168,
        include_definition: bool = False,
    ) -> dict:
        """
        Search Step Functions executions with advanced filtering.

        Supports regex patterns for state names and input/output content matching.
        This is powerful for finding specific execution scenarios.

        Args:
            state_machine_arn: ARN of the state machine
            state_name: Filter by state name (supports regex, e.g., "Match.*Entity")
            input_pattern: Regex pattern to match in state inputs (e.g., "customer_id.*12345")
            output_pattern: Regex pattern to match in state outputs (e.g., "entity_type.*company")
            status_filter: Optional status filter (RUNNING, SUCCEEDED, FAILED, etc.)
            max_results: Maximum number of executions to process (default: 50)
            hours_back: Number of hours to look back (default: 168 = 7 days)
            include_definition: If True, includes the state machine definition with Lambda ARNs (default: False)
        """
        executions = sf_debugger.search_executions(
            state_machine_arn=state_machine_arn,
            state_name=state_name if state_name else None,
            input_pattern=input_pattern if input_pattern else None,
            output_pattern=output_pattern if output_pattern else None,
            status_filter=status_filter if status_filter else None,
            max_results=max_results,
            hours_back=hours_back,
            include_definition=include_definition,
        )
        return {
            "executions": executions,
            "count": len(executions),
            "filters": {
                "state_name": state_name or None,
                "input_pattern": input_pattern or None,
                "output_pattern": output_pattern or None,
                "status": status_filter or None,
            },
        }


# LangSmith Debugging Tools - using langsmith SDK
# Supports multiple environments via AWS Secrets Manager or .env file
if is_langsmith_configured() and should_expose_tool("list_langsmith_projects"):

    @mcp.tool()
    async def list_langsmith_projects(environment: str, limit: int = 100) -> dict:
        """
        List available LangSmith projects.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
                        - prod: Uses PRODUCTION/env/vars from AWS Secrets Manager
                        - dev: Uses DEV/env/vars from AWS Secrets Manager
                        - local: Loads from .env file
            limit: Maximum number of projects to return (default: 100)
        """
        debugger = get_langsmith_debugger(environment)
        projects = debugger.list_projects(limit=limit)
        return {
            "environment": environment,
            "projects": projects,
            "count": len(projects),
            "default_project": debugger.default_project,
        }


if is_langsmith_configured() and should_expose_tool("list_langsmith_runs"):

    @mcp.tool()
    async def list_langsmith_runs(
        environment: str,
        project_name: str = "",
        run_type: str = "",
        is_root: bool = True,
        error_only: bool = False,
        hours_back: int = 24,
        limit: int = 100,
    ) -> dict:
        """
        List runs/traces from a LangSmith project.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
            project_name: Project name (uses default from credentials if empty)
            run_type: Filter by type: chain, llm, tool, retriever, embedding, prompt, parser
            is_root: If True, return only root runs/top-level traces (default: True)
            error_only: If True, return only errored runs (default: False)
            hours_back: Number of hours to look back (default: 24)
            limit: Maximum number of runs to return (default: 100)
        """
        from datetime import datetime, timedelta

        debugger = get_langsmith_debugger(environment)

        start_time = datetime.now(UTC) - timedelta(hours=hours_back)

        runs = debugger.list_runs(
            project_name=project_name if project_name else None,
            run_type=run_type if run_type else None,
            is_root=is_root,
            error=True if error_only else None,
            start_time=start_time,
            limit=limit,
        )

        return {
            "environment": environment,
            "project": project_name or debugger.default_project,
            "runs": runs,
            "count": len(runs),
            "filters": {
                "run_type": run_type or None,
                "is_root": is_root,
                "error_only": error_only,
                "hours_back": hours_back,
            },
        }


if is_langsmith_configured() and should_expose_tool("get_langsmith_run_details"):

    @mcp.tool()
    async def get_langsmith_run_details(
        environment: str, run_id: str, include_children: bool = True, full_content: bool = False
    ) -> dict:
        """
        Get detailed information about a specific LangSmith run/trace.

        By default, returns a SUMMARY with key metadata. Full content is stored in memory
        with semantic embeddings (sentence-transformers) and can be searched using
        search_run_content() or accessed via get_run_field().

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
            run_id: The run ID (UUID) to retrieve
            include_children: If True, also fetch child runs (default: True)
            full_content: If True, return full content instead of summary (default: False).
                         WARNING: Full content can be ~25k+ tokens. Use only when necessary.

        Returns:
            - reference_id: Use this with search_run_content() or get_run_field()
            - summary: Key metadata (status, latency, tokens, tools used, etc.)
            - If full_content=True: Also includes the complete run data

        TIP: Use search_run_content(reference_id, "your query") to semantically search
        within the run without loading everything into context.
        """
        debugger = get_langsmith_debugger(environment)
        details = debugger.get_run_details(run_id, include_children=include_children)

        # Create reference ID and store in memory
        reference_id = f"{environment}:{run_id}"
        memory = get_memory_store()

        # Extract summary information
        summary = _extract_run_summary(details)

        # Store full content in memory for later retrieval
        memory.store(reference_id, details, summary=summary)

        result = {
            "environment": environment,
            "reference_id": reference_id,
            "summary": summary,
            "hint": (
                "Full content stored in memory. Use search_run_content(reference_id, query) "
                "to search within this run, or get_run_field(reference_id, field_path) for specific fields."
            ),
        }

        # Optionally include full content (for backward compatibility or when explicitly needed)
        if full_content:
            result["run"] = details
            result["warning"] = "Full content included. This may use significant context."

        return result


def _extract_run_summary(details: dict) -> dict:
    """Extract key summary information from run details."""
    summary = {
        "id": details.get("id"),
        "name": details.get("name"),
        "status": details.get("status"),
        "run_type": details.get("run_type"),
        "latency_seconds": details.get("latency_seconds"),
        "total_tokens": details.get("total_tokens"),
        "prompt_tokens": details.get("prompt_tokens"),
        "completion_tokens": details.get("completion_tokens"),
        "error": details.get("error"),
        "link": details.get("link"),
    }

    # Extract tools called from chat history
    tools_called = []
    outputs = details.get("outputs", {})
    chat_history = outputs.get("chat_history", [])
    if isinstance(chat_history, list):
        for msg in chat_history:
            if isinstance(msg, dict):
                # Look for tool calls in AI messages
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls:
                    if isinstance(tc, dict) and "name" in tc:
                        tools_called.append(tc["name"])
                # Look for tool messages
                if msg.get("type") == "tool":
                    tool_name = msg.get("name", "unknown_tool")
                    if tool_name not in tools_called:
                        tools_called.append(tool_name)

    summary["tools_called"] = list(set(tools_called)) if tools_called else []
    summary["message_count"] = len(chat_history) if isinstance(chat_history, list) else 0

    # Include user query if available
    inputs = details.get("inputs", {})
    if isinstance(inputs, dict):
        input_data = inputs.get("input", {})
        if isinstance(input_data, dict):
            summary["user_query"] = input_data.get("user_query")

    # Include final response text if available
    if isinstance(outputs, dict):
        response = outputs.get("response", {})
        if isinstance(response, dict):
            final_text = response.get("final_text", "")
            if final_text:
                # Truncate for summary
                summary["response_preview"] = final_text[:500] + ("..." if len(final_text) > 500 else "")

    # Child run count
    children = details.get("children", [])
    summary["child_count"] = len(children) if isinstance(children, list) else 0

    return summary


if is_langsmith_configured() and should_expose_tool("search_langsmith_runs"):

    @mcp.tool()
    async def search_langsmith_runs(
        environment: str,
        search_text: str,
        project_name: str = "",
        hours_back: int = 24,
        limit: int = 50,
        include_children: bool = True,
    ) -> dict:
        """
        Search for LangSmith conversations containing specific text content.

        PURPOSE: This is a lightweight search tool designed to find conversations
        that contain a specific string. It returns only minimal match information
        to avoid large responses. Use this to locate a conversation, then use
        get_langsmith_run_details to retrieve full details.

        IMPORTANT - Use Specific Search Strings:
        - GOOD: "Error code XYZ-12345", "user@specific-email.com", "order_id: 98765"
        - BAD: "error", "failed", "user" (too generic, will match many runs)

        The more unique your search text, the faster and more accurate results.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
            search_text: The text to search for (case-insensitive). Use unique
                        identifiers, error codes, or specific phrases for best results.
            project_name: Project name (uses default from credentials if empty)
            hours_back: Number of hours to look back (default: 24)
            limit: Maximum runs to search through (default: 50)
            include_children: Search in child runs too (default: True)

        Returns:
            List of matches with run_id, context snippet, and link to full details

        If this tool fails, please report the issue at:
        https://github.com/Coykto/debug_mcp/issues
        """
        debugger = get_langsmith_debugger(environment)

        try:
            matches = debugger.find_conversation_by_content(
                search_text=search_text,
                project_name=project_name if project_name else None,
                hours_back=hours_back,
                limit=limit,
                include_children=include_children,
            )
        except Exception as e:
            # Provide helpful error message with guidance
            error_msg = str(e)
            return {
                "error": True,
                "error_message": error_msg,
                "environment": environment,
                "search_text": search_text,
                "guidance": (
                    "This search tool encountered an error. "
                    "DO NOT fall back to using get_langsmith_run_details to search - "
                    "that approach will overflow context with ~25k tokens per run. "
                    "Instead, please report this issue so it can be fixed."
                ),
                "report_issue": "https://github.com/Coykto/debug_mcp/issues",
                "tip": "Include the error message and search parameters when reporting.",
            }

        return {
            "environment": environment,
            "project": project_name or debugger.default_project,
            "search_text": search_text,
            "matches": matches,
            "match_count": len(matches),
            "runs_searched": limit,
            "hours_back": hours_back,
            "tip": "Use get_langsmith_run_details with a run_id to get full conversation details",
        }


if is_langsmith_configured() and should_expose_tool("search_run_content"):

    @mcp.tool()
    async def search_run_content(
        reference_id: str,
        query: str,
        search_type: str = "auto",
        max_results: int = 5,
    ) -> dict:
        """
        Search within a previously fetched LangSmith run's content using semantic similarity.

        This tool searches through the full content of a run that was previously
        retrieved with get_langsmith_run_details(). Use this to find specific
        information without loading the entire run into context.

        The run content is automatically chunked and embedded using sentence-transformers
        (all-MiniLM-L6-v2 model) for semantic search. This means you can search using
        natural language queries and find semantically related content.

        Args:
            reference_id: The reference_id returned by get_langsmith_run_details()
                         (format: "environment:run_id", e.g., "dev:abc-123-def")
            query: What to search for. Can be:
                   - Specific text: "July 5th, 2024"
                   - Keywords: "birthday start date"
                   - Semantic queries: "when did the project start" (finds related content)
            search_type: Search method to use:
                        - "auto": Use semantic similarity search (default, recommended)
                        - "keyword": Exact keyword/text matching only
                        - "similar": Explicit semantic similarity search
            max_results: Maximum number of matching chunks to return (default: 5)

        Returns:
            List of matching content chunks with their location (path) in the data structure
            and similarity scores (for semantic search)

        Example:
            1. First: get_langsmith_run_details(environment="dev", run_id="abc-123")
               -> Returns reference_id: "dev:abc-123"
            2. Then: search_run_content(reference_id="dev:abc-123", query="RAG tool results")
               -> Returns relevant chunks containing RAG tool information
        """
        memory = get_memory_store()
        stored_run = memory.get(reference_id)

        if not stored_run:
            return {
                "error": True,
                "error_message": f"No stored run found for reference_id: {reference_id}",
                "hint": "Make sure to call get_langsmith_run_details() first to store the run content.",
                "available_runs": [r["reference_id"] for r in memory.list_stored_runs()],
            }

        # Determine search method
        if search_type == "similar":
            results = memory.search_similar(reference_id, query, max_results=max_results)
            method_used = "semantic_similarity"
        elif search_type == "keyword":
            results = memory.search_keyword(reference_id, query, max_results=max_results)
            method_used = "keyword"
        else:  # auto
            # Try similarity first if embeddings are available
            results = memory.search_similar(reference_id, query, max_results=max_results)
            if results and any("similarity" in r for r in results):
                method_used = "semantic_similarity"
            else:
                results = memory.search_keyword(reference_id, query, max_results=max_results)
                method_used = "keyword"

        return {
            "reference_id": reference_id,
            "query": query,
            "search_method": method_used,
            "results": results,
            "result_count": len(results),
            "tip": "Use get_run_field(reference_id, path) to get the full content at a specific path",
        }


if is_langsmith_configured() and should_expose_tool("get_run_field"):

    @mcp.tool()
    async def get_run_field(reference_id: str, field_path: str) -> dict:
        """
        Get a specific field from a previously fetched LangSmith run.

        Use this to retrieve the full content of a specific field after
        finding it with search_run_content().

        Args:
            reference_id: The reference_id from get_langsmith_run_details()
            field_path: Dot-notation path to the field. Examples:
                       - "outputs.chat_history.2.content" - Get 3rd message content
                       - "outputs.response.final_text" - Get the final response
                       - "inputs.input.user_query" - Get the user's question
                       - "children.0.outputs" - Get first child run's outputs

        Returns:
            The value at the specified path, or error if not found

        Example paths for common data:
            - User query: "inputs.input.user_query"
            - Chat history: "outputs.chat_history"
            - Specific message: "outputs.chat_history.{index}.content"
            - Final response: "outputs.response.final_text"
            - Tool calls: "outputs.chat_history.{index}.tool_calls"
        """
        memory = get_memory_store()
        stored_run = memory.get(reference_id)

        if not stored_run:
            return {
                "error": True,
                "error_message": f"No stored run found for reference_id: {reference_id}",
                "hint": "Make sure to call get_langsmith_run_details() first to store the run content.",
                "available_runs": [r["reference_id"] for r in memory.list_stored_runs()],
            }

        value = memory.get_field(reference_id, field_path)

        if value is None:
            # Try to provide helpful suggestions
            available_keys = []
            parts = field_path.split(".")
            parent_path = ".".join(parts[:-1]) if len(parts) > 1 else ""
            parent = memory.get_field(reference_id, parent_path) if parent_path else stored_run.full_data

            if isinstance(parent, dict):
                available_keys = list(parent.keys())[:20]  # Limit suggestions
            elif isinstance(parent, list):
                available_keys = [f"{i}" for i in range(min(len(parent), 20))]

            return {
                "error": True,
                "error_message": f"Field not found at path: {field_path}",
                "parent_path": parent_path or "(root)",
                "available_keys": available_keys,
                "hint": "Check the path and try again. Use search_run_content() to find content locations.",
            }

        # Calculate size info for large values
        size_info = {}
        if isinstance(value, str):
            size_info = {"type": "string", "length": len(value), "word_count": len(value.split())}
        elif isinstance(value, list):
            size_info = {"type": "list", "length": len(value)}
        elif isinstance(value, dict):
            size_info = {"type": "dict", "keys": list(value.keys())[:20]}

        return {
            "reference_id": reference_id,
            "field_path": field_path,
            "value": value,
            "size_info": size_info,
        }


# Jira Tools - using jira-python library
# Only expose if Jira credentials are configured
if is_jira_configured() and should_expose_tool("get_jira_ticket"):

    @mcp.tool()
    async def get_jira_ticket(issue_key: str) -> dict:
        """
        Get full details of a Jira ticket.

        Args:
            issue_key: The Jira issue key (e.g., IGAL-123)

        Returns details including summary, description, status, assignee,
        reporter, labels, created and updated dates.
        """
        return jira_debugger.get_ticket_details(issue_key)


if is_jira_configured() and should_expose_tool("search_jira_tickets"):

    @mcp.tool()
    async def search_jira_tickets(
        query: str = "",
        issue_type: str = "",
        status: str = "",
        assignee: str = "",
        limit: int = 10,
    ) -> dict:
        """
        Search for Jira tickets with filters and text search.

        Args:
            query: Text to search for in ticket summaries
            issue_type: Filter by issue type (e.g., Bug, Story, Task, Epic)
            status: Filter by status (e.g., To Do, In Progress, Done)
            assignee: Filter by assignee (username or display name)
            limit: Maximum results to return (default: 10)

        Note: At least one parameter must be provided.
        """
        return jira_debugger.search_tickets(
            query=query if query else None,
            issue_type=issue_type if issue_type else None,
            status=status if status else None,
            assignee=assignee if assignee else None,
            limit=limit,
        )
