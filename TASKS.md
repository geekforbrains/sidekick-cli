# Code Review Tasks

## Development Rules

1. **NO backwards compatibility** - Do NOT try to support backwards compatibility/legacy code with these updates. The goal is a clean slate. Clean up old code/files as needed.

2. **Minimal comments** - Do NOT add unnecessary inline comments, only if they're actually helpful.

3. **Import organization** - Always put Python imports at the top of the file.

4. **Test after each task** - After every task, run `make lint` and `make test` to ensure nothing has broken.

5. **No new tests** - Do NOT implement new tests, we'll do that later. However, if a test breaks because of changes, ensure you fix either the code or refactor the test depending on what makes sense.

## Task #1: Refactor Global State in session.py (COMPLETED)

### Issue
The session module uses global mutable state variables throughout the application, making it difficult to test, maintain, and reason about data flow.

### Problems Found
- Multiple global variables defined at module level (lines 4-19)
- State is mutated directly from various modules without encapsulation
- No clear ownership or lifecycle management of session data
- Difficult to unit test due to persistent state between tests
- Potential thread safety issues if used concurrently
- Hidden dependencies make code flow hard to trace

### Solution
- Convert global variables to a Session dataclass
- Use dataclass with field factory for mutable defaults
- Maintain single global instance for backward compatibility
- Preserve existing API to minimize code changes

### Critical Changes
- Create Session dataclass with all current global variables as fields
- Initialize mutable fields using field(default_factory=...)
- Keep init() method as instance method
- Create single global session instance
- Update import statements where needed

### Related Files
- `src/sidekick/session.py` - Primary file to refactor
- `src/sidekick/main.py` - Heavy user of session state
- `src/sidekick/agent.py` - Accesses session for model info and usage tracking
- `src/sidekick/commands.py` - Likely uses session state
- Various test files that may need session mocking

### Benefits
- Improved testability with fresh instances
- Better IDE support and type checking
- Clear data structure visibility
- Easy migration path to dependency injection
- No breaking changes to existing code
- Foundation for future improvements

## Task #2: Fix Hardcoded File Path in agent.py (COMPLETED)

### Issue
The _get_prompt function uses a relative hardcoded path that breaks when the package is installed via pip and assumes the working directory is always the project root.

### Problems Found
- Hardcoded relative path: `./src/sidekick/prompts/{name}.txt` (line 13)
- No error handling for missing files
- Breaks when package is installed via pip
- Not portable across different environments
- Platform-dependent path separator

### Solution
- Use pathlib.Path with __file__ to get relative path
- Add proper error handling for missing files
- Use Path.read_text() for cleaner code
- Platform-independent path handling

### Critical Changes
- Import pathlib.Path
- Change _get_prompt to use Path(__file__).parent / "prompts"
- Add try/except for FileNotFoundError
- Return meaningful error message

### Related Files
- `src/sidekick/agent.py` - Contains the problematic function
- `src/sidekick/prompts/system.txt` - The prompt file being loaded
- Tests that may mock file operations

### Benefits
- Works correctly when installed as package
- Platform independent
- Better error messages
- More maintainable
- Follows Python best practices

## Task #3: Fix Typo in UI Module (COMPLETED)

### Issue
Simple typo in the THINKING_MESSAGES list that should be corrected.

### Problems Found
- "Calculating trajenctories..." should be "Calculating trajectories..." (line 51)

### Solution
- Fix the spelling of "trajectories"

### Critical Changes
- Change "trajenctories" to "trajectories" in THINKING_MESSAGES

### Related Files
- `src/sidekick/ui.py` - Contains the typo

### Benefits
- Professional appearance
- No confusion for users

## Task #4: Remove Unnecessary Async Functions in UI Module (COMPLETED)

### Issue
Most UI functions are marked as async but perform no asynchronous operations, creating unnecessary overhead and complexity.

### Problems Found
- 14 functions marked as async that only call synchronous console.print()
- Only confirm_tool_call() genuinely needs to be async
- Creates confusion about which functions are truly asynchronous
- Adds unnecessary await calls throughout the codebase
- Makes testing more complex than needed

### Solution
- Remove async keyword from functions that don't need it
- Keep async only for confirm_tool_call()
- Update all calls to these functions to remove await

### Critical Changes
- Remove async/await from: banner, info, error, warning, success, bullet, muted, agent, line, dump, help, version, update_available, usage
- Update all calls throughout codebase to remove await
- Keep async for confirm_tool_call only

### Related Files
- `src/sidekick/ui.py` - Contains the functions
- `src/sidekick/main.py` - Many UI function calls
- `src/sidekick/agent.py` - UI function calls
- `src/sidekick/commands.py` - Likely has UI function calls
- Any other files calling UI functions

