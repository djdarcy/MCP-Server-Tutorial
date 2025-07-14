# Chapter 5: Debugging and Testing

## Overview

This chapter covers comprehensive debugging and testing strategies for MCP servers, including VS Code debugging setup, breakpoint strategies, test suite development, and protocol-level debugging.

## VS Code Debugging Setup

### 1. Launch Configuration

Our `.vscode/launch.json` configuration for debugging the MCP server:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug MCP Server",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/simple_mcp_server/server.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "MCP_DEBUG": "1"
            },
            "args": [],
            "stopOnEntry": false,
            "justMyCode": false,
            "subProcess": true
        },
        {
            "name": "Debug MCP Tests",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/tests/test_server.py",
            "console": "integratedTerminal",
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}",
                "MCP_DEBUG": "1"
            },
            "args": [],
            "stopOnEntry": false,
            "justMyCode": false
        }
    ]
}
```

### 2. Debug Environment Variables

```python
# debug_utils.py - Enhanced debugging support
import os
import logging

def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv("MCP_DEBUG", "0") == "1"

def setup_debug_logging():
    """Configure enhanced logging for debug mode."""
    if is_debug_mode():
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/debug.log'),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(level=logging.INFO)
```

## Breakpoint Strategies

### 1. Server Initialization Breakpoints

```python
# server.py - Key breakpoints for server initialization
class SimpleMCPServer:
    def __init__(self):
        """Initialize the MCP server."""
        self.server = Server("simple-mcp-server")
        
        # BREAKPOINT: Server creation
        # Inspect: self.server, configuration
        logger.info("MCP Server initialized")
        
        # Register handlers
        self.setup_handlers()
        
        # BREAKPOINT: After handler registration
        # Inspect: registered handlers, tool list
        logger.info("Handlers registered")
    
    def setup_handlers(self):
        """Set up MCP request handlers."""
        # BREAKPOINT: Before handler registration
        # Inspect: Available handlers, tool definitions
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """Handle list_tools request."""
            # BREAKPOINT: Tool list request
            # Inspect: Client request, available tools
            tools = get_all_tools()
            logger.info(f"Returning {len(tools)} tools")
            return tools
```

### 2. Request Processing Breakpoints

```python
# handlers.py - Request processing breakpoints
async def handle_tool_execution(name: str, arguments: Dict[str, Any]) -> types.CallToolResult:
    """Handle tool execution with debugging breakpoints."""
    
    # BREAKPOINT: Request received
    # Inspect: name, arguments, request context
    logger.debug(f"Tool execution request: {name} with args: {arguments}")
    
    try:
        # BREAKPOINT: Before parameter validation
        # Inspect: arguments, expected schema
        validate_parameters(name, arguments)
        
        # BREAKPOINT: After validation, before execution
        # Inspect: validated arguments, tool handler
        if name == "hello_world":
            result = await handle_hello_world(arguments)
        elif name == "echo":
            result = await handle_echo(arguments)
        # ... other tools
        
        # BREAKPOINT: After execution, before return
        # Inspect: result, execution time, success status
        logger.debug(f"Tool {name} executed successfully")
        return result
        
    except Exception as e:
        # BREAKPOINT: Error handling
        # Inspect: error type, error message, stack trace
        logger.error(f"Tool {name} execution error: {str(e)}")
        return create_error_result(str(e))
```

### 3. Protocol-Level Breakpoints

```python
# debug_utils.py - Protocol message inspection
def log_mcp_message(direction: str, message: Dict[str, Any]):
    """Log MCP protocol messages with debugging breakpoints."""
    
    # BREAKPOINT: Message logging
    # Inspect: message content, direction, timestamp
    timestamp = datetime.now().isoformat()
    logger.debug(f"MCP {direction}: {json.dumps(message, indent=2)}")
    
    # Enhanced inspection for different message types
    if "method" in message:
        method = message["method"]
        # BREAKPOINT: Method-specific inspection
        # Inspect: method name, parameters, request ID
        logger.debug(f"Method: {method}")
        
        if method == "tools/call":
            # BREAKPOINT: Tool call inspection
            # Inspect: tool name, arguments, call context
            params = message.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            logger.debug(f"Tool call: {tool_name} with {arguments}")
