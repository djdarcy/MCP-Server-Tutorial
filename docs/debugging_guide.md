# MCP Debugging Guide

## Understanding the MCP Architecture

### High-Level Flow
1. **Client (Claude Code)** connects to **Server (Your MCP Server)**
2. Client requests available tools via `list_tools()` RPC
3. Server responds with tool definitions (name, description, schema)
4. Client can call tools via `call_tool(name, arguments)` RPC
5. Server executes tool logic and returns results

### Key Components

#### 1. MCP Server (`server.py`)
- **Purpose**: Main entry point that handles MCP protocol
- **Key Functions**:
  - `list_tools()`: Returns available tools
  - `call_tool()`: Executes specific tools
  - `list_prompts()`: Returns available prompts (optional)
  - `get_prompt()`: Retrieves specific prompts (optional)

#### 2. Tools (`tools.py`)
- **Purpose**: Defines what tools are available
- **Key Functions**:
  - `get_all_tools()`: Returns list of Tool objects
  - Each Tool has: name, description, inputSchema

#### 3. Handlers (`handlers.py`)
- **Purpose**: Implements the actual tool logic
- **Key Functions**:
  - Individual handler functions for each tool
  - Input validation and processing
  - Response formatting

#### 4. Debug Utils (`debug_utils.py`)
- **Purpose**: Comprehensive logging and debugging
- **Key Functions**:
  - Structured logging
  - MCP message tracing
  - Performance monitoring

## Common MCP Issues and Debugging

### Issue 1: Server Not Recognized by Claude Code

**Symptoms:**
- Server doesn't appear in Claude Code
- No tools available in Claude Code
- Connection errors

**Debug Steps:**
1. **Check Server Registration**:
   ```bash
   # Verify server starts without errors
   python simple_mcp_server/server.py
   ```

