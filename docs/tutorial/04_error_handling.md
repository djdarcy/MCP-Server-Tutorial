# Chapter 4: Error Handling

## Overview

Error handling is crucial for robust MCP servers. This chapter covers how to implement proper error handling patterns, graceful error responses, and comprehensive error logging for debugging.

## MCP Error Handling Patterns

### 1. Protocol-Level Errors

MCP uses JSON-RPC 2.0 error responses with specific error codes:

```python
# Example error response structure
{
    "jsonrpc": "2.0",
    "id": "request_id",
    "error": {
        "code": -32602,  # Invalid params
        "message": "Invalid parameters",
        "data": {
            "details": "Parameter 'name' is required"
        }
    }
}
```

### 2. Common Error Codes

```python
# Standard JSON-RPC error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# MCP-specific error codes (custom range)
TOOL_NOT_FOUND = -32001
TOOL_EXECUTION_ERROR = -32002
AUTHENTICATION_ERROR = -32003
RATE_LIMIT_ERROR = -32004
```

## Implementation Examples

### 1. Parameter Validation Errors

```python
def validate_parameters(tool_name: str, arguments: Dict[str, Any]) -> None:
    """
    Validate tool parameters against schema.
    
    Raises:
        ValueError: If parameters don't match schema
    """
    if tool_name == "math_add":
        if "a" not in arguments or "b" not in arguments:
            raise ValueError("Parameters 'a' and 'b' are required")
        
        if not isinstance(arguments["a"], (int, float)):
            raise ValueError("Parameter 'a' must be a number")
        
        if not isinstance(arguments["b"], (int, float)):
            raise ValueError("Parameter 'b' must be a number")
    
    elif tool_name == "echo":
        if "message" not in arguments:
            raise ValueError("Parameter 'message' is required")
        
        if not isinstance(arguments["message"], str):
            raise ValueError("Parameter 'message' must be a string")
```

### 2. Tool Execution Error Handling

```python
async def handle_tool_execution(name: str, arguments: Dict[str, Any]) -> types.CallToolResult:
    """
    Handle tool execution with comprehensive error handling.
    """
    try:
        # Validate parameters first
        validate_parameters(name, arguments)
        
        # Log the execution attempt
        logger.info(f"Executing tool: {name} with arguments: {arguments}")
        
        # Execute the tool
        if name == "hello_world":
            result = await handle_hello_world(arguments)
        elif name == "echo":
            result = await handle_echo(arguments)
        elif name == "get_time":
            result = await handle_get_time(arguments)
        elif name == "math_add":
            result = await handle_math_add(arguments)
        elif name == "debug_info":
            result = await handle_debug_info(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Log successful execution
        logger.info(f"Tool {name} executed successfully")
        return result
        
    except ValueError as e:
        # Parameter validation or tool not found errors
        logger.error(f"Tool {name} validation error: {str(e)}")
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )],
            isError=True
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Tool {name} execution error: {str(e)}", exc_info=True)
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Internal error executing tool {name}: {str(e)}"
            )],
            isError=True
        )
```

### 3. Graceful Error Responses

```python
def create_error_response(error_code: int, message: str, details: Any = None) -> Dict[str, Any]:
    """
    Create a standardized error response.
    """
    error_response = {
        "code": error_code,
        "message": message
    }
    
    if details:
        error_response["data"] = {"details": details}
    
    return error_response

# Usage examples
def handle_invalid_parameters(tool_name: str, error_details: str):
    return create_error_response(
        error_code=INVALID_PARAMS,
        message=f"Invalid parameters for tool {tool_name}",
        details=error_details
    )

def handle_tool_not_found(tool_name: str):
    return create_error_response(
        error_code=TOOL_NOT_FOUND,
        message=f"Tool '{tool_name}' not found",
        details=f"Available tools: {', '.join(get_tool_names())}"
    )
```

## Error Logging and Debugging

### 1. Comprehensive Error Logging

```python
import logging
import traceback
from datetime import datetime

def setup_error_logging():
    """
    Configure logging for error tracking.
    """
    # Create error-specific logger
    error_logger = logging.getLogger('mcp_errors')
    error_logger.setLevel(logging.ERROR)
    
    # Create error log file handler
    error_handler = logging.FileHandler('logs/mcp_errors.log')
    error_handler.setLevel(logging.ERROR)
    
    # Create detailed formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    error_handler.setFormatter(formatter)
    
    error_logger.addHandler(error_handler)
    return error_logger

def log_error_with_context(logger, error: Exception, context: Dict[str, Any]):
    """
    Log error with full context information.
    """
    error_info = {
        "timestamp": datetime.now().isoformat(),
        "error_type": type(error).__name__,
        "error_message": str(error),
        "traceback": traceback.format_exc(),
        "context": context
    }
    
    logger.error(f"MCP Error: {json.dumps(error_info, indent=2)}")
```

### 2. Error Recovery Strategies

```python
async def execute_with_retry(
    func, 
    max_retries: int = 3, 
    delay: float = 1.0
) -> Any:
    """
    Execute function with retry logic for transient errors.
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed, re-raise
                raise
            
            # Log retry attempt
            logger.warning(f"Attempt {attempt + 1} failed: {str(e)}, retrying...")
            await asyncio.sleep(delay)
    
    # Should never reach here
    raise RuntimeError("Maximum retries exceeded")

# Usage example
async def handle_get_time_with_retry(arguments: Dict[str, Any]) -> types.CallToolResult:
    """
    Handle time requests with retry logic.
    """
    async def get_time_operation():
        return await handle_get_time(arguments)
    
    try:
        return await execute_with_retry(get_time_operation)
    except Exception as e:
        logger.error(f"Failed to get time after retries: {str(e)}")
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Error: Unable to get time - {str(e)}"
            )],
            isError=True
        )
```

