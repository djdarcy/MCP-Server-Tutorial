#!/usr/bin/env python
"""
Simple test runner that avoids Unicode issues on Windows
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add the simple_mcp_server directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'simple_mcp_server'))

# Import the modules
from tools import get_all_tools, get_tool_by_name, validate_tool_arguments
from handlers import (
    handle_hello_world,
    handle_echo,
    handle_get_time,
    handle_math_add,
    handle_debug_info
)
from debug_utils import setup_logging, log_mcp_message, create_debug_report

# Setup logging
logger = setup_logging(level="INFO", console_output=False, file_output=True)

def test_tool_discovery():
    """Test that tools are properly defined and discoverable"""
    print("=" * 50)
    print("[INFO] Testing Tool Discovery")
    print("=" * 50)
    
    try:
        tools = get_all_tools()
        print(f"[PASS] Found {len(tools)} tools")
        
        for tool in tools:
            print(f"   [INFO] {tool.name}")
            print(f"      Description: {tool.description}")
            print(f"      Required params: {tool.inputSchema.get('required', [])}")
            print(f"      All params: {list(tool.inputSchema.get('properties', {}).keys())}")
            
            # Test tool retrieval by name
            retrieved_tool = get_tool_by_name(tool.name)
            assert retrieved_tool.name == tool.name
            print(f"      [PASS] Tool retrieval test passed")
            print("")
        
        return True
    except Exception as e:
        print(f"[FAIL] Tool discovery failed: {str(e)}")
        return False

def test_tool_validation():
    """Test tool argument validation"""
    print("=" * 50)
    print("[INFO] Testing Tool Validation")
    print("=" * 50)
    
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
        
        print(f"[TEST] Testing: {description}")
        
        result = validate_tool_arguments(tool_name, args)
        
        if result == should_pass:
            print(f"   [PASS] Validation test passed (result: {result})")
        else:
            print(f"   [FAIL] Validation test failed (expected: {should_pass}, got: {result})")
            return False
    
    return True

def run_tests():
    """Run all tests"""
    print("[INFO] Starting MCP Server Tests")
    print("=" * 50)
    
    tests = [
        ("Tool Discovery", test_tool_discovery),
        ("Tool Validation", test_tool_validation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "[PASS]" if result else "[FAIL]"
            print(f"{status} {test_name} tests")
        except Exception as e:
            results.append((test_name, False))
            print(f"[ERROR] {test_name} tests failed with exception: {str(e)}")
    
    # Summary
    print("")
    print("=" * 50)
    print("[INFO] Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("[PASS] All tests passed! The MCP server is working correctly.")
        return True
    else:
        print("[FAIL] Some tests failed. Check the logs for details.")
        return False

def main():
    """Main test runner"""
    print("[TEST] MCP Server Test Suite")
    print("=" * 50)
    
    try:
        # Run tests
        success = run_tests()
        
        # Generate debug report
        print("\n" + "=" * 50)
        print("[INFO] Debug Report")
        print("=" * 50)
        
        debug_report = create_debug_report()
        print(debug_report)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("[STOP] Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"[ERROR] Test suite crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