2. **Check Claude Desktop Configuration**:
   - Location: `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
   - Ensure server is properly configured
   - Check command path and arguments

3. **Verify MCP Protocol Communication**:
   ```python
   # Add breakpoint in server.py at line 89 (list_tools handler)
   # Check if Claude Code is calling list_tools()
   ```

4. **Check Logs**:
   - Server logs in `logs/` directory
   - Look for connection attempts
   - Check for protocol errors

### Issue 2: Tools Not Appearing

**Symptoms:**
- Server starts but tools don't appear
- `list_tools()` returns empty list
- Tools appear but with missing information

**Debug Steps:**
1. **Test Tool Discovery**:
   ```python
   # Run the test suite
   python tests/test_server.py
   ```

2. **Check Tool Definitions**:
   ```python
   # Add breakpoint in tools.py at get_all_tools()
   # Verify tools are properly defined
   # Check inputSchema format
   ```

3. **Verify Tool Registration**:
   ```python
   # Add breakpoint in server.py at handle_list_tools()
   # Check if tools are being returned correctly
   ```

### Issue 3: Tool Execution Fails

**Symptoms:**
- Tools appear but fail when called
- Error messages in Claude Code
- Timeout errors

**Debug Steps:**
1. **Test Tool Handlers**:
   ```python
   # Add breakpoint in handlers.py at specific handler
   # Check input arguments
   # Verify handler logic
   ```

2. **Check Parameter Validation**:
   ```python
   # Add breakpoint in server.py at handle_call_tool()
   # Verify arguments match schema
   # Check for missing required parameters
   ```

3. **Verify Response Format**:
   ```python
   # Ensure handlers return correct format
   # Must return List[types.TextContent | types.ImageContent | types.EmbeddedResource]
   ```

### Issue 4: Server Crashes or Hangs

**Symptoms:**
- Server stops responding
- Claude Code shows connection errors
- No response to requests

**Debug Steps:**
1. **Check for Exceptions**:
   ```python
   # Add try-catch blocks in handlers
   # Check logs for stack traces
   ```

2. **Monitor Resource Usage**:
   ```python
   # Check if server is using too much memory/CPU
   # Look for infinite loops or blocking operations
   ```

3. **Test with Minimal Configuration**:
   ```python
   # Start with single tool
   # Add tools one by one to isolate issues
   ```

## VS Code Debugging Setup

### 1. Launch Configuration
The `.vscode/launch.json` provides these debug options:

- **Debug MCP Server**: Basic debugging with breakpoints
- **Debug MCP Server (Verbose)**: Detailed logging enabled
- **Test MCP Server Locally**: Debug the test suite

### 2. Key Breakpoints to Set

#### Server Initialization
- `server.py:56`: Server constructor
- `server.py:68`: Handler setup

#### Tool Discovery
- `server.py:89`: `list_tools()` handler
- `tools.py:20`: `get_all_tools()` function

#### Tool Execution
- `server.py:110`: `call_tool()` handler
- Individual handlers in `handlers.py`

#### Error Handling
- `server.py:169`: Error handling in `call_tool()`
- `handlers.py:200`: Error formatting

### 3. Debugging Workflow

1. **Start Debugging**:
   - Press F5 or select "Debug MCP Server"
   - Server starts in debug mode

2. **Set Breakpoints**:
   - Click line numbers to set breakpoints
   - Focus on key communication points

3. **Test with Claude Code**:
   - Connect Claude Code to server
   - Trigger tool discovery or execution
   - Step through code with F10/F11

4. **Inspect Variables**:
   - Check request arguments
   - Verify tool definitions
   - Examine response formats

## MCP Protocol Deep Dive

### Message Format
MCP uses JSON-RPC 2.0 format:

```json
{
  "jsonrpc": "2.0",
  "method": "list_tools",
  "params": {},
  "id": 1
}
```

### Tool Definition Format
```json
{
  "name": "tool_name",
  "description": "Tool description",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param1": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param1"]
  }
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "type": "text",
      "text": "Response content"
    }
  ],
  "id": 1
}
```

## Performance Optimization

### 1. Tool Discovery Optimization
- Cache tool definitions
- Minimize tool list size
- Use efficient data structures

### 2. Handler Optimization
- Minimize processing time
- Use async operations where possible
- Cache frequently accessed data

### 3. Error Handling
- Fail fast on invalid inputs
- Provide clear error messages
- Log errors for debugging

## Testing Strategies

### 1. Unit Testing
```python
# Test individual tools
pytest tests/test_tools.py

# Test handlers
pytest tests/test_handlers.py
```

### 2. Integration Testing
```python
# Test full server
python tests/test_server.py
```

### 3. Manual Testing
```python
# Test with Claude Code
# Verify tool discovery
# Test tool execution
# Check error handling
```

## Best Practices

### 1. Code Organization
- Separate concerns (server, tools, handlers)
- Use type hints
- Document functions clearly

### 2. Error Handling
- Validate inputs early
- Provide meaningful error messages
- Log errors with context

### 3. Logging
- Use structured logging
- Log MCP protocol messages
- Include timing information

### 4. Testing
- Test tool discovery
- Test parameter validation
- Test error conditions

## Troubleshooting Checklist

### Before Debugging:
- [ ] Python 3.8+ installed
- [ ] MCP package installed
- [ ] Virtual environment activated
- [ ] All dependencies installed

### Server Issues:
- [ ] Server starts without errors
- [ ] Tools are properly defined
- [ ] Handlers return correct format
- [ ] Error handling is implemented

### Client Issues:
- [ ] Claude Desktop configured correctly
- [ ] Server path is correct
- [ ] Environment variables set
- [ ] Claude Desktop restarted

### Communication Issues:
- [ ] MCP protocol messages logged
- [ ] Request/response format correct
- [ ] No timeout issues
- [ ] Error messages clear

---

*This guide provides a comprehensive approach to debugging MCP servers. Use it as a reference when diagnosing issues with your MCP implementations.*
