# Chapter 2: Protocol Flow - Understanding MCP Communication

## Overview

The Model Context Protocol follows a specific flow of messages between client and server. Understanding this flow is helpful for debugging issues and for implementing MCP servers.

## The Complete MCP Protocol Flow

### 1. Server Discovery and Connection

**What Happens**: The MCP client (Claude Code) discovers and connects to your server.

**Process**:
1. Client reads configuration file (`claude_desktop_config.json`)
2. Client finds server command and arguments
3. Client launches server process
4. Client establishes stdio communication channel

**Example Configuration**:
```json
{
  "mcpServers": {
    "simple-mcp-debug": {
      "command": "python",
      "args": ["c:\\path\\to\\simple_mcp_server\\server.py"],
      "cwd": "c:\\path\\to\\project"
    }
  }
}
```

**Debug Points**:
- Server must start without errors
- Server must accept stdio input/output
- Server must implement proper JSON-RPC 2.0 protocol

### 2. Tool Discovery Phase

**What Happens**: Client discovers what tools are available on the server.

**Message Flow**:
```
Client → Server: list_tools() request
Server → Client: list_tools() response with tool definitions
```

**Actual Protocol Messages**:

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "list_tools",
  "params": {},
  "id": 1
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "name": "hello_world",
      "description": "A simple greeting tool",
      "inputSchema": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "description": "Name to greet"
          }
        },
        "required": []
      }
    }
  ],
  "id": 1
}
```

**Implementation in Our Server**:
```python
@self.server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """Handle tool discovery requests"""
    logger.info("📋 Client requesting tool list")
    
    tools = get_all_tools()
    logger.info(f"📋 Returning {len(tools)} tools")
    
    return tools
