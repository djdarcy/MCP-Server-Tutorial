# Chapter 3: Tool Registration - How Tools Are Defined and Discovered

## Overview

Tool registration is the foundation of MCP functionality. This chapter explains how tools are defined, registered with the server, and discovered by clients. Understanding this process is crucial for building effective MCP servers.

## What is Tool Registration?

Tool registration is the process of:
1. **Defining** what tools your server provides
2. **Registering** those tools with the MCP server
3. **Exposing** tool schemas to clients for discovery
4. **Routing** tool execution requests to appropriate handlers

## Tool Definition Structure

### MCP Tool Components

Every MCP tool must have these components:

```python
types.Tool(
    name="tool_name",              # Unique identifier
    description="Tool description", # Human-readable description
    inputSchema={                  # JSON Schema for parameters
        "type": "object",
        "properties": {
            "param1": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param1"]
    }
)
```

### JSON Schema for Parameters

The `inputSchema` uses JSON Schema format to define:
- **Parameter types** (string, number, boolean, object, array)
- **Required parameters** vs optional parameters
- **Parameter descriptions** for user guidance
- **Validation rules** (min/max values, patterns, etc.)

## Tool Registration in Practice

### Step 1: Define Tool Schemas

In our `tools.py` file, we define tools centrally:

```python
def get_all_tools() -> List[types.Tool]:
    """Return all available MCP tools"""
    
    return [
        # Simple tool with no parameters
        types.Tool(
            name="hello_world",
            description="A simple greeting tool",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Name to greet (optional)",
                        "default": "World"
                    }
                },
                "required": []
            }
        ),
        
        # Tool with required parameters
        types.Tool(
            name="math_add",
            description="Add two numbers together",
            inputSchema={
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number"
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number"
                    }
                },
                "required": ["a", "b"]
            }
        )
    ]
```

### Step 2: Register Tools with Server

In our `server.py` file, we register the tool discovery handler:

```python
@self.server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """Return list of available tools"""
    logger.info("📋 Client requesting tool list")
    
    tools = get_all_tools()
    logger.info(f"📋 Returning {len(tools)} tools:")
    
    for tool in tools:
        logger.info(f"   - {tool.name}: {tool.description}")
    
    return tools
```

### Step 3: Register Tool Execution Handler

Also in `server.py`, we register the tool execution handler:

```python
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool execution"""
    logger.info(f"🔧 Tool execution request: {name}")
    logger.info(f"🔧 Arguments: {arguments}")
    
    # Route to appropriate handler
    if name == "hello_world":
        result = await handle_hello_world(arguments)
    elif name == "math_add":
        result = await handle_math_add(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")
    
    return [types.TextContent(type="text", text=result)]
```

## Tool Discovery Process

### Client-Side Discovery

When a client connects to your server:

1. **Client sends `list_tools()` request**
2. **Server responds with tool definitions**
3. **Client analyzes tool schemas**
4. **Client enables tools for user interaction**

### Server-Side Discovery Response

Our server logs show the discovery process:

```
[10:30:00] 📋 Client requesting tool list
[10:30:00] 📋 Returning 5 tools:
[10:30:00]    - hello_world: A simple greeting tool
[10:30:00]    - echo: Echo back the input message
[10:30:00]    - get_time: Get current time in various formats
[10:30:00]    - math_add: Add two numbers together
[10:30:00]    - debug_info: Get debug information about the server
```

## Advanced Tool Registration Patterns

### 1. Dynamic Tool Registration

Tools can be registered dynamically based on configuration:

```python
def get_all_tools() -> List[types.Tool]:
    """Return tools based on configuration"""
    tools = []
    
    # Always include basic tools
    tools.extend(get_basic_tools())
    
    # Add optional tools based on configuration
    if config.get("enable_math_tools"):
        tools.extend(get_math_tools())
    
    if config.get("enable_file_tools"):
        tools.extend(get_file_tools())
    
    return tools
```

### 2. Tool Registration with Metadata

Add metadata to tools for better organization:

```python
def get_all_tools() -> List[types.Tool]:
    """Return tools with metadata"""
    tools = []
    
    for tool_config in TOOL_CONFIGS:
        tool = types.Tool(
            name=tool_config["name"],
            description=tool_config["description"],
            inputSchema=tool_config["schema"]
        )
        
        # Add metadata (not part of MCP spec, but useful internally)
        tool._metadata = {
            "category": tool_config["category"],
            "version": tool_config["version"],
            "author": tool_config["author"]
        }
        
        tools.append(tool)
    
    return tools
```

### 3. Tool Registration with Validation

Validate tool definitions during registration:

```python
def validate_tool_definition(tool: types.Tool) -> None:
    """Validate a tool definition"""
    
    # Check required fields
    if not tool.name:
        raise ValueError("Tool name is required")
    
    if not tool.description:
        raise ValueError("Tool description is required")
    
    # Validate schema
    try:
        jsonschema.validate({}, tool.inputSchema)
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid schema: {e}")
    
    # Check name format
    if not re.match(r'^[a-zA-Z0-9_]+$', tool.name):
        raise ValueError("Tool name must contain only letters, numbers, and underscores")

def get_all_tools() -> List[types.Tool]:
    """Return validated tools"""
    tools = []
    
    for tool_config in TOOL_CONFIGS:
        tool = create_tool_from_config(tool_config)
        validate_tool_definition(tool)
        tools.append(tool)
    
    return tools
```

## Tool Execution Registration

### Handler Registration Pattern

We use a clean pattern to register tool handlers:

```python
# In handlers.py
TOOL_HANDLERS = {
    "hello_world": handle_hello_world,
    "echo": handle_echo,
    "get_time": handle_get_time,
    "math_add": handle_math_add,
    "debug_info": handle_debug_info,
}

# In server.py
@self.server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Route tool execution to appropriate handler"""
    
    if name not in TOOL_HANDLERS:
        raise ValueError(f"Unknown tool: {name}")
    
    handler = TOOL_HANDLERS[name]
    
    # Handle special cases (like debug_info needing server reference)
    if name == "debug_info":
        return await handler(arguments, self)
    else:
        return await handler(arguments)
```

### Decorator Pattern for Registration

Alternative registration using decorators:

```python
# Tool registry
_tool_registry = {}

def tool(name: str, description: str, schema: dict):
    """Decorator for registering tools"""
    def decorator(handler_func):
        _tool_registry[name] = {
            "handler": handler_func,
            "description": description,
            "schema": schema
        }
        return handler_func
    return decorator

# Usage
@tool("hello_world", "A simple greeting tool", {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "Name to greet"}
    }
})
async def handle_hello_world(arguments: dict) -> str:
    name = arguments.get("name", "World")
    return f"Hello, {name}!"

# Generate tools from registry
def get_all_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=name,
            description=config["description"],
            inputSchema=config["schema"]
        )
        for name, config in _tool_registry.items()
    ]
```

## Testing Tool Registration

### Unit Tests for Tool Definition

```python
def test_tool_definitions():
    """Test that all tools are properly defined"""
    tools = get_all_tools()
    
    # Check basic structure
    assert len(tools) > 0
    
    for tool in tools:
        # Check required fields
        assert hasattr(tool, 'name')
        assert hasattr(tool, 'description')
        assert hasattr(tool, 'inputSchema')
        
        # Check field types
        assert isinstance(tool.name, str)
        assert isinstance(tool.description, str)
        assert isinstance(tool.inputSchema, dict)
        
        # Check schema structure
        assert tool.inputSchema.get("type") == "object"
        assert "properties" in tool.inputSchema
```

### Integration Tests for Tool Discovery

```python
async def test_tool_discovery():
    """Test tool discovery process"""
    # Simulate client request
    server = SimpleMCPServer()
    tools = await server.handle_list_tools()
    
    # Verify response
    assert isinstance(tools, list)
    assert len(tools) > 0
    
    # Check tool names are unique
    tool_names = [tool.name for tool in tools]
    assert len(tool_names) == len(set(tool_names))
```

### Tests for Tool Execution Registration