## Common Error Scenarios

### 1. Missing Required Parameters

```python
# Test case: Missing required parameter
{
    "tool": "math_add",
    "arguments": {
        "a": 5
        # Missing "b" parameter
    }
}

# Expected error response
{
    "isError": true,
    "content": [{
        "type": "text",
        "text": "Error: Parameter 'b' is required"
    }]
}
```

### 2. Invalid Parameter Types

```python
# Test case: Invalid parameter type
{
    "tool": "math_add",
    "arguments": {
        "a": "not_a_number",
        "b": 10
    }
}

# Expected error response
{
    "isError": true,
    "content": [{
        "type": "text",
        "text": "Error: Parameter 'a' must be a number"
    }]
}
```

### 3. Tool Not Found

```python
# Test case: Non-existent tool
{
    "tool": "nonexistent_tool",
    "arguments": {}
}

# Expected error response
{
    "isError": true,
    "content": [{
        "type": "text",
        "text": "Error: Unknown tool: nonexistent_tool"
    }]
}
```

## Testing Error Handling

### 1. Error Handling Test Suite

```python
import pytest
from simple_mcp_server.handlers import handle_tool_execution

@pytest.mark.asyncio
async def test_missing_required_parameter():
    """Test handling of missing required parameters."""
    result = await handle_tool_execution("math_add", {"a": 5})
    
    assert result.isError is True
    assert "Parameter 'b' is required" in result.content[0].text

@pytest.mark.asyncio
async def test_invalid_parameter_type():
    """Test handling of invalid parameter types."""
    result = await handle_tool_execution("math_add", {"a": "string", "b": 10})
    
    assert result.isError is True
    assert "must be a number" in result.content[0].text

@pytest.mark.asyncio
async def test_tool_not_found():
    """Test handling of non-existent tools."""
    result = await handle_tool_execution("nonexistent_tool", {})
    
    assert result.isError is True
    assert "Unknown tool" in result.content[0].text
```

### 2. Error Logging Verification

```python
def test_error_logging(caplog):
    """Test that errors are properly logged."""
    with caplog.at_level(logging.ERROR):
        # Trigger an error
        try:
            validate_parameters("math_add", {"a": "string"})
        except ValueError:
            pass
    
    # Verify error was logged
    assert "Parameter 'a' must be a number" in caplog.text
```

## Best Practices

### 1. Error Response Guidelines

- **Always include context**: Help users understand what went wrong
- **Be specific**: Provide actionable error messages
- **Use consistent format**: Maintain the same error structure across tools
- **Log everything**: Capture errors for debugging and monitoring

### 2. Error Recovery Patterns

- **Graceful degradation**: Continue operation when possible
- **Retry transient errors**: Implement exponential backoff for network issues
- **User-friendly messages**: Translate technical errors to user-friendly language
- **Fallback mechanisms**: Provide alternative approaches when primary method fails

### 3. Debugging Error Handling

```python
# Enable detailed error logging
logging.basicConfig(level=logging.DEBUG)

# Test error scenarios manually
async def test_error_scenarios():
    """Manual test for error scenarios."""
    test_cases = [
        {"tool": "math_add", "args": {"a": 5}},  # Missing parameter
        {"tool": "math_add", "args": {"a": "str", "b": 10}},  # Invalid type
        {"tool": "unknown", "args": {}},  # Tool not found
    ]
    
    for test_case in test_cases:
        result = await handle_tool_execution(test_case["tool"], test_case["args"])
        print(f"Test: {test_case}")
        print(f"Result: {result}")
        print("---")
```

## Integration with VS Code Debugging

### 1. Error Breakpoints

Set breakpoints in error handling code:

```python
# Set breakpoint here to catch parameter validation errors
try:
    validate_parameters(name, arguments)
except ValueError as e:
    # Breakpoint: Inspect error and arguments
    logger.error(f"Validation error: {str(e)}")
    return create_error_response(...)
```

### 2. Error Inspection

Use VS Code's debug console to inspect error objects:

```python
# In debug console
>>> error
ValueError('Parameter 'a' must be a number')
>>> arguments
{'a': 'string', 'b': 10}
>>> type(arguments['a'])
<class 'str'>
```

## Summary

This chapter covered:

1. **MCP Error Patterns**: Understanding JSON-RPC error format and MCP-specific codes
2. **Error Implementation**: Practical examples of parameter validation and tool execution errors
3. **Error Logging**: Comprehensive logging strategies for debugging
4. **Error Recovery**: Retry mechanisms and graceful degradation
5. **Testing**: Comprehensive error handling test suite
6. **Best Practices**: Guidelines for user-friendly error handling

The error handling system is essential for creating robust MCP servers that can gracefully handle various failure scenarios while providing useful feedback for debugging and user experience.

## Next Steps

- **Chapter 5**: Debugging and Testing - Learn advanced debugging techniques
- **Chapter 6**: Authentication and Security - Implement secure MCP servers
- **Chapter 7**: State Management - Handle server state and resources
