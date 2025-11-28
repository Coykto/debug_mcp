# Project Preferences

## Testing Philosophy
- **No unit tests** - the project owner considers them useless for this project
- **Verification via real tool calls** - test tools by actually calling them against real services
- **Manual integration testing** - use the MCP server locally and verify tool outputs
- **Tool verification tests** - see `tool-verification-tests.md` memory file for comprehensive test cases

## Important: Tool Verification
After implementing or modifying any MCP tool:
1. Read the `tool-verification-tests.md` memory file
2. Run relevant test cases to verify the tool works
3. Update the test file if you added/changed tools