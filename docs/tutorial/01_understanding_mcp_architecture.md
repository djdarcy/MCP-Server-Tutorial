# Chapter 1: Understanding MCP Architecture

## Overview

The Model Context Protocol (MCP) is a communication protocol that enables AI assistants to interact with external tools and services. Understanding the architecture is fundamental to building effective MCP servers and debugging integration issues.

## What is MCP?

MCP is a **client-server protocol** that allows AI assistants (clients) to discover and execute tools provided by external servers. Think of it as a standardized way for AI systems to access external capabilities.

### Key Components

```
┌─────────────────┐    MCP Protocol   ┌─────────────────┐
│                 │ ◄──────────────── │                 │
│   MCP Client    │                   │   MCP Server    │
│ (Claude Code)   │ ────────────────► │ (Your Server)   │
│                 │                   │                 │
└─────────────────┘                   └─────────────────┘
```

## Core Architecture Principles

### 1. Protocol-Based Communication

MCP uses **JSON-RPC 2.0** as its underlying communication protocol. This means:
- All messages are JSON formatted
- Request/response patterns are standardized
- Error handling follows JSON-RPC conventions

**Example Message Flow**:
```json
// Client requests available tools
{
  "jsonrpc": "2.0",
  "method": "list_tools",
  "params": {},
  "id": 1
}

// Server responds with tool definitions
{
  "jsonrpc": "2.0",
  "result": [
    {
      "name": "hello_world",
      "description": "A simple greeting tool",
      "inputSchema": {
        "type": "object",
        "properties": {
          "name": {"type": "string"}
        }
      }
    }
  ],
  "id": 1
}
```

### 2. Tool-Centric Design

Everything in MCP revolves around **tools**:
- Tools are discrete functions that servers expose
- Each tool has a name, description, and input schema
- Tools are discovered dynamically by clients
- Tools are executed on-demand with parameters

### 3. Stateless Operation

MCP servers are typically **stateless**:
- Each request is independent
- No session management required
- Servers can be restarted without losing state
- Clients handle connection management

## MCP Server Architecture

### Basic Server Structure

```python
from mcp.server import Server
import mcp.types as types

class MyMCPServer:
    def __init__(self):
        self.server = Server("my-server")
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.server.list_tools()
        async def handle_list_tools():
            # Return available tools
            return [
                types.Tool(
                    name="example_tool",
                    description="Example tool",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            # Execute the requested tool
            if name == "example_tool":
                return [types.TextContent(type="text", text="Hello!")]
```

### Required Protocol Handlers

Every MCP server must implement these handlers:

1. **`list_tools()`** - Tool Discovery
   - Returns list of available tools
   - Called when client wants to discover capabilities
   - Must return `List[types.Tool]`

2. **`call_tool(name, arguments)`** - Tool Execution
   - Executes a specific tool with given parameters
   - Called when client wants to use a tool
   - Must return `List[types.TextContent | types.ImageContent | types.EmbeddedResource]`

### Optional Protocol Handlers

Additional handlers for extended functionality:

1. **`list_prompts()`** - Prompt Discovery
   - Returns available prompt templates
   - For servers that provide reusable prompts

2. **`get_prompt(name, arguments)`** - Prompt Retrieval
   - Returns specific prompt content
   - For template-based interactions

## Client Architecture

### Client Responsibilities

MCP clients (like Claude Code) handle:
- **Discovery**: Finding and connecting to MCP servers
- **Tool Discovery**: Requesting available tools from servers
- **Tool Execution**: Calling tools with appropriate parameters
- **Error Handling**: Managing connection and execution errors

### Client-Server Interaction Flow

```
1. Client discovers server (configuration-based)
2. Client connects to server
3. Client requests tool list → Server returns tools
4. Client analyzes tools and their schemas
5. Client calls tool with parameters → Server executes and returns result
6. Client processes result and presents to user
```

## Practical Example: Simple MCP Server

Let's examine our simple MCP server architecture:

### File Structure
```
simple_mcp_server/
├── server.py        # Main server implementation
├── tools.py         # Tool definitions and schemas
├── handlers.py      # Tool execution logic
└── debug_utils.py   # Debugging and logging
```

### Key Architectural Decisions

1. **Separation of Concerns**:
   - `tools.py` defines WHAT tools are available
   - `handlers.py` defines HOW tools are executed
   - `server.py` handles protocol communication
   - `debug_utils.py` provides observability

2. **Comprehensive Logging**:
   - Every MCP message is logged
   - Request/response pairs are traced
   - Error conditions are captured
   - Performance metrics are recorded

3. **Error Handling**:
   - All tool handlers have try/catch blocks
   - Errors are formatted as proper MCP responses
   - Error details are logged for debugging

## Testing the Architecture

### Tool Discovery Test
```python
# Test that tools are discoverable
async def test_tool_discovery():
    tools = get_all_tools()
    assert len(tools) > 0
    assert all(hasattr(tool, 'name') for tool in tools)
    assert all(hasattr(tool, 'description') for tool in tools)
    assert all(hasattr(tool, 'inputSchema') for tool in tools)
```

### Tool Execution Test
```python
# Test that tools execute correctly
async def test_tool_execution():
    result = await handle_hello_world({"name": "World"})
    assert "Hello, World" in result
```

## Common Architectural Patterns

### 1. Tool Registration Pattern
```python
# Define tools in a central registry
TOOLS = {
    "hello_world": {
        "handler": handle_hello_world,
        "schema": {...}
    }
}

# Use registry in server
@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    if name in TOOLS:
        return await TOOLS[name]["handler"](arguments)
```

### 2. Middleware Pattern
```python
# Add middleware for common functionality
async def with_logging(handler):
    async def wrapper(arguments):
        logger.info(f"Calling {handler.__name__}")
        result = await handler(arguments)
        logger.info(f"Completed {handler.__name__}")
        return result
    return wrapper
```

### 3. Validation Pattern
```python
# Validate inputs before execution
def validate_arguments(schema, arguments):
    # Validate arguments against JSON schema
    # Raise ValueError if invalid
    pass

async def safe_handler(arguments):
    validate_arguments(tool_schema, arguments)
    return await actual_handler(arguments)
```

## Architecture Benefits

### For Development
- **Modularity**: Clean separation of concerns
- **Testability**: Each component can be tested independently
- **Maintainability**: Clear structure makes changes easier
- **Debuggability**: Comprehensive logging enables problem diagnosis

### For Integration
- **Standardization**: Protocol ensures compatibility
- **Flexibility**: Tools can be added/removed dynamically
- **Reliability**: Error handling prevents crashes
- **Observability**: Logging enables monitoring

## Next Steps

After understanding the architecture:
1. Learn about the **Protocol Flow** (Chapter 2)
2. Understand **Tool Registration** (Chapter 3)
3. Implement **Error Handling** (Chapter 4)
4. Set up **Debugging** (Chapter 5)

## Key Takeaways

- MCP is a client-server protocol based on JSON-RPC 2.0
- Everything revolves around tools and their execution
- Proper architecture separates concerns and enables debugging
- Comprehensive logging is essential for development and troubleshooting
- Error handling must be built into every layer

---

*This chapter provided the foundation for understanding MCP architecture. The next chapter will dive into the specific protocol flow and message patterns.*