### Benefits
- Simpler code without unnecessary async overhead
- Clearer distinction between sync and async operations
- Easier testing
- Better performance (marginal)
- More pythonic code

## Task #5: DRY Violation - Duplicated Error Handling in Tools (COMPLETED)

### Issue
All tool files have identical error handling patterns with duplicated code for formatting error messages and calling ui.error.

### Problems Found
- Pattern `err_msg = "..."; await ui.error(err_msg); return err_msg` repeated in every tool
- Inconsistent exception types caught (some catch FileNotFoundError, others don't)
- Duplicated error formatting logic across all tools
- Makes it hard to maintain consistent error handling

### Solution
- Create a decorator or context manager for tool error handling
- Standardize which exceptions each tool should catch
- Centralize error message formatting
- Consider returning structured error responses instead of strings

### Critical Changes
- Add error handling utility (decorator or context manager)
- Refactor all tool functions to use centralized error handling
- Ensure consistent exception handling across tools

### Related Files
- `src/sidekick/tools/read_file.py`
- `src/sidekick/tools/write_file.py`
- `src/sidekick/tools/update_file.py`
- `src/sidekick/tools/run_command.py`
- New utility file for error handling

### Benefits
- DRY principle compliance
- Consistent error handling
- Easier to maintain and update error logic
- Better error message formatting
- Cleaner tool implementations

## Task #6: Standardize Exception Handling in Config Module (COMPLETED)

### Issue
The config module defines custom exceptions (ConfigError and ConfigValidationError) but uses them inconsistently, making error handling unpredictable for callers.

### Problems Found
- read_config_file() raises standard exceptions directly (FileNotFoundError, PermissionError, JSONDecodeError)
- update_config_file() wraps exceptions in ConfigError
- validate_config_structure() uses ConfigValidationError consistently
- Inconsistent error handling patterns across the module

### Solution
- Wrap all exceptions in appropriate custom exceptions
- Use ConfigError for file/IO related issues
- Use ConfigValidationError for validation issues
- Maintain original exception as cause for debugging

### Critical Changes
- Modify read_config_file() to wrap FileNotFoundError in ConfigError
- Wrap PermissionError in ConfigError with original as cause
- Wrap JSONDecodeError in ConfigValidationError
- Ensure consistent exception types across module

### Related Files
- `src/sidekick/config.py` - Main file to update
- `src/sidekick/main.py` - Already handles these exceptions properly
- Tests that mock config operations

### Benefits
- Predictable error handling for callers
- Consistent API across config module
- Better error categorization
- Easier to handle config errors uniformly
- Original exceptions preserved for debugging

## Task #7: Create Config Directory If Missing (COMPLETED)

### Issue
The config file is saved to ~/.config/sidekick.json but the ~/.config directory might not exist on all systems, causing file write failures.

### Problems Found
- get_config_path() assumes ~/.config exists
- No directory creation before writing config
- Could fail on fresh systems or minimal environments
- Windows systems less likely to have ~/.config

### Solution
- Add directory creation with parents=True
- Create directory before any config write operations
- Use Path.mkdir(parents=True, exist_ok=True)

### Critical Changes
- Update update_config_file() to create directory
- Update any other config write operations
- Ensure directory creation happens before file operations

### Related Files
- `src/sidekick/config.py` - Add directory creation
- `src/sidekick/setup.py` - May also write config

### Benefits
- Works on fresh systems
- No manual directory creation needed
- Cross-platform compatibility
- Prevents write failures
- Better user experience

## Task #8: Consolidate MCP Server Validation Logic (COMPLETED)

### Issue
Duplicate validation logic exists in two places for MCP server configuration, violating DRY principle and making maintenance harder.

### Problems Found
- parse_mcp_servers in config.py validates server structure
- validate_server_config in servers.py performs nearly identical validation
- Different exception types used (ConfigValidationError vs ValueError)
- Slight variations in validation checks
- Same validation logic maintained in two places

### Solution
- Keep validation in config.py as the single source of truth
- Remove validate_server_config from servers.py
- Update create_mcp_server to use parse_mcp_servers validation
- Ensure consistent exception types

### Critical Changes
- Remove validate_server_config function
- Update create_mcp_server to rely on prior validation
- Ensure parse_mcp_servers validates individual servers thoroughly
- Consider extracting single server validation if needed

### Related Files
- `src/sidekick/config.py` - Contains parse_mcp_servers
- `src/sidekick/mcp/servers.py` - Remove duplicate validation
- Tests for both modules

### Benefits
- Single source of truth for validation
- Easier maintenance
- Consistent validation behavior
- Reduced code duplication
- DRY principle compliance

## Task #9: Improve MCP Server Load Error Visibility (COMPLETED)

### Issue
MCP server loading errors are swallowed and logged, returning empty list, making it hard to distinguish between no servers configured and load failures.

### Problems Found
- load_mcp_servers catches all exceptions and returns []
- Users don't see which MCP servers failed to load
- No distinction between "no servers" and "load error"
- Silent failures could confuse users

### Solution
- Keep CLI running but show clear error messages to users
- Log errors and also display them via UI
- Show which servers loaded successfully vs failed
- Consider showing partial success state

### Critical Changes
- Add UI error/warning calls for failed server loads
- Show specific server names that failed
- Continue loading other servers after failures
- Display summary of loaded vs failed servers

### Related Files
- `src/sidekick/mcp/servers.py` - Update error handling
- `src/sidekick/main.py` - May need to handle error display

### Benefits
- Users see which MCP servers failed
- CLI remains functional
- Better debugging information
- Clear feedback on server status
- No silent failures

## Task #10: Remove Deprecated get_configured_servers Function (COMPLETED)

### Issue
The get_configured_servers function is marked as deprecated but still actively used throughout the codebase.

### Problems Found
- Function marked deprecated in comment but still used
- Used in main.py and agent.py
- Creates confusion about which function to use
- Unnecessary wrapper function

### Solution
- Update all calls to use load_mcp_servers directly
- Remove get_configured_servers function
- Remove deprecation comment
- Update any imports

### Critical Changes
- Change main.py:49 to use load_mcp_servers
- Change agent.py:176 to use load_mcp_servers
- Remove get_configured_servers function definition
- Update imports if needed

### Related Files
- `src/sidekick/mcp/servers.py` - Remove deprecated function
- `src/sidekick/main.py` - Update function call
- `src/sidekick/agent.py` - Update function call
- Any other files importing this function

### Benefits
- Cleaner codebase
- No confusion about which function to use
- Consistent API
- Removed dead code

## Task #11: Add Stack Traces to MCP Error Logging

### Issue
Exception logging in load_mcp_servers loses stack trace information, making debugging difficult.

### Problems Found
- Generic exception catches don't include stack traces
- Hard to debug why server creation failed
- Only error message is logged, not full context
- ValueError catches could benefit from more info

### Solution
- Add exc_info=True to exception logging
- Include stack traces for debugging
- Keep user-facing messages simple
- Improve debugging capability

### Critical Changes
- Add exc_info=True to ValueError logging
- Add exc_info=True to generic Exception logging
- Ensure logs capture full error context

### Related Files
- `src/sidekick/mcp/servers.py` - Update logger.warning calls

### Benefits
- Better debugging information
- Stack traces in logs
- Easier to diagnose issues
- Maintains simple user messages
- Improved troubleshooting

## Task #12: Create Panel Helper Function in UI Module

### Issue
Panel creation logic is duplicated 6 times in the UI module with nearly identical patterns, violating DRY principle.

### Problems Found
- Same panel creation pattern in error(), agent(), dump(), confirm_tool_call(), help()
- Repeated Padding configuration
- Duplicated console.print with padding wrapper
- Same title_align="left" everywhere
- Similar structure with only title and border_style changing

### Solution
- Create a helper function for panel creation
- Standardize padding values as constants
- Centralize panel display logic
- Keep consistent styling

### Critical Changes
- Add create_panel() helper function
- Add display_panel() for print with padding
- Define padding constants
- Refactor all panel creation to use helper

### Related Files
- `src/sidekick/ui.py` - Refactor panel creation

### Benefits
- DRY principle compliance
- Easier to modify panel styling globally
- Reduced code duplication
- Consistent panel appearance
- Cleaner function implementations

## Task #13: Consolidate Name Formatting Functions

### Issue
Multiple functions across the codebase handle name formatting for display purposes with different implementations.

### Problems Found
- format_tool_name() in ui.py uses TOOL_DISPLAY_NAMES lookup
- _format_display_name() in mcp/servers.py does string manipulation
- _format_tool_display() in agent.py handles tool display
- Similar purpose but different implementations
- No central place for display formatting logic

### Solution
- Create a display formatting utility module
- Consolidate all name formatting logic
- Handle both tool names and server names
- Provide consistent formatting rules

### Critical Changes
- Create new utils/display.py module
- Move format_tool_name to utilities
- Move _format_display_name to utilities
- Update imports across codebase
- Consolidate _format_tool_display logic

### Related Files
- `src/sidekick/ui.py` - Remove format_tool_name
- `src/sidekick/mcp/servers.py` - Remove _format_display_name
- `src/sidekick/agent.py` - Update _format_tool_display
- New utils/display.py file

### Benefits
- Single source for display logic
- Consistent formatting across app
- Easier to maintain
- Better organization
- Reusable formatting functions