```

## Test Suite Development

### 1. Comprehensive Test Structure

```python
# tests/test_server.py - Complete test suite
import pytest
import asyncio
import json
from unittest.mock import Mock, patch

from simple_mcp_server.server import SimpleMCPServer
from simple_mcp_server.tools import get_all_tools
from simple_mcp_server.handlers import handle_tool_execution

class TestMCPServer:
    """Test suite for MCP server functionality."""
    
    @pytest.fixture
    def server(self):
        """Create server instance for testing."""
        return SimpleMCPServer()
    
    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server.server is not None
        assert server.server.name == "simple-mcp-server"
    
    def test_tool_registration(self, server):
        """Test that tools are properly registered."""
        tools = get_all_tools()
        assert len(tools) > 0
        
        # Check specific tools
        tool_names = [tool.name for tool in tools]
        assert "hello_world" in tool_names
        assert "echo" in tool_names
        assert "get_time" in tool_names
        assert "math_add" in tool_names
        assert "debug_info" in tool_names
    
    def test_tool_schemas(self, server):
        """Test that tool schemas are valid."""
        tools = get_all_tools()
        
        for tool in tools:
            # Check required fields
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            
            # Check schema structure
            schema = tool.inputSchema
            assert schema.get("type") == "object"
            assert "properties" in schema
```

### 2. Tool-Specific Tests

```python
class TestToolExecution:
    """Test individual tool execution."""
    
    @pytest.mark.asyncio
    async def test_hello_world(self):
        """Test hello_world tool execution."""
        # Test with default parameters
        result = await handle_tool_execution("hello_world", {})
        assert result.isError is False
        assert "Hello, World!" in result.content[0].text
        
        # Test with custom name
        result = await handle_tool_execution("hello_world", {"name": "Alice"})
        assert result.isError is False
        assert "Hello, Alice!" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_echo(self):
        """Test echo tool execution."""
        # Test basic echo
        result = await handle_tool_execution("echo", {"message": "test"})
        assert result.isError is False
        assert "Echo: test" in result.content[0].text
        
        # Test with custom prefix
        result = await handle_tool_execution("echo", {
            "message": "test", 
            "prefix": "Custom: "
        })
        assert result.isError is False
        assert "Custom: test" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_math_add(self):
        """Test math_add tool execution."""
        # Test integer addition
        result = await handle_tool_execution("math_add", {"a": 5, "b": 3})
        assert result.isError is False
        assert "8" in result.content[0].text
        
        # Test float addition
        result = await handle_tool_execution("math_add", {"a": 5.5, "b": 3.2})
        assert result.isError is False
        assert "8.7" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_get_time(self):
        """Test get_time tool execution."""
        # Test default format
        result = await handle_tool_execution("get_time", {})
        assert result.isError is False
        assert "Current time" in result.content[0].text
        
        # Test specific formats
        formats = ["iso", "readable", "timestamp"]
        for fmt in formats:
            result = await handle_tool_execution("get_time", {"format": fmt})
            assert result.isError is False
            assert len(result.content[0].text) > 0
```

### 3. Error Handling Tests

```python
class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_missing_required_parameter(self):
        """Test handling of missing required parameters."""
        result = await handle_tool_execution("math_add", {"a": 5})
        assert result.isError is True
        assert "required" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_invalid_parameter_type(self):
        """Test handling of invalid parameter types."""
        result = await handle_tool_execution("math_add", {"a": "string", "b": 10})
        assert result.isError is True
        assert "number" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_tool_not_found(self):
        """Test handling of non-existent tools."""
        result = await handle_tool_execution("nonexistent_tool", {})
        assert result.isError is True
        assert "unknown" in result.content[0].text.lower()
    
    @pytest.mark.asyncio
    async def test_empty_arguments(self):
        """Test handling of empty arguments."""
        # Should work for optional parameters
        result = await handle_tool_execution("hello_world", {})
        assert result.isError is False
        
        # Should fail for required parameters
        result = await handle_tool_execution("echo", {})
        assert result.isError is True
