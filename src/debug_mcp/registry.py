"""Central registry for debug tools with category-based discovery."""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


class ToolParameter(BaseModel):
    """Schema for a tool parameter."""

    name: str
    type: str  # "string", "integer", "boolean", "list[str]"
    description: str
    required: bool = True
    default: Any = None


class ToolSchema(BaseModel):
    """Complete schema for a tool."""

    name: str
    description: str
    category: str  # "cloudwatch", "stepfunctions", "langsmith", "jira"
    parameters: list[ToolParameter]


@dataclass
class ToolRegistryEntry:
    """Registry entry combining schema + handler."""

    schema: ToolSchema
    handler: Callable[..., Awaitable[dict[str, Any]]]
    arg_model: type[BaseModel] | None = None


class ToolRegistry:
    """Central registry for all debug tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolRegistryEntry] = {}
        self._categories: dict[str, str] = {
            "cloudwatch": "CloudWatch Logs tools for querying and analyzing AWS logs",
            "stepfunctions": "Step Functions tools for debugging state machine executions",
            "langsmith": "LangSmith tools for tracing and debugging LLM applications",
            "jira": "Jira tools for searching and viewing tickets",
        }

    def register(
        self,
        schema: ToolSchema,
        handler: Callable[..., Awaitable[dict[str, Any]]],
        arg_model: type[BaseModel] | None = None,
    ) -> None:
        """Register a tool with its schema and handler."""
        self._tools[schema.name] = ToolRegistryEntry(
            schema=schema,
            handler=handler,
            arg_model=arg_model,
        )

    async def execute(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with validated arguments."""
        entry = self._tools.get(tool_name)

        if not entry:
            available = [t.schema.name for t in self._tools.values()]
            raise ValueError(f"Unknown tool: {tool_name}. Available tools: {available}")

        # Validate with Pydantic model if available
        if entry.arg_model:
            try:
                validated = entry.arg_model(**arguments)
                arguments = validated.model_dump()
            except Exception as e:
                raise ValueError(f"Invalid arguments: {e}") from e

        return await entry.handler(**arguments)

    def list_categories(self) -> list[dict[str, str]]:
        """List all available tool categories with descriptions."""
        return [{"name": name, "description": desc} for name, desc in self._categories.items()]

    def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """List tools, optionally filtered by category."""
        tools: list[dict[str, Any]] = []
        for entry in self._tools.values():
            if category is None or entry.schema.category == category:
                tools.append(
                    {
                        "name": entry.schema.name,
                        "description": entry.schema.description,
                        "category": entry.schema.category,
                        "parameters": [p.model_dump() for p in entry.schema.parameters],
                    }
                )
        return sorted(tools, key=lambda t: (t["category"], t["name"]))


def debug_tool(
    name: str,
    description: str,
    category: str,
    parameters: list[ToolParameter],
    arg_model: type[BaseModel] | None = None,
) -> Callable[[Callable[..., Awaitable[dict]]], Callable[..., Awaitable[dict]]]:
    """Decorator to register a debug tool with the global registry."""

    def decorator(func: Callable[..., Awaitable[dict]]) -> Callable[..., Awaitable[dict]]:
        schema = ToolSchema(
            name=name,
            description=description,
            category=category,
            parameters=parameters,
        )
        registry.register(schema, func, arg_model)
        return func

    return decorator


# Global registry instance
registry = ToolRegistry()
