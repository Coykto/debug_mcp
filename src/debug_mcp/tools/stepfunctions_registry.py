"""Registry for Step Functions tools using the @debug_tool decorator."""

import os

from pydantic import BaseModel, Field

from ..registry import ToolParameter, debug_tool
from .stepfunctions import StepFunctionsDebugger


class ListStateMachinesArgs(BaseModel):
    """Arguments for list_state_machines tool."""

    max_results: int = Field(default=100, description="Maximum number of state machines to return (default: 100)")


class ListStepFunctionExecutionsArgs(BaseModel):
    """Arguments for list_step_function_executions tool."""

    state_machine_arn: str = Field(description="ARN of the state machine")
    status_filter: str = Field(
        default="", description="Optional status filter (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)"
    )
    max_results: int = Field(default=100, description="Maximum number of executions to return (default: 100)")
    hours_back: int = Field(default=168, description="Number of hours to look back (default: 168 = 7 days)")


class GetStateMachineDefinitionArgs(BaseModel):
    """Arguments for get_state_machine_definition tool."""

    state_machine_arn: str = Field(description="ARN of the state machine")


class GetStepFunctionExecutionDetailsArgs(BaseModel):
    """Arguments for get_step_function_execution_details tool."""

    execution_arn: str = Field(description="ARN of the execution")
    include_definition: bool = Field(
        default=False, description="If True, includes the state machine definition with Lambda ARNs (default: False)"
    )


class SearchStepFunctionExecutionsArgs(BaseModel):
    """Arguments for search_step_function_executions tool."""

    state_machine_arn: str = Field(description="ARN of the state machine")
    state_name: str = Field(default="", description='Filter by state name (supports regex, e.g., "Match.*Entity")')
    input_pattern: str = Field(
        default="", description='Regex pattern to match in state inputs (e.g., "customer_id.*12345")'
    )
    output_pattern: str = Field(
        default="", description='Regex pattern to match in state outputs (e.g., "entity_type.*company")'
    )
    status_filter: str = Field(default="", description="Optional status filter (RUNNING, SUCCEEDED, FAILED, etc.)")
    max_results: int = Field(default=50, description="Maximum number of executions to process (default: 50)")
    hours_back: int = Field(default=168, description="Number of hours to look back (default: 168 = 7 days)")
    include_definition: bool = Field(
        default=False, description="If True, includes the state machine definition with Lambda ARNs (default: False)"
    )


def is_aws_configured() -> bool:
    """Check if AWS credentials are configured (region is required, profile is optional)."""
    return bool(os.getenv("AWS_REGION"))


# Initialize Step Functions debugger only if AWS is configured
_sf_debugger: StepFunctionsDebugger | None = None
if is_aws_configured():
    _sf_debugger = StepFunctionsDebugger()


# Register list_state_machines tool
if is_aws_configured():

    @debug_tool(
        name="list_state_machines",
        description="List all Step Functions state machines in the account",
        category="stepfunctions",
        parameters=[
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of state machines to return (default: 100)",
                required=False,
                default=100,
            ),
        ],
        arg_model=ListStateMachinesArgs,
    )
    async def list_state_machines_registry(max_results: int = 100) -> dict:
        """List all Step Functions state machines in the account."""
        state_machines = _sf_debugger.list_state_machines(max_results=max_results)
        return {"state_machines": state_machines, "count": len(state_machines)}