```

## Protocol-Level Debugging

### 1. Message Tracing

```python
# debug_utils.py - Protocol message tracing
class MCPMessageTracer:
    """Trace MCP protocol messages for debugging."""
    
    def __init__(self):
        self.messages = []
        self.enabled = is_debug_mode()
    
    def trace_message(self, direction: str, message: Dict[str, Any]):
        """Trace a protocol message."""
        if not self.enabled:
            return
        
        message_trace = {
            "timestamp": datetime.now().isoformat(),
            "direction": direction,
            "message": message
        }
        
        self.messages.append(message_trace)
        
        # Log to file for analysis
        with open("logs/protocol_trace.json", "a") as f:
            f.write(json.dumps(message_trace) + "\n")
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """Get complete message history."""
        return self.messages
    
    def analyze_message_flow(self) -> Dict[str, Any]:
        """Analyze message flow patterns."""
        analysis = {
            "total_messages": len(self.messages),
            "by_direction": {},
            "by_method": {},
            "errors": []
        }
        
        for msg in self.messages:
            direction = msg["direction"]
            analysis["by_direction"][direction] = analysis["by_direction"].get(direction, 0) + 1
            
            if "method" in msg["message"]:
                method = msg["message"]["method"]
                analysis["by_method"][method] = analysis["by_method"].get(method, 0) + 1
            
            if "error" in msg["message"]:
                analysis["errors"].append(msg)
        
        return analysis
```

### 2. Request/Response Correlation

```python
# debug_utils.py - Request/response correlation
class RequestCorrelator:
    """Correlate requests with responses for debugging."""
    
    def __init__(self):
        self.pending_requests = {}
        self.completed_requests = {}
    
    def track_request(self, request_id: str, request: Dict[str, Any]):
        """Track an outgoing request."""
        self.pending_requests[request_id] = {
            "request": request,
            "timestamp": datetime.now(),
            "response": None
        }
    
    def track_response(self, request_id: str, response: Dict[str, Any]):
        """Track a response to a request."""
        if request_id in self.pending_requests:
            request_data = self.pending_requests.pop(request_id)
            request_data["response"] = response
            request_data["duration"] = (datetime.now() - request_data["timestamp"]).total_seconds()
            
            self.completed_requests[request_id] = request_data
    
    def get_pending_requests(self) -> Dict[str, Any]:
        """Get requests waiting for responses."""
        return self.pending_requests
    
    def get_request_metrics(self) -> Dict[str, Any]:
        """Get request performance metrics."""
        if not self.completed_requests:
            return {}
        
        durations = [req["duration"] for req in self.completed_requests.values()]
        
        return {
            "total_requests": len(self.completed_requests),
            "average_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "pending_requests": len(self.pending_requests)
        }
```

## Advanced Debugging Techniques

### 1. Memory and Performance Debugging

```python
# debug_utils.py - Performance monitoring
import psutil
import time
from functools import wraps

