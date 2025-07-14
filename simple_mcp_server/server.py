#!/usr/bin/env python3
"""
Simple MCP Server - Debug Test

This is a minimal Model Context Protocol (MCP) server designed for learning
and debugging the MCP protocol. It exposes a few basic tools to understand
how MCP servers work and how to debug them.

Key Learning Points:
1. MCP server initialization and setup
2. Tool definition and registration
3. Request handling and response formatting
4. Error handling and logging
5. Debugging with VS Code breakpoints

Usage:
    python server.py

Debug Usage:
    Set breakpoints in VS Code and run via launch.json configuration
"""

import asyncio
import sys
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# MCP imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Local imports
from tools import get_all_tools
from handlers import (
    handle_hello_world,
    handle_echo,
    handle_get_time,
    handle_math_add,
    handle_debug_info
)
from debug_utils import setup_logging, log_mcp_message

# Configure logging for debugging
logger = setup_logging()

class SimpleMCPServer:
    """
    A simple MCP server for learning and debugging.
    
    This server implements the minimum required MCP protocol handlers
    and provides detailed logging for understanding the communication flow.
    """
    
    def __init__(self, name: str = "simple-mcp-debug"):
        """Initialize the MCP server"""
        logger.info(f"🚀 Initializing SimpleMCPServer: {name}")
        
        self.server = Server(name)
        self.server_name = name
        self.start_time = datetime.now()
        self.request_count = 0
        
        # Setup MCP protocol handlers
        self._setup_handlers()
        
        logger.info("✅ SimpleMCPServer initialized successfully")
    
    def _setup_handlers(self):
        """Set up MCP protocol handlers with detailed logging"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[types.Tool]:
            """
            Handle list_tools request - this is called when a client
            wants to discover what tools are available.
            """
            self.request_count += 1
            logger.info(f"📋 list_tools request #{self.request_count}")
            
            try:
                tools = get_all_tools()
                logger.info(f"📋 Returning {len(tools)} tools:")
                for tool in tools:
                    logger.info(f"   - {tool.name}: {tool.description}")
                
                log_mcp_message("list_tools", "response", {"tool_count": len(tools)})
                return tools
                
            except Exception as e:
                logger.error(f"❌ Error in list_tools: {str(e)}")
                raise
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Dict[str, Any]
        ) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
            """
            Handle call_tool request - this is called when a client
            wants to execute a specific tool.
            """
            self.request_count += 1
            logger.info(f"🔧 call_tool request #{self.request_count}")
            logger.info(f"   Tool: {name}")
            logger.info(f"   Arguments: {json.dumps(arguments, indent=2)}")
            
            log_mcp_message("call_tool", "request", {
                "tool_name": name,
                "arguments": arguments
            })
            
            try:
                # Route to appropriate handler based on tool name
                if name == "hello_world":
                    result = await handle_hello_world(arguments)
                elif name == "echo":
                    result = await handle_echo(arguments)
                elif name == "get_time":
                    result = await handle_get_time(arguments)
                elif name == "math_add":
                    result = await handle_math_add(arguments)
                elif name == "debug_info":
                    result = await handle_debug_info(arguments, self)
                else:
                    error_msg = f"Unknown tool: {name}"
                    logger.error(f"❌ {error_msg}")
                    result = error_msg
                
                # Ensure result is in the correct format
                if isinstance(result, str):
                    response = [types.TextContent(type="text", text=result)]
                elif isinstance(result, list):
                    response = result
                else:
                    response = [types.TextContent(type="text", text=str(result))]
                
                logger.info(f"✅ Tool {name} executed successfully")
                log_mcp_message("call_tool", "response", {
                    "tool_name": name,
                    "success": True,
                    "response_length": len(str(response))
                })
                
                return response
                
            except Exception as e:
                error_msg = f"Error executing tool {name}: {str(e)}"
                logger.error(f"❌ {error_msg}")
                
                log_mcp_message("call_tool", "error", {
                    "tool_name": name,
                    "error": str(e)
                })
                
                return [types.TextContent(type="text", text=error_msg)]
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> List[types.Prompt]:
            """
            Handle list_prompts request - we don't have prompts in this simple server
            but we implement this for completeness.
            """
            self.request_count += 1
            logger.info(f"📝 list_prompts request #{self.request_count}")
            logger.info("📝 No prompts available in this simple server")
            
            log_mcp_message("list_prompts", "response", {"prompt_count": 0})
            return []
        
        @self.server.get_prompt()
        async def handle_get_prompt(
            name: str,
            arguments: Dict[str, Any]
        ) -> types.GetPromptResult:
            """
            Handle get_prompt request - we don't have prompts in this simple server
            """
            self.request_count += 1
            logger.info(f"📝 get_prompt request #{self.request_count} for: {name}")
            
            log_mcp_message("get_prompt", "error", {
                "prompt_name": name,
                "error": "No prompts available"
            })
            
            raise ValueError(f"No prompt named {name}")
    
    async def run(self):
        """Run the MCP server"""
        logger.info("🌟 Starting SimpleMCPServer...")
        logger.info(f"📊 Server ready to accept connections")
        logger.info(f"🔧 Available tools: {len(get_all_tools())}")
        
        try:
            # This runs the server and handles the MCP protocol
            async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
                logger.info("🔌 MCP server connected via stdio")
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=self.server_name,
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=NotificationOptions(),
                            experimental_capabilities={}
                        )
                    )
                )
        except Exception as e:
            logger.error(f"💥 Server error: {str(e)}")
            raise
        finally:
            logger.info("👋 SimpleMCPServer shutting down")

def main():
    """Main entry point"""
    logger.info("=" * 50)
    logger.info("🚀 SimpleMCPServer Starting...")
    logger.info("=" * 50)
    
    # Create and run the server
    server = SimpleMCPServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
