"""
Debug utilities for the Simple MCP Server

This module provides comprehensive logging and debugging capabilities
for understanding MCP server behavior and diagnosing issues.

Key Learning Points:
1. Structured logging for MCP servers
2. Message tracing and debugging
3. Performance monitoring
4. Error diagnosis and reporting
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Import the safe console handler
try:
    from .unicode_safe import get_safe_console_handler
except ImportError:
    # If relative import fails, try absolute import
    try:
        from unicode_safe import get_safe_console_handler
    except ImportError:
        # If both fail, create a simple fallback
        def get_safe_console_handler():
            return logging.StreamHandler(sys.stdout)


# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Configure logging format
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Set up comprehensive logging for the MCP server.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console_output: Whether to log to console
        file_output: Whether to log to file
    
    Returns:
        Configured logger instance
    """
    
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Create main logger
    logger = logging.getLogger("SimpleMCPServer")
    logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Console handler with proper encoding for Windows
    if console_output:
        console_handler = get_safe_console_handler()
        console_handler.setLevel(numeric_level)
        logger.addHandler(console_handler)
    
    # File handler
    if file_output:
        log_file = LOGS_DIR / f"mcp_server_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Also create a debug file with more detailed logging
        debug_log_file = LOGS_DIR / f"mcp_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        debug_handler = logging.FileHandler(debug_log_file)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Module name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(f"SimpleMCPServer.{name}")


def log_mcp_message(
    message_type: str,
    direction: str,
    data: Dict[str, Any],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log MCP protocol messages with structured format.
    
    Args:
        message_type: Type of MCP message (e.g., 'list_tools', 'call_tool')
        direction: 'request', 'response', or 'error'
        data: Message data to log
        logger: Logger instance (optional)
    """
    if logger is None:
        logger = get_logger("MCPProtocol")
    
    # Create structured log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "message_type": message_type,
        "direction": direction,
        "data": data
    }
    
    # Log with appropriate level
    if direction == "error":
        logger.error(f"MCP {message_type} {direction}: {json.dumps(log_entry, indent=2)}")
    else:
        logger.info(f"MCP {message_type} {direction}: {json.dumps(log_entry, indent=2)}")
    
    # Also write to separate MCP protocol log
    protocol_log_file = LOGS_DIR / "mcp_protocol.jsonl"
    with open(protocol_log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")


def log_performance(
    operation: str,
    duration_ms: float,
    additional_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log performance metrics for debugging.
    
    Args:
        operation: Name of the operation
        duration_ms: Duration in milliseconds
        additional_data: Additional data to log
    """
    logger = get_logger("Performance")
    
    perf_data = {
        "operation": operation,
        "duration_ms": duration_ms,
        "timestamp": datetime.now().isoformat()
    }
    
    if additional_data:
        perf_data.update(additional_data)
    
    logger.info(f"Performance: {json.dumps(perf_data)}")
    
    # Also write to separate performance log
    perf_log_file = LOGS_DIR / "performance.jsonl"
    with open(perf_log_file, "a") as f:
        f.write(json.dumps(perf_data) + "\n")


def log_error_details(
    error: Exception,
    context: Dict[str, Any],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log detailed error information for debugging.
    
    Args:
        error: Exception instance
        context: Context information (e.g., tool name, arguments)
        logger: Logger instance (optional)
    """
    if logger is None:
        logger = get_logger("ErrorDetails")
    
    error_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add stack trace if available
    import traceback
    error_data["stack_trace"] = traceback.format_exc()
    
    logger.error(f"Error details: {json.dumps(error_data, indent=2)}")
    
    # Also write to separate error log
    error_log_file = LOGS_DIR / "errors.jsonl"
    with open(error_log_file, "a") as f:
        f.write(json.dumps(error_data) + "\n")


def create_debug_report() -> str:
    """
    Create a comprehensive debug report.
    
    Returns:
        Debug report as formatted string
    """
    report_lines = [
        "=" * 50,
        "MCP Server Debug Report",
        "=" * 50,
        f"Generated: {datetime.now().isoformat()}",
        "",
        "System Information:",
        f"  Python Version: {sys.version}",
        f"  Platform: {sys.platform}",
        f"  Working Directory: {os.getcwd()}",
        "",
        "Log Files:",
    ]
    
    # List log files
    for log_file in LOGS_DIR.glob("*.log"):
        size = log_file.stat().st_size
        modified = datetime.fromtimestamp(log_file.stat().st_mtime)
        report_lines.append(f"  {log_file.name} ({size} bytes, modified: {modified})")
    
    for log_file in LOGS_DIR.glob("*.jsonl"):
        size = log_file.stat().st_size
        modified = datetime.fromtimestamp(log_file.stat().st_mtime)
        report_lines.append(f"  {log_file.name} ({size} bytes, modified: {modified})")
    
    return "\n".join(report_lines)


# Context manager for timing operations
class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        if self.start_time:
            duration = (self.end_time - self.start_time).total_seconds() * 1000
            
            additional_data = {}
            if exc_type:
                additional_data["error"] = str(exc_val)
            
            log_performance(self.operation_name, duration, additional_data)


# Initialize logging when module is imported
_default_logger = setup_logging()