def profile_function(func):
    """Decorator to profile function execution."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = await func(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_diff = end_memory - start_memory
            
            logger.debug(f"Function {func.__name__} - Duration: {duration:.3f}s, Memory: {memory_diff} bytes")
            
            return result
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.error(f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}")
            raise
    
    return wrapper

# Usage
@profile_function
async def handle_math_add(arguments: Dict[str, Any]) -> types.CallToolResult:
    """Handle math addition with profiling."""
    # ... implementation
```

### 2. State Inspection

```python
# debug_utils.py - Server state inspection
class ServerStateInspector:
    """Inspect server state for debugging."""
    
    def __init__(self, server):
        self.server = server
    
    def get_server_state(self) -> Dict[str, Any]:
        """Get current server state."""
        return {
            "server_name": self.server.server.name,
            "tools_count": len(get_all_tools()),
            "memory_usage": psutil.Process().memory_info().rss,
            "cpu_percent": psutil.Process().cpu_percent(),
            "uptime": time.time() - self.server.start_time
        }
    
    def get_tool_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        # This would track tool call counts, errors, etc.
        return {
            "tool_calls": getattr(self.server, 'tool_calls', {}),
            "tool_errors": getattr(self.server, 'tool_errors', {}),
            "most_used_tool": self._get_most_used_tool()
        }
    
    def _get_most_used_tool(self) -> str:
        """Get the most frequently used tool."""
        tool_calls = getattr(self.server, 'tool_calls', {})
        if not tool_calls:
            return "None"
        
        return max(tool_calls, key=tool_calls.get)
```

## Testing with Real Claude Integration

### 1. Integration Test Setup

```python
# tests/test_integration.py - Integration testing
import subprocess
import time
import json
from pathlib import Path

class TestClaudeIntegration:
    """Test integration with Claude Desktop."""
    
    def setup_claude_config(self):
        """Set up Claude Desktop configuration for testing."""
        config = {
            "mcpServers": {
                "simple-mcp-server": {
                    "command": "python",
                    "args": [str(Path(__file__).parent.parent / "simple_mcp_server" / "server.py")],
                    "env": {
                        "MCP_DEBUG": "1"
                    }
                }
            }
        }
        
        # Write to Claude config location (platform-specific)
        config_path = self.get_claude_config_path()
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)
    
    def get_claude_config_path(self) -> Path:
        """Get Claude Desktop configuration path."""
        import platform
        
        if platform.system() == "Windows":
            return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif platform.system() == "Darwin":
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:
            return Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    
    def test_server_startup(self):
        """Test that server starts correctly."""
        process = subprocess.Popen([
            "python", "simple_mcp_server/server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give server time to start
        time.sleep(2)
        
        # Check if process is running
        assert process.poll() is None, "Server process should be running"
        
        # Clean up
        process.terminate()
        process.wait()
```

## Debugging Best Practices

### 1. Structured Debugging Approach

```python
# Debugging checklist for MCP servers
def debug_mcp_server():
    """
    Structured debugging approach for MCP servers.
    
    1. Server Initialization
       - Check server starts without errors
       - Verify tool registration
       - Confirm handler setup
    
    2. Tool Discovery
       - Verify list_tools returns expected tools
       - Check tool schemas are valid
       - Confirm tool descriptions are clear
    
    3. Tool Execution
       - Test each tool with valid parameters
       - Test error scenarios
       - Verify response format
    
    4. Protocol Communication
       - Trace message flow
       - Check request/response correlation
       - Monitor for message errors
    
    5. Error Handling
       - Test all error paths
       - Verify error messages are helpful
       - Check logging captures errors
    """
    pass
```

### 2. Common Debugging Scenarios

```python
# Common debugging scenarios and solutions
DEBUGGING_SCENARIOS = {
    "server_not_recognized": {
        "symptoms": ["Claude doesn't show server", "No tools available"],
        "checks": [
            "Verify claude_desktop_config.json is correct",
            "Check server starts without errors",
            "Confirm server outputs to stdio",
            "Verify MCP protocol compliance"
        ]
    },
    
    "tools_not_appearing": {
        "symptoms": ["Server recognized but no tools", "Empty tool list"],
        "checks": [
            "Check list_tools handler registration",
            "Verify get_all_tools() returns tools",
            "Check tool schema validation",
            "Confirm tools are properly formatted"
        ]
    },
    
    "tool_execution_fails": {
        "symptoms": ["Tool calls return errors", "Unexpected responses"],
        "checks": [
            "Verify parameter validation",
            "Check tool handler implementation",
            "Test error handling paths",
            "Confirm response format"
        ]
    }
}
```

## Summary

This chapter covered:

1. **VS Code Setup**: Complete debugging configuration and environment setup
2. **Breakpoint Strategies**: Strategic placement of breakpoints for effective debugging
3. **Test Suite Development**: Comprehensive testing approach for MCP servers
4. **Protocol Debugging**: Advanced techniques for tracing MCP communication
5. **Performance Monitoring**: Tools for monitoring server performance and resource usage
6. **Integration Testing**: Testing with real Claude Desktop integration
7. **Best Practices**: Structured debugging approach and common scenario solutions

The debugging and testing infrastructure provides a solid foundation for developing, testing, and maintaining robust MCP servers.

## Next Steps

- **Chapter 6**: Authentication and Security - Implement secure MCP servers
- **Chapter 7**: State Management - Handle server state and resources
- **Chapter 8**: Claude Integration - Deep dive into Claude Desktop integration
