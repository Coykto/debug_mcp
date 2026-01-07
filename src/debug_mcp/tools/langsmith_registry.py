"""Registry for LangSmith tools - registers directly with FastMCP."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastmcp import FastMCP

from ..utils.run_memory import get_memory_store
from .langsmith import get_langsmith_debugger


def _extract_run_summary(details: dict) -> dict[str, Any]:
    """Extract key summary information from run details."""
    summary: dict[str, Any] = {
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


def register_tools(mcp: FastMCP) -> None:
    """Register LangSmith tools with the MCP server."""

    @mcp.tool()
    async def list_langsmith_projects(environment: str, limit: int = 100) -> dict:
        """List available LangSmith projects.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
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
        """List runs/traces from a LangSmith project.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
            project_name: Project name (uses default from credentials if empty)
            run_type: Filter by type: chain, llm, tool, retriever, embedding, prompt, parser
            is_root: If True, return only root runs/top-level traces (default: True)
            error_only: If True, return only errored runs (default: False)
            hours_back: Number of hours to look back (default: 24)
            limit: Maximum number of runs to return (default: 100)
        """
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

    @mcp.tool()
    async def get_langsmith_run_details(
        environment: str, run_id: str, include_children: bool = True, full_content: bool = False
    ) -> dict:
        """Get detailed information about a specific LangSmith run/trace.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
            run_id: The run ID (UUID) to retrieve
            include_children: If True, also fetch child runs (default: True)
            full_content: If True, return full content instead of summary (default: False).
                WARNING: Full content can be ~25k+ tokens.
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

    @mcp.tool()
    async def search_langsmith_runs(
        environment: str,
        search_text: str,
        project_name: str = "",
        hours_back: int = 24,
        limit: int = 50,
        include_children: bool = True,
    ) -> dict:
        """Search for LangSmith conversations containing specific text content.

        Args:
            environment: Environment to query ('prod', 'dev', 'local')
            search_text: The text to search for (case-insensitive). Use unique identifiers for best results.
            project_name: Project name (uses default from credentials if empty)
            hours_back: Number of hours to look back (default: 24)
            limit: Maximum runs to search through (default: 50)
            include_children: Search in child runs too (default: True)
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

    @mcp.tool()
    async def search_run_content(
        reference_id: str,
        query: str,
        search_type: str = "auto",
        max_results: int = 5,
    ) -> dict:
        """Search within a previously fetched LangSmith run's content using semantic similarity.

        Args:
            reference_id: The reference_id returned by get_langsmith_run_details()
            query: What to search for (text, keywords, or semantic queries)
            search_type: Search method: 'auto' (semantic, default), 'keyword' (exact), 'similar' (explicit semantic)
            max_results: Maximum number of matching chunks to return (default: 5)
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

    @mcp.tool()
    async def get_run_field(reference_id: str, field_path: str) -> dict:
        """Get a specific field from a previously fetched LangSmith run.

        Args:
            reference_id: The reference_id from get_langsmith_run_details()
            field_path: Dot-notation path to the field (e.g., 'outputs.chat_history.2.content')
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
        size_info: dict[str, Any] = {}
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