```

**Common Issues**:
- Server not responding to `list_tools()` requests
- Invalid tool schema causing client errors
- Missing required fields in tool definitions

### 3. Tool Execution Phase

**What Happens**: Client executes a specific tool with parameters.

**Message Flow**:
```
Client → Server: call_tool(name, arguments) request
Server → Client: call_tool() response with results
```

**Actual Protocol Messages**:

**Request**:
```json
{
  "jsonrpc": "2.0",
  "method": "call_tool",
  "params": {
    "name": "hello_world",
    "arguments": {
      "name": "Claude"
    }
  },
  "id": 2
}
```

**Response**:
```json
{
  "jsonrpc": "2.0",
  "result": [
    {
      "type": "text",
      "text": "Hello, Claude! 👋\n\nGenerated at: 2025-07-13T10:30:00"
    }
  ],
  "id": 2
}
```

**Implementation in Our Server**:
```python
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool execution requests"""
    logger.info(f"🔧 Client requesting tool execution: {name}")
    logger.info(f"🔧 Arguments: {arguments}")
    
    # Route to appropriate handler
    if name == "hello_world":
        result = await handle_hello_world(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    # Format response
    return [types.TextContent(type="text", text=result)]
```

## Detailed Protocol Analysis

### JSON-RPC 2.0 Structure

Every MCP message follows JSON-RPC 2.0 format:

**Request Format**:
```json
{
  "jsonrpc": "2.0",      // Protocol version
  "method": "method_name", // Method to call
  "params": {...},        // Method parameters
  "id": 123              // Request ID for matching responses
}
```

**Response Format**:
```json
{
  "jsonrpc": "2.0",      // Protocol version
  "result": {...},       // Method result (success)
  "id": 123              // Matches request ID
}
```

**Error Format**:
```json
{
  "jsonrpc": "2.0",      // Protocol version
  "error": {             // Error object
    "code": -32000,      // Error code
    "message": "Error description",
    "data": {...}        // Additional error data
  },
  "id": 123              // Matches request ID
}
```

### MCP-Specific Methods

#### 1. `list_tools`
- **Purpose**: Tool discovery
- **Parameters**: None
- **Returns**: Array of tool definitions
- **When Called**: Client startup, tool refresh

#### 2. `call_tool`
- **Purpose**: Tool execution
- **Parameters**: `name` (string), `arguments` (object)
- **Returns**: Array of content objects
- **When Called**: User invokes a tool

#### 3. `list_prompts` (Optional)
- **Purpose**: Prompt template discovery
- **Parameters**: None
- **Returns**: Array of prompt definitions
- **When Called**: Client startup, prompt refresh

#### 4. `get_prompt` (Optional)
- **Purpose**: Prompt template retrieval
- **Parameters**: `name` (string), `arguments` (object)
- **Returns**: Prompt result object
- **When Called**: User requests a prompt

## Tracing Protocol Flow in Practice

### Setting Up Protocol Tracing

Our server includes comprehensive protocol tracing:

```python
def log_mcp_message(message_type: str, direction: str, data: dict):
    """Log MCP protocol messages for debugging"""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message_type": message_type,
        "direction": direction,
        "data": data
    }
    
    logger.info(f"MCP {message_type} {direction}: {json.dumps(log_entry)}")
```

### Example Protocol Trace

**Tool Discovery**:
```
[10:30:00] MCP list_tools request: {"params": {}}
[10:30:00] MCP list_tools response: {"tool_count": 5}
```

**Tool Execution**:
```
[10:30:15] MCP call_tool request: {"tool_name": "hello_world", "arguments": {"name": "Test"}}
[10:30:15] MCP call_tool response: {"success": true, "response_length": 45}
```

## Common Protocol Issues and Solutions

### Issue 1: Server Not Responding

**Symptoms**:
- Client can't discover tools
- No response to `list_tools()` requests
- Connection timeouts

**Debug Steps**:
1. Check server startup logs
2. Verify server is listening on stdio
3. Test server independently

**Solution**:
```python
# Add startup logging
logger.info("🌟 Server starting up...")
logger.info("📊 Server ready to accept connections")

# Test with our test suite
python tests/test_server.py
```

### Issue 2: Invalid Tool Schema

**Symptoms**:
- Tools discovered but not usable
- Client errors when trying to call tools
- Schema validation failures

**Debug Steps**:
1. Validate tool schema format
2. Check required vs optional parameters
3. Verify parameter types

**Solution**:
```python
# Validate tool definitions
def validate_tool_schema(tool):
    required_fields = ["name", "description", "inputSchema"]
    for field in required_fields:
        if not hasattr(tool, field):
            raise ValueError(f"Tool missing required field: {field}")
```

### Issue 3: Tool Execution Errors

**Symptoms**:
- Tools discoverable but fail when called
- Error responses from server
- Timeout or crash during execution

**Debug Steps**:
1. Add logging to tool handlers
2. Validate input parameters
3. Check error handling

**Solution**:
```python
async def handle_call_tool(name: str, arguments: dict):
    try:
        # Log request
        logger.info(f"Executing tool: {name}")
        
        # Validate arguments
        validate_arguments(name, arguments)
        
        # Execute tool
        result = await execute_tool(name, arguments)
        
        # Log success
        logger.info(f"Tool execution successful: {name}")
        return result
        
    except Exception as e:
        # Log error
        logger.error(f"Tool execution failed: {name}, error: {str(e)}")
        raise
```

## Advanced Protocol Features

### 1. Streaming Responses

For long-running operations, MCP supports streaming:

```python
# Stream results as they become available
async def handle_streaming_tool():
    for chunk in process_data():
        yield types.TextContent(type="text", text=chunk)
```

### 2. Resource Management

MCP can handle file and resource references:

```python
# Return file references
return [types.EmbeddedResource(
    type="resource",
    resource={
        "uri": "file:///path/to/file.txt",
        "mimeType": "text/plain"
    }
)]
```

### 3. Error Handling Patterns

**Graceful Error Handling**:
```python
try:
    result = await risky_operation()
    return [types.TextContent(type="text", text=result)]
except ValidationError as e:
    return [types.TextContent(type="text", text=f"Validation Error: {str(e)}")]
except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    return [types.TextContent(type="text", text="Internal server error")]
```

## Testing Protocol Flow

### Unit Tests for Protocol Handlers

```python
async def test_list_tools_protocol():
    """Test tool discovery protocol"""
    # Simulate client request
    tools = await handle_list_tools()
    
    # Verify response format
    assert isinstance(tools, list)
    assert all(hasattr(tool, 'name') for tool in tools)
    assert all(hasattr(tool, 'description') for tool in tools)
    assert all(hasattr(tool, 'inputSchema') for tool in tools)

async def test_call_tool_protocol():
    """Test tool execution protocol"""
    # Simulate client request
    result = await handle_call_tool("hello_world", {"name": "Test"})
    
    # Verify response format
    assert isinstance(result, list)
    assert all(hasattr(item, 'type') for item in result)
    assert all(hasattr(item, 'text') for item in result)
```

### Integration Tests

```python
# Test complete protocol flow
async def test_full_protocol_flow():
    # 1. Tool discovery
    tools = await handle_list_tools()
    assert len(tools) > 0
    
    # 2. Tool execution
    for tool in tools:
        # Test with minimal valid arguments
        result = await handle_call_tool(tool.name, {})
        assert result is not None
```

## Protocol Performance Considerations

### 1. Tool Discovery Optimization

- Cache tool definitions
- Minimize tool list size
- Use efficient data structures

### 2. Tool Execution Optimization

- Validate arguments early
- Use async operations for I/O
- Implement timeouts for long operations

### 3. Error Handling Optimization

- Fail fast on invalid inputs
- Provide clear error messages
- Log errors for debugging

## Next Steps

After understanding protocol flow:
1. Learn about **Tool Registration** (Chapter 3)
2. Understand **Authentication** (Chapter 4)
3. Implement **Error Handling** (Chapter 5)
4. Set up **Debugging** (Chapter 6)

## Key Takeaways

- MCP follows a request/response pattern using JSON-RPC 2.0
- Tool discovery happens first, then tool execution
- Proper logging is essential for debugging protocol issues
- Error handling must be implemented at every protocol level
- Testing protocol handlers independently helps isolate issues

---

*This chapter covered the complete MCP protocol flow. The next chapter will focus on how tools are registered and managed within the server.*
