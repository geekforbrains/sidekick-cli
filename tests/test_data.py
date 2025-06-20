"""Shared test data for sidekick tests."""

# Valid MCP server configurations
VALID_MCP_SERVER = {"command": "uvx", "args": ["mcp-server-fetch"]}

VALID_MCP_SERVER_WITH_NAME = {
    "command": "uvx",
    "args": ["mcp-server-fetch"],
    "name": "Fetch Server",
}

VALID_MCP_SERVER_WITH_ENV = {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-brave-search"],
    "env": {"BRAVE_API_KEY": "test-key"},
}

VALID_MCP_CONFIG = {"mcpServers": {"fetch": VALID_MCP_SERVER}}

# Invalid MCP server configurations
INVALID_MCP_SERVER_NOT_DICT = "not a dict"
INVALID_MCP_SERVER_NO_COMMAND = {"args": ["test"]}
INVALID_MCP_SERVER_NO_ARGS = {"command": "test"}
INVALID_MCP_SERVER_EMPTY_ARGS = {"command": "test", "args": []}
INVALID_MCP_SERVER_NON_LIST_ARGS = {"command": "test", "args": "not-a-list"}
INVALID_MCP_SERVER_NON_DICT_ENV = {"command": "test", "args": ["arg"], "env": "not-a-dict"}

# Mock tool calls
MOCK_TOOL_CALL = {
    "tool_name": "test_tool",
    "tool_call_id": "tc_123",
    "tool_args": {"arg1": "value1"},
}
