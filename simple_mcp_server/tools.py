"""
Tool definitions for the Simple MCP Server

This module defines all the tools that the MCP server exposes to clients.
Each tool has a name, description, and input schema that defines what
parameters it accepts.

Key Learning Points:
1. How to define MCP tools with proper schemas
2. Input validation and parameter handling
3. Tool discovery and registration
4. Schema-based documentation
"""

from typing import List
import mcp.types as types


def get_all_tools() -> List[types.Tool]:
    """
    Return all available MCP tools.
    
    This function is called by the server when a client requests
    the list of available tools via the list_tools RPC call.
    """
    
    return [
        # Basic greeting tool
        types.Tool(
            name="hello_world",
            description="A simple greeting tool that returns a hello message",
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
        
        # Echo tool for testing input/output
        types.Tool(
            name="echo",
            description="Echo back the input message with optional prefix",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message to echo back"
                    },
                    "prefix": {
                        "type": "string",
                        "description": "Optional prefix to add to the message",
                        "default": "Echo: "
                    }
                },
                "required": ["message"]
            }
        ),
        
        # Time tool for testing system interaction
        types.Tool(
            name="get_time",
            description="Get current time in various formats",
            inputSchema={
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Time format: 'iso', 'readable', or 'timestamp'",
                        "enum": ["iso", "readable", "timestamp"],
                        "default": "readable"
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'US/Eastern')",
                        "default": "local"
                    }
                },
                "required": []
            }
        ),
        
        # Math tool for testing parameter validation
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
        ),
        
        # Debug tool for server introspection
        types.Tool(
            name="debug_info",
            description="Get debug information about the MCP server",
            inputSchema={
                "type": "object",
                "properties": {
                    "include_tools": {
                        "type": "boolean",
                        "description": "Include tool information in response",
                        "default": True
                    },
                    "include_stats": {
                        "type": "boolean",
                        "description": "Include server statistics",
                        "default": True
                    }
                },
                "required": []
            }
        )
    ]


def get_tool_by_name(name: str) -> types.Tool:
    """
    Get a specific tool by name.
    
    This is a helper function for debugging and testing.
    """
    tools = get_all_tools()
    for tool in tools:
        if tool.name == name:
            return tool
    raise ValueError(f"Tool '{name}' not found")


def validate_tool_arguments(tool_name: str, arguments: dict) -> bool:
    """
    Validate arguments against a tool's schema.
    
    This is a helper function for debugging and testing.
    Returns True if arguments are valid, False otherwise.
    """
    try:
        tool = get_tool_by_name(tool_name)
        schema = tool.inputSchema
        
        # Basic validation - check required fields
        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in arguments:
                return False
        
        # Check field types (basic validation)
        properties = schema.get("properties", {})
        for field, value in arguments.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
        
        return True
        
    except Exception:
        return False
