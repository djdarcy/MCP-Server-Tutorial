#!/usr/bin/env python3
"""
Test script for the Simple MCP Server

This script tests the MCP server locally without needing Claude Code,
helping us understand the MCP protocol and debug server issues.

Key Learning Points:
1. How to test MCP servers independently
2. Understanding MCP request/response format
3. Debugging server behavior step by step
4. Validating tool definitions and handlers
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add the simple_mcp_server directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "simple_mcp_server"))

from tools import get_all_tools, get_tool_by_name, validate_tool_arguments
from handlers import (
    handle_hello_world,
    handle_echo,
    handle_get_time,
    handle_math_add,
    handle_debug_info
)
from debug_utils import setup_logging, log_mcp_message, create_debug_report

# Set up logging
logger = setup_logging(level="DEBUG")

class MockMCPServer:
    """Mock MCP server for testing"""
    def __init__(self):
        self.server_name = "simple-mcp-debug"
        self.start_time = None
        self.request_count = 0
        
    async def initialize(self):
        """Initialize the mock server"""
        from datetime import datetime
        self.start_time = datetime.now()
        logger.info("🚀 Mock MCP Server initialized")

async def test_tool_discovery():
    """Test that tools are properly defined and discoverable"""
    logger.info("=" * 50)
    logger.info("🔍 Testing Tool Discovery")
    logger.info("=" * 50)
    
    try:
        tools = get_all_tools()
        logger.info(f"✅ Found {len(tools)} tools:")
        
        for tool in tools:
            logger.info(f"   📋 {tool.name}")
            logger.info(f"      Description: {tool.description}")
            logger.info(f"      Required params: {tool.inputSchema.get('required', [])}")
            logger.info(f"      All params: {list(tool.inputSchema.get('properties', {}).keys())}")
            
            # Test tool retrieval by name
            retrieved_tool = get_tool_by_name(tool.name)
            assert retrieved_tool.name == tool.name
            logger.info(f"      ✅ Tool retrieval test passed")
            
            logger.info("")
        
        return True
    except Exception as e:
        logger.error(f"❌ Tool discovery failed: {str(e)}")
        return False

async def test_tool_validation():
    """Test tool argument validation"""
    logger.info("=" * 50)
    logger.info("🔍 Testing Tool Validation")
    logger.info("=" * 50)
    
    test_cases = [
        # hello_world tests
        {
            "tool": "hello_world",
            "args": {},
            "should_pass": True,
            "description": "hello_world with no args"
        },
        {
            "tool": "hello_world",
            "args": {"name": "Test"},
            "should_pass": True,
            "description": "hello_world with name"
        },
        
        # echo tests
        {
            "tool": "echo",
            "args": {"message": "Hello"},
            "should_pass": True,
            "description": "echo with required message"
        },
        {
            "tool": "echo",
            "args": {},
            "should_pass": False,
            "description": "echo without required message"
        },
        
        # math_add tests
        {
            "tool": "math_add",
            "args": {"a": 5, "b": 3},
            "should_pass": True,
            "description": "math_add with valid numbers"
        },
        {
            "tool": "math_add",
            "args": {"a": 5},
            "should_pass": False,
            "description": "math_add missing parameter b"
        },
    ]
    
    for test_case in test_cases:
        tool_name = test_case["tool"]
        args = test_case["args"]
        should_pass = test_case["should_pass"]
        description = test_case["description"]
        
        logger.info(f"🧪 Testing: {description}")
        
        result = validate_tool_arguments(tool_name, args)
        
        if result == should_pass:
            logger.info(f"   ✅ Validation test passed (result: {result})")
        else:
            logger.error(f"   ❌ Validation test failed (expected: {should_pass}, got: {result})")
            return False
    
    return True

async def test_tool_handlers():
    """Test individual tool handlers"""
    logger.info("=" * 50)
    logger.info("🔍 Testing Tool Handlers")
    logger.info("=" * 50)
    
    # Create mock server for debug_info
    mock_server = MockMCPServer()
    await mock_server.initialize()
    
    test_cases = [
        {
            "handler": handle_hello_world,
            "args": {"name": "TestUser"},
            "expected_contains": "Hello, TestUser",
            "description": "hello_world handler"
        },
        {
            "handler": handle_echo,
            "args": {"message": "Test message", "prefix": "Echo: "},
            "expected_contains": "Echo: Test message",
            "description": "echo handler"
        },
        {
            "handler": handle_get_time,
            "args": {"format": "readable"},
            "expected_contains": "Current time:",
            "description": "get_time handler"
        },
        {
            "handler": handle_math_add,
            "args": {"a": 10, "b": 5},
            "expected_contains": "10 + 5 = 15",
            "description": "math_add handler"
        },
        {
            "handler": lambda args: handle_debug_info(args, mock_server),
            "args": {"include_tools": True},
            "expected_contains": "Debug Information",
            "description": "debug_info handler"
        }
    ]
    
    for test_case in test_cases:
        handler = test_case["handler"]
        args = test_case["args"]
        expected_contains = test_case["expected_contains"]
        description = test_case["description"]
        
        logger.info(f"🧪 Testing: {description}")
        
        try:
            result = await handler(args)
            
            if expected_contains in result:
                logger.info(f"   ✅ Handler test passed")
                logger.info(f"   📄 Result preview: {result[:100]}...")
            else:
                logger.error(f"   ❌ Handler test failed: expected '{expected_contains}' not found")
                logger.error(f"   📄 Actual result: {result}")
                return False
                
        except Exception as e:
            logger.error(f"   ❌ Handler test failed with exception: {str(e)}")
            return False
    
    return True

async def test_error_handling():
    """Test error handling in tool handlers"""
    logger.info("=" * 50)
    logger.info("🔍 Testing Error Handling")
    logger.info("=" * 50)
    
    # Test cases that should raise errors
    error_test_cases = [
        {
            "handler": handle_echo,
            "args": {},  # Missing required 'message' parameter
            "description": "echo without required message"
        },
        {
            "handler": handle_math_add,
            "args": {"a": "not_a_number", "b": 5},
            "description": "math_add with invalid number"
        },
        {
            "handler": handle_get_time,
            "args": {"format": "invalid_format"},
            "description": "get_time with invalid format"
        }
    ]
    
    for test_case in error_test_cases:
        handler = test_case["handler"]
        args = test_case["args"]
        description = test_case["description"]
        
        logger.info(f"🧪 Testing error case: {description}")
        
        try:
            result = await handler(args)
            logger.error(f"   ❌ Expected error but got result: {result}")
            return False
        except Exception as e:
            logger.info(f"   ✅ Correctly caught error: {str(e)}")
    
    return True

async def run_all_tests():
    """Run all tests"""
    logger.info("🧪 Starting MCP Server Tests")
    logger.info("=" * 50)
    
    test_results = []
    
    # Run tests
    tests = [
        ("Tool Discovery", test_tool_discovery),
        ("Tool Validation", test_tool_validation),
        ("Tool Handlers", test_tool_handlers),
        ("Error Handling", test_error_handling)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"🏃 Running {test_name} tests...")
        try:
            result = await test_func()
            test_results.append((test_name, result))
            if result:
                logger.info(f"✅ {test_name} tests PASSED")
            else:
                logger.error(f"❌ {test_name} tests FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} tests CRASHED: {str(e)}")
            test_results.append((test_name, False))
        
        logger.info("")
    
    # Summary
    logger.info("=" * 50)
    logger.info("📊 Test Summary")
    logger.info("=" * 50)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("[PASS] All tests passed! The MCP server is working correctly.")
        return True
    else:
        logger.error("[FAIL] Some tests failed. Check the logs for details.")
        return False

def main():
    """Main test runner"""
    print("[TEST] MCP Server Test Suite")
    print("=" * 50)
    
    try:
        # Run tests
        success = asyncio.run(run_all_tests())
        
        # Generate debug report
        logger.info("\n" + "=" * 50)
        logger.info("[INFO] Debug Report")
        logger.info("=" * 50)
        
        debug_report = create_debug_report()
        logger.info(debug_report)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        logger.info("[STOP] Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"[ERROR] Test suite crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
