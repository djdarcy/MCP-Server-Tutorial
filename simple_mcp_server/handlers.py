"""
Request handlers for the Simple MCP Server

This module contains the actual implementation of each tool.
Each handler receives arguments and returns a response.

Key Learning Points:
1. How to implement MCP tool handlers
2. Input validation and error handling
3. Response formatting for MCP protocol
4. Debugging and logging within handlers
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict, List
import mcp.types as types
from debug_utils import get_logger

logger = get_logger(__name__)


async def handle_hello_world(arguments: Dict[str, Any]) -> str:
    """
    Handle hello_world tool request.
    
    This is the simplest possible tool handler that demonstrates
    basic input processing and response formatting.
    """
    logger.info("🌍 Handling hello_world request")
    logger.debug(f"Arguments: {arguments}")
    
    # Get the name parameter, default to "World"
    name = arguments.get("name", "World")
    
    # Create greeting message
    greeting = f"Hello, {name}! 👋"
    
    # Add some debug info
    timestamp = datetime.now().isoformat()
    response = f"{greeting}\n\nGenerated at: {timestamp}"
    
    logger.info(f"✅ hello_world completed: greeting for '{name}'")
    return response


async def handle_echo(arguments: Dict[str, Any]) -> str:
    """
    Handle echo tool request.
    
    This demonstrates input validation and parameter handling.
    """
    logger.info("🔄 Handling echo request")
    logger.debug(f"Arguments: {arguments}")
    
    # Validate required parameters
    if "message" not in arguments:
        error_msg = "Missing required parameter: message"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    message = arguments["message"]
    prefix = arguments.get("prefix", "Echo: ")
    
    # Create echo response
    response = f"{prefix}{message}"
    
    logger.info(f"✅ echo completed: '{message}'")
    return response


async def handle_get_time(arguments: Dict[str, Any]) -> str:
    """
    Handle get_time tool request.
    
    This demonstrates system interaction and format handling.
    """
    logger.info("🕐 Handling get_time request")
    logger.debug(f"Arguments: {arguments}")
    
    time_format = arguments.get("format", "readable")
    timezone = arguments.get("timezone", "local")
    
    # Get current time
    now = datetime.now()
    
    # Format based on requested format
    if time_format == "iso":
        time_str = now.isoformat()
    elif time_format == "timestamp":
        time_str = str(now.timestamp())
    elif time_format == "readable":
        time_str = now.strftime("%Y-%m-%d %H:%M:%S")
    else:
        error_msg = f"Unknown time format: {time_format}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Build response
    response = f"Current time: {time_str}"
    if timezone != "local":
        response += f" (requested timezone: {timezone})"
    
    logger.info(f"✅ get_time completed: format={time_format}")
    return response


async def handle_math_add(arguments: Dict[str, Any]) -> str:
    """
    Handle math_add tool request.
    
    This demonstrates parameter validation and type checking.
    """
    logger.info("🔢 Handling math_add request")
    logger.debug(f"Arguments: {arguments}")
    
    # Validate required parameters
    if "a" not in arguments or "b" not in arguments:
        error_msg = "Missing required parameters: a and b"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    try:
        a = float(arguments["a"])
        b = float(arguments["b"])
    except (ValueError, TypeError) as e:
        error_msg = f"Invalid number format: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Perform calculation
    result = a + b
    
    # Format response
    response = f"{a} + {b} = {result}"
    
    logger.info(f"✅ math_add completed: {a} + {b} = {result}")
    return response


async def handle_debug_info(arguments: Dict[str, Any], server) -> str:
    """
    Handle debug_info tool request.
    
    This demonstrates server introspection and debugging capabilities.
    """
    logger.info("🔍 Handling debug_info request")
    logger.debug(f"Arguments: {arguments}")
    
    include_tools = arguments.get("include_tools", True)
    include_stats = arguments.get("include_stats", True)
    
    # Build debug information
    debug_info = {
        "server_name": server.server_name,
        "start_time": server.start_time.isoformat(),
        "uptime_seconds": (datetime.now() - server.start_time).total_seconds(),
        "request_count": server.request_count,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "timestamp": datetime.now().isoformat()
    }
    
    # Add tool information if requested
    if include_tools:
        from tools import get_all_tools
        tools = get_all_tools()
        debug_info["tools"] = [
            {
                "name": tool.name,
                "description": tool.description,
                "required_params": tool.inputSchema.get("required", [])
            }
            for tool in tools
        ]
    
    # Add server statistics if requested
    if include_stats:
        debug_info["statistics"] = {
            "tools_available": len(debug_info.get("tools", [])),
            "avg_requests_per_minute": server.request_count / max(1, debug_info["uptime_seconds"] / 60)
        }
    
    # Format as JSON for readability
    response = "🔍 MCP Server Debug Information\n\n"
    response += json.dumps(debug_info, indent=2)
    
    logger.info("✅ debug_info completed")
    return response


# Error handling utilities
def format_error_response(error: Exception, tool_name: str) -> List[types.TextContent]:
    """
    Format an error response for the MCP protocol.
    
    This is a helper function for consistent error handling.
    """
    logger.error(f"❌ Error in {tool_name}: {str(error)}")
    
    error_message = f"Error in {tool_name}: {str(error)}"
    return [types.TextContent(type="text", text=error_message)]


def validate_required_params(arguments: Dict[str, Any], required: List[str]) -> None:
    """
    Validate that all required parameters are present.
    
    This is a helper function for parameter validation.
    """
    missing = [param for param in required if param not in arguments]
    if missing:
        raise ValueError(f"Missing required parameters: {', '.join(missing)}")
