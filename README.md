# MCP Server Tutorial

A detailed, hands-on tutorial for learning MCP (Model Context Protocol) server development with working examples and debugging tools.

## Project Overview

This tutorial project creates a minimal, well-documented MCP server designed to help you understand:
- How MCP servers work
- How to debug MCP servers with VS Code
- How to diagnose common MCP issues
- How to register servers with Claude Desktop
- How to build your own MCP tools and servers

## Quick Start

### 1. Setup Environment

```bash
# Run the setup script
scripts\setup.bat

# Or manually:
python -m venv venv
venv\Scripts\activate.bat
pip install mcp
```

### 2. Test the Server

```bash
# Activate virtual environment
venv\Scripts\activate.bat

# Run tests (basic test without Unicode issues)
python tests\test_simple.py

# Or run full test suite (may have Unicode display issues on Windows)
python tests\test_server.py

# Or use the safe test runner for Windows
scripts\test_safe.bat
```

**Note for Windows users:** If you see Unicode encoding errors, use `scripts\test_safe.bat` which redirects output to `test_output.log`.

### 3. Debug the Server

1. Open this folder in VS Code
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Debug MCP Server"
4. Press F5 to start debugging

Key breakpoints to set:
- `server.py:89` - Tool discovery
- `server.py:110` - Tool execution
- `handlers.py:25` - Individual tool handlers

### 4. Register with Claude Code

1. Copy the configuration from `config\claude_desktop.json`
2. Add to your Claude Desktop configuration file
3. Restart Claude Desktop
4. The server should appear as "simple-mcp-debug"

## Project Structure

```
MCPDebugTest/
├── CLAUDE.md                    # Detailed learning documentation
├── README.md                    # This file
├── setup.bat                    # Windows setup script
├── requirements.txt             # Python dependencies
├── simple_mcp_server/           # Main MCP server code
│   ├── server.py               # MCP server implementation
│   ├── tools.py                # Tool definitions
│   ├── handlers.py             # Tool handlers
│   └── debug_utils.py          # Debugging utilities
├── tests/                       # Test scripts
│   └── test_server.py          # Server validation tests
├── config/                      # Configuration files
│   └── claude_desktop.json     # Claude Desktop config
├── .vscode/                     # VS Code configuration
│   └── launch.json             # Debug configurations
└── logs/                        # Debug logs (created on first run)
```

## Available Tools

The MCP server exposes these tools for testing:

### 1. hello_world
Simple greeting tool
- **Parameters**: `name` (optional)
- **Purpose**: Basic functionality test

### 2. echo
Echo back messages with optional prefix
- **Parameters**: `message` (required), `prefix` (optional)
- **Purpose**: Input/output testing

### 3. get_time
Get current time in various formats
- **Parameters**: `format` (iso/readable/timestamp), `timezone` (optional)
- **Purpose**: System interaction testing

### 4. math_add
Add two numbers together
- **Parameters**: `a` (required), `b` (required)
- **Purpose**: Parameter validation testing

### 5. debug_info
Get server debug information
- **Parameters**: `include_tools` (boolean), `include_stats` (boolean)
- **Purpose**: Server introspection

## Debugging Features

### Logging
- Detailed MCP protocol message logging
- Performance metrics
- Error tracking with stack traces
- Separate log files for different aspects

### VS Code Integration
- Pre-configured debug launch configurations
- Breakpoint-friendly code structure
- Variable inspection capabilities
- Step-through debugging

### Test Suite
- Automated tool discovery testing
- Parameter validation testing
- Error handling validation
- Handler functionality testing

## Understanding MCP Protocol

### Tool Discovery Flow
1. Client connects to server
2. Client calls `list_tools()` RPC
3. Server returns available tools with schemas
4. Client can now call individual tools

### Tool Execution Flow
1. Client calls `call_tool(name, arguments)` RPC
2. Server validates arguments against schema
3. Server routes to appropriate handler
4. Handler processes request and returns result
5. Server formats response and sends back

### Key Debugging Points
- **Tool Registration**: Set breakpoints in `get_all_tools()`
- **Tool Discovery**: Set breakpoints in `handle_list_tools()`
- **Tool Execution**: Set breakpoints in `handle_call_tool()`
- **Individual Handlers**: Set breakpoints in specific tool handlers

## Common Issues and Solutions

### Issue: Tools Not Appearing in Claude Code
**Debug Steps:**
1. Check Claude Desktop configuration
2. Verify server starts without errors
3. Check `list_tools()` response in logs
4. Restart Claude Desktop

### Issue: Tool Execution Fails
**Debug Steps:**
1. Check parameter validation in logs
2. Set breakpoints in tool handlers
3. Verify handler return format
4. Check error handling paths

### Issue: Server Won't Start
**Debug Steps:**
1. Check Python environment
2. Verify MCP library installation
3. Check import paths
4. Review startup logs

### Issue: Unicode/Emoji Characters in Windows Console
**Problem:** Windows Command Prompt may not display Unicode characters properly
**Solutions:**
1. Use `scripts\test_safe.bat` which redirects output to a file
2. Use Windows Terminal or PowerShell instead of Command Prompt
3. Set console code page: `chcp 65001` before running tests
4. Check `test_output.log` for full test results

### Issue: Test Suite Crashes with UnicodeEncodeError
**Problem:** Python logging fails when trying to output Unicode characters to Windows console
**Solutions:**
1. Run tests with `scripts\test_safe.bat` to redirect output
2. Use the simplified test runner: `python tests\test_simple.py`
3. Check log files in the `logs\` directory for detailed output
4. The server functionality works correctly; only the console output has Unicode issues

## Next Steps

Once you understand this tutorial server:

1. **Build Your Own Server**: Use the same patterns to create your own MCP server
2. **Explore Advanced Features**: Add more complex tools and state management
3. **Deploy to Production**: Follow the production deployment guide in the docs
4. **Contribute Back**: Share improvements and additional examples with the community

## Learning Resources

- [MCP Specification](https://modelcontextprotocol.io/specification)
- [Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Claude Desktop Documentation](https://claude.ai/docs)
- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)

## Contributing

This is a learning project. Feel free to:
- Add more test tools
- Enhance debugging capabilities
- Improve documentation
- Add more comprehensive tests

---

*Happy debugging! 🐛🔍*
