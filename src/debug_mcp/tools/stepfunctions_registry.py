"""Registry for Step Functions tools - registers directly with FastMCP."""

from fastmcp import FastMCP

from .stepfunctions import StepFunctionsDebugger


def register_tools(mcp: FastMCP) -> None:
    """Register Step Functions tools with the MCP server."""
    sf_debugger = StepFunctionsDebugger()

    @mcp.tool()
    async def list_state_machines(max_results: int = 100) -> dict:
        """List all Step Functions state machines in the account.

        Args:
            max_results: Maximum number of state machines to return (default: 100)
        """
        state_machines = sf_debugger.list_state_machines(max_results=max_results)
        return {"state_machines": state_machines, "count": len(state_machines)}

    @mcp.tool()
    async def list_step_function_executions(
        state_machine_arn: str,
        status_filter: str = "",
        max_results: int = 100,
        hours_back: int = 168,
    ) -> dict:
        """List executions for a Step Functions state machine.

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

    @mcp.tool()
    async def get_state_machine_definition(state_machine_arn: str) -> dict:
        """Get the state machine definition including ASL and extracted resources.

        Args:
            state_machine_arn: ARN of the state machine
        """
        return sf_debugger.get_state_machine_definition(state_machine_arn)

    @mcp.tool()
    async def get_step_function_execution_details(execution_arn: str, include_definition: bool = False) -> dict:
        """Get detailed information about a specific Step Functions execution.

        Args:
            execution_arn: ARN of the execution
            include_definition: If True, includes the state machine definition with Lambda ARNs (default: False)
        """
        if include_definition:
            return sf_debugger.get_execution_details_with_definition(execution_arn)
        return sf_debugger.get_execution_details(execution_arn)

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
        """Search Step Functions executions with advanced filtering.

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