# Register list_step_function_executions tool
if is_aws_configured():

    @debug_tool(
        name="list_step_function_executions",
        description="List executions for a Step Functions state machine",
        category="stepfunctions",
        parameters=[
            ToolParameter(
                name="state_machine_arn",
                type="string",
                description="ARN of the state machine",
                required=True,
            ),
            ToolParameter(
                name="status_filter",
                type="string",
                description="Optional status filter (RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED)",
                required=False,
                default="",
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of executions to return (default: 100)",
                required=False,
                default=100,
            ),
            ToolParameter(
                name="hours_back",
                type="number",
                description="Number of hours to look back (default: 168 = 7 days)",
                required=False,
                default=168,
            ),
        ],
        arg_model=ListStepFunctionExecutionsArgs,
    )
    async def list_step_function_executions_registry(
        state_machine_arn: str,
        status_filter: str = "",
        max_results: int = 100,
        hours_back: int = 168,
    ) -> dict:
        """List executions for a Step Functions state machine."""
        executions = _sf_debugger.list_executions(
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


# Register get_state_machine_definition tool
if is_aws_configured():

    @debug_tool(
        name="get_state_machine_definition",
        description="Get the state machine definition including ASL and extracted resources",
        category="stepfunctions",
        parameters=[
            ToolParameter(
                name="state_machine_arn",
                type="string",
                description="ARN of the state machine",
                required=True,
            ),
        ],
        arg_model=GetStateMachineDefinitionArgs,
    )
    async def get_state_machine_definition_registry(state_machine_arn: str) -> dict:
        """Get the state machine definition including ASL and extracted resources."""
        return _sf_debugger.get_state_machine_definition(state_machine_arn)


# Register get_step_function_execution_details tool
if is_aws_configured():

    @debug_tool(
        name="get_step_function_execution_details",
        description="Get detailed information about a specific Step Functions execution",
        category="stepfunctions",
        parameters=[
            ToolParameter(
                name="execution_arn",
                type="string",
                description="ARN of the execution",
                required=True,
            ),
            ToolParameter(
                name="include_definition",
                type="boolean",
                description="If True, includes the state machine definition with Lambda ARNs (default: False)",
                required=False,
                default=False,
            ),
        ],
        arg_model=GetStepFunctionExecutionDetailsArgs,
    )
    async def get_step_function_execution_details_registry(
        execution_arn: str, include_definition: bool = False
    ) -> dict:
        """Get detailed information about a specific Step Functions execution."""
        if include_definition:
            return _sf_debugger.get_execution_details_with_definition(execution_arn)
        return _sf_debugger.get_execution_details(execution_arn)


# Register search_step_function_executions tool
if is_aws_configured():

    @debug_tool(
        name="search_step_function_executions",
        description="Search Step Functions executions with advanced filtering",
        category="stepfunctions",
        parameters=[
            ToolParameter(
                name="state_machine_arn",
                type="string",
                description="ARN of the state machine",
                required=True,
            ),
            ToolParameter(
                name="state_name",
                type="string",
                description='Filter by state name (supports regex, e.g., "Match.*Entity")',
                required=False,
                default="",
            ),
            ToolParameter(
                name="input_pattern",
                type="string",
                description='Regex pattern to match in state inputs (e.g., "customer_id.*12345")',
                required=False,
                default="",
            ),
            ToolParameter(
                name="output_pattern",
                type="string",
                description='Regex pattern to match in state outputs (e.g., "entity_type.*company")',
                required=False,
                default="",
            ),
            ToolParameter(
                name="status_filter",
                type="string",
                description="Optional status filter (RUNNING, SUCCEEDED, FAILED, etc.)",
                required=False,
                default="",
            ),
            ToolParameter(
                name="max_results",
                type="number",
                description="Maximum number of executions to process (default: 50)",
                required=False,
                default=50,
            ),
            ToolParameter(
                name="hours_back",
                type="number",
                description="Number of hours to look back (default: 168 = 7 days)",
                required=False,
                default=168,
            ),
            ToolParameter(
                name="include_definition",
                type="boolean",
                description="If True, includes the state machine definition with Lambda ARNs (default: False)",
                required=False,
                default=False,
            ),
        ],
        arg_model=SearchStepFunctionExecutionsArgs,
    )
    async def search_step_function_executions_registry(
        state_machine_arn: str,
        state_name: str = "",
        input_pattern: str = "",
        output_pattern: str = "",
        status_filter: str = "",
        max_results: int = 50,
        hours_back: int = 168,
        include_definition: bool = False,
    ) -> dict:
        """Search Step Functions executions with advanced filtering."""
        executions = _sf_debugger.search_executions(
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