```python
async def test_tool_execution_registration():
    """Test that all registered tools can be executed"""
    server = SimpleMCPServer()
    tools = await server.handle_list_tools()
    
    for tool in tools:
        # Test with minimal valid arguments
        try:
            result = await server.handle_call_tool(tool.name, {})
            assert result is not None
        except Exception as e:
            # Should fail gracefully with clear error message
            assert "required" in str(e).lower() or "missing" in str(e).lower()
```

## Common Registration Issues and Solutions

### Issue 1: Tool Not Appearing in Discovery

**Symptoms**:
- Tool defined but not returned by `list_tools()`
- Client doesn't see the tool

**Common Causes**:
- Tool not added to `get_all_tools()` return list
- Exception during tool creation
- Invalid tool schema

**Solution**:
```python
def get_all_tools() -> List[types.Tool]:
    tools = []
    
    try:
        # Add each tool with error handling
        tools.append(create_hello_world_tool())
        tools.append(create_math_add_tool())
        # ... other tools
        
        logger.info(f"Successfully registered {len(tools)} tools")
        return tools
        
    except Exception as e:
        logger.error(f"Error during tool registration: {e}")
        # Return partial list or empty list
        return tools
```

### Issue 2: Tool Execution Not Working

**Symptoms**:
- Tool appears in discovery but fails when called
- "Unknown tool" errors during execution

**Common Causes**:
- Tool name mismatch between definition and handler
- Handler not registered in routing logic
- Exception in handler code

**Solution**:
```python
# Ensure consistent naming
TOOL_DEFINITIONS = {
    "hello_world": {
        "description": "A simple greeting tool",
        "schema": {...},
        "handler": handle_hello_world
    }
}

def get_all_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=name,
            description=config["description"],
            inputSchema=config["schema"]
        )
        for name, config in TOOL_DEFINITIONS.items()
    ]

async def handle_call_tool(name: str, arguments: dict):
    if name not in TOOL_DEFINITIONS:
        raise ValueError(f"Unknown tool: {name}")
    
    handler = TOOL_DEFINITIONS[name]["handler"]
    return await handler(arguments)
```

### Issue 3: Invalid Tool Schema

**Symptoms**:
- Tools discovered but client shows schema errors
- Parameters not working correctly

**Common Causes**:
- Invalid JSON Schema format
- Missing required schema fields
- Type mismatches

**Solution**:
```python
import jsonschema

def validate_tool_schema(schema: dict) -> None:
    """Validate tool schema"""
    try:
        # Validate against JSON Schema meta-schema
        jsonschema.Draft7Validator.check_schema(schema)
        
        # Check required fields
        if schema.get("type") != "object":
            raise ValueError("Tool schema must be of type 'object'")
        
        if "properties" not in schema:
            raise ValueError("Tool schema must have 'properties' field")
            
    except jsonschema.SchemaError as e:
        raise ValueError(f"Invalid schema: {e}")
```

## Best Practices for Tool Registration

### 1. Consistent Naming

- Use consistent naming conventions (snake_case recommended)
- Make names descriptive but concise
- Avoid special characters except underscores

### 2. Clear Descriptions

- Write clear, concise tool descriptions
- Explain what the tool does and when to use it
- Include example use cases if helpful

### 3. Proper Schema Design

- Use appropriate JSON Schema types
- Provide clear parameter descriptions
- Set reasonable defaults for optional parameters
- Use validation rules (min/max, patterns) where appropriate

### 4. Error Handling

- Validate tool definitions during registration
- Handle registration errors gracefully
- Provide clear error messages for debugging

### 5. Testing

- Test tool discovery process
- Test tool execution for all registered tools
- Test error conditions and edge cases

## Next Steps

After understanding tool registration:
1. Learn about **Authentication** (Chapter 4)
2. Understand **Error Handling** (Chapter 5)
3. Set up **Debugging** (Chapter 6)
4. Implement **State Management** (Chapter 7)

## Key Takeaways

- Tool registration involves defining, registering, and exposing tools
- Tools are discovered through the `list_tools()` protocol method
- Tool execution is routed through the `call_tool()` protocol method
- Proper schema design is crucial for tool usability
- Testing registration and execution is essential for reliability
- Consistent patterns make maintenance easier

---

*This chapter covered tool registration in detail. The next chapter will focus on authentication and security considerations for MCP servers.*
