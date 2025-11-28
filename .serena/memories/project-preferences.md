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

## Subagent Environment Variables Pattern
Subagents don't inherit shell environment variables. When delegating tasks that need credentials:

1. **First, read env values from the user's shell** using Bash:
   ```bash
   echo "VAR_NAME=${VAR_NAME}"
   ```

2. **Then pass them explicitly in the subagent prompt**, e.g.:
   ```
   Environment variables to use:
   - JIRA_HOST=provectus-dev.atlassian.net
   - JIRA_EMAIL=ebasmov@provectus.com
   - AWS_PROFILE=your-profile
   ```

3. **For sensitive tokens**, read the actual value and pass it to subagent:
   ```bash
   echo "${JIRA_API_TOKEN}"
   ```
   Then include in subagent prompt: `os.environ['JIRA_API_TOKEN'] = '<value>'`
   
   **IMPORTANT**: Never store tokens in memory files (they get committed). Always read fresh from shell.

**Known configuration for this project:**
- Jira: host=`provectus-dev.atlassian.net`, email=`ebasmov@provectus.com`, project=`IGAL`
- AWS: profile from env, region may need explicit setting
- `JIRA_API_TOKEN` is in the user's environment
