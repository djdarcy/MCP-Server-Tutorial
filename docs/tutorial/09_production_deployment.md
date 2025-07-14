# Chapter 9: Production Deployment

## Overview

This chapter covers production deployment strategies, monitoring and logging systems, production-ready error handling, scaling considerations, and operational best practices for MCP servers.

## Production Architecture

### 1. Production Server Structure

```python
# production_server.py - Production-ready MCP server
import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

# Production imports
from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Production modules
from .auth import ProductionAuth
from .monitoring import MetricsCollector, HealthMonitor
from .logging_config import setup_production_logging
from .config import ProductionConfig
from .cache import ProductionCache
from .rate_limiting import ProductionRateLimiter
from .tools import ProductionTools

@dataclass
class ServerMetrics:
    """Server metrics for monitoring."""
    requests_total: int = 0
    requests_failed: int = 0
    requests_success: int = 0
    response_time_avg: float = 0.0
    active_connections: int = 0
    uptime_seconds: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

class ProductionMCPServer:
    """Production-ready MCP server with full monitoring and error handling."""
    
    def __init__(self, config_path: str = "config/production.json"):
        self.config = ProductionConfig(config_path)
        self.logger = setup_production_logging(self.config.log_level)
        
        # Initialize server
        self.server = Server(self.config.server_name)
        
        # Initialize components
        self.auth = ProductionAuth(self.config.auth_config)
        self.cache = ProductionCache(self.config.cache_config)
        self.rate_limiter = ProductionRateLimiter(self.config.rate_limit_config)
        self.metrics = MetricsCollector()
        self.health_monitor = HealthMonitor()
        
        # Server state
        self.start_time = datetime.now()
        self.is_running = False
        self.metrics_data = ServerMetrics()
        
        # Tools
        self.tools = ProductionTools(
            auth=self.auth,
            cache=self.cache,
            metrics=self.metrics
        )
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        # Setup request handlers
        self._setup_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, self._signal_handler)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())
    
    def _setup_handlers(self):
        """Setup MCP request handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Handle list_tools request with monitoring."""
            start_time = datetime.now()
            
            try:
                # Update metrics
                self.metrics_data.requests_total += 1
                
                # Get tools
                tools = await self.tools.get_all_tools()
                
                # Log request
                self.logger.info(f"Returned {len(tools)} tools")
                
                # Update success metrics
                self.metrics_data.requests_success += 1
                self._update_response_time(start_time)
                
                return tools
                
            except Exception as e:
                self.metrics_data.requests_failed += 1
                self.logger.error(f"Error in list_tools: {str(e)}", exc_info=True)
                raise
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Dict[str, Any]
        ) -> types.CallToolResult:
            """Handle tool calls with full production monitoring."""
            start_time = datetime.now()
            request_id = self.metrics.generate_request_id()
            
            try:
                # Update metrics
                self.metrics_data.requests_total += 1
                
                # Log request
                self.logger.info(f"Tool call: {name} (ID: {request_id})")
                
                # Rate limiting
                if not await self.rate_limiter.is_allowed(request_id):
                    self.logger.warning(f"Rate limit exceeded for request {request_id}")
                    return types.CallToolResult(
                        content=[types.TextContent(
                            type="text",
                            text="Rate limit exceeded. Please try again later."
                        )],
                        isError=True
                    )
                
                # Authentication
                if not await self.auth.authenticate_request(request_id):
                    self.logger.warning(f"Authentication failed for request {request_id}")
                    return types.CallToolResult(
                        content=[types.TextContent(
                            type="text",
                            text="Authentication required"
                        )],
                        isError=True
                    )
                
                # Execute tool
                result = await self.tools.execute_tool(name, arguments, request_id)
                
                # Update success metrics
                self.metrics_data.requests_success += 1
                self._update_response_time(start_time)
                
                self.logger.info(f"Tool call completed: {name} (ID: {request_id})")
                return result
                
            except Exception as e:
                self.metrics_data.requests_failed += 1
                self.logger.error(f"Error in tool call {name}: {str(e)}", exc_info=True)
                
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text=f"Internal server error: {str(e)}"
                    )],
                    isError=True
                )
    
    def _update_response_time(self, start_time: datetime):
        """Update response time metrics."""
        response_time = (datetime.now() - start_time).total_seconds()
        
        # Update rolling average
        if self.metrics_data.requests_success > 0:
            self.metrics_data.response_time_avg = (
                (self.metrics_data.response_time_avg * (self.metrics_data.requests_success - 1) + response_time) 
                / self.metrics_data.requests_success
            )
        else:
            self.metrics_data.response_time_avg = response_time
    
    async def start(self):
        """Start the production server."""
        self.logger.info(f"Starting {self.config.server_name} server")
        
        try:
            # Initialize components
            await self.auth.initialize()
            await self.cache.initialize()
            await self.rate_limiter.initialize()
            await self.metrics.initialize()
            
            # Start health monitoring
            await self.health_monitor.start()
            
            self.is_running = True
            self.logger.info("Production server started successfully")
            
            # Start metrics collection
            asyncio.create_task(self._collect_metrics())
            
        except Exception as e:
            self.logger.error(f"Failed to start server: {str(e)}", exc_info=True)
            raise
    
    async def shutdown(self):
        """Graceful shutdown of the server."""
        self.logger.info("Initiating graceful shutdown")
        
        self.is_running = False
        
        try:
            # Stop health monitoring
            await self.health_monitor.stop()
            
            # Shutdown components
            await self.metrics.shutdown()
            await self.rate_limiter.shutdown()
            await self.cache.shutdown()
            await self.auth.shutdown()
            
            self.logger.info("Graceful shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {str(e)}", exc_info=True)
    
    async def _collect_metrics(self):
        """Collect server metrics periodically."""
        while self.is_running:
            try:
                # Update uptime
                self.metrics_data.uptime_seconds = (
                    datetime.now() - self.start_time
                ).total_seconds()
                
                # Update system metrics
                import psutil
                process = psutil.Process()
                self.metrics_data.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                self.metrics_data.cpu_usage_percent = process.cpu_percent()
                
                # Send metrics to monitoring system
                await self.metrics.record_metrics(self.metrics_data)
                
                # Sleep for metrics interval
                await asyncio.sleep(self.config.metrics_interval)
                
            except Exception as e:
                self.logger.error(f"Error collecting metrics: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get server health status."""
        return {
            "status": "healthy" if self.is_running else "unhealthy",
            "uptime": self.metrics_data.uptime_seconds,
            "metrics": {
                "requests_total": self.metrics_data.requests_total,
                "requests_success": self.metrics_data.requests_success,
                "requests_failed": self.metrics_data.requests_failed,
                "response_time_avg": self.metrics_data.response_time_avg,
                "memory_usage_mb": self.metrics_data.memory_usage_mb,
                "cpu_usage_percent": self.metrics_data.cpu_usage_percent
            },
            "components": {
                "auth": await self.auth.get_health_status(),
                "cache": await self.cache.get_health_status(),
                "rate_limiter": await self.rate_limiter.get_health_status()
            }
        }

# Production server runner
async def run_production_server():
    """Run the production server."""
    server = ProductionMCPServer()
    
    try:
        await server.start()
        
        # Run server using MCP stdio
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.server.run(
                read_stream, 
                write_stream, 
                InitializationOptions(
                    server_name=server.config.server_name,
                    server_version=server.config.server_version
                )
            )
    
    except KeyboardInterrupt:
        server.logger.info("Received keyboard interrupt")
    except Exception as e:
        server.logger.error(f"Server error: {str(e)}", exc_info=True)
    finally:
        await server.shutdown()

if __name__ == "__main__":
    asyncio.run(run_production_server())
```

## Production Configuration

### 1. Configuration Management

```python
# config.py - Production configuration management
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class AuthConfig:
    """Authentication configuration."""
    enabled: bool = True
    auth_type: str = "api_key"
    api_keys_file: str = "config/api_keys.json"
    oauth2_client_id: str = ""
    oauth2_client_secret: str = ""
    oauth2_auth_server: str = ""

@dataclass
class CacheConfig:
    """Cache configuration."""
    enabled: bool = True
    cache_type: str = "memory"
    max_size: int = 1000
    max_memory_mb: int = 100
    ttl_seconds: int = 3600
    redis_url: str = ""

@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    requests_per_minute: int = 100
    burst_size: int = 10
    cleanup_interval: int = 300

@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "logs/production.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    json_format: bool = True

class ProductionConfig:
    """Production configuration manager."""
    
    def __init__(self, config_path: str = "config/production.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Initialize typed configs
        self.auth_config = AuthConfig(**self.config.get("auth", {}))
        self.cache_config = CacheConfig(**self.config.get("cache", {}))
        self.rate_limit_config = RateLimitConfig(**self.config.get("rate_limit", {}))
        self.logging_config = LoggingConfig(**self.config.get("logging", {}))
        
        # Server configuration
        self.server_name = self.config.get("server_name", "production-mcp-server")
        self.server_version = self.config.get("server_version", "1.0.0")
        self.metrics_interval = self.config.get("metrics_interval", 60)
        self.log_level = self.logging_config.level
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.config_path.exists():
            return self._create_default_config()
        
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {str(e)}")
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration."""
        default_config = {
            "server_name": "production-mcp-server",
            "server_version": "1.0.0",
            "metrics_interval": 60,
            "auth": {
                "enabled": True,
                "auth_type": "api_key",
                "api_keys_file": "config/api_keys.json"
            },
            "cache": {
                "enabled": True,
                "cache_type": "memory",
                "max_size": 1000,
                "max_memory_mb": 100,
                "ttl_seconds": 3600
            },
            "rate_limit": {
                "enabled": True,
                "requests_per_minute": 100,
                "burst_size": 10,
                "cleanup_interval": 300
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_path": "logs/production.log",
                "max_file_size_mb": 10,
                "backup_count": 5,
                "json_format": True
            }
        }
        
        # Save default config
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        return default_config
    
    def get_environment_overrides(self) -> Dict[str, Any]:
        """Get configuration overrides from environment variables."""
        overrides = {}
        
        # Server configuration
        if os.getenv("MCP_SERVER_NAME"):
            overrides["server_name"] = os.getenv("MCP_SERVER_NAME")
        
        # Auth configuration
        if os.getenv("MCP_AUTH_ENABLED"):
            overrides["auth"] = overrides.get("auth", {})
            overrides["auth"]["enabled"] = os.getenv("MCP_AUTH_ENABLED").lower() == "true"
        
        if os.getenv("MCP_API_KEY"):
            overrides["auth"] = overrides.get("auth", {})
            overrides["auth"]["api_key"] = os.getenv("MCP_API_KEY")
        
        # Logging configuration
        if os.getenv("MCP_LOG_LEVEL"):
            overrides["logging"] = overrides.get("logging", {})
            overrides["logging"]["level"] = os.getenv("MCP_LOG_LEVEL")
        
        return overrides
    
    def apply_environment_overrides(self):
        """Apply environment variable overrides."""
        overrides = self.get_environment_overrides()
        
        def deep_update(base_dict, update_dict):
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict:
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value
        
        deep_update(self.config, overrides)
```

## Monitoring and Metrics

### 1. Comprehensive Monitoring System

```python
# monitoring.py - Production monitoring and metrics
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import defaultdict, deque

@dataclass
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and aggregates server metrics."""
    
    def __init__(self):
        self.metrics_buffer: List[MetricPoint] = []
        self.metric_aggregates: Dict[str, List[float]] = defaultdict(list)
        self.request_durations: deque = deque(maxlen=1000)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.running = False
    
    async def initialize(self):
        """Initialize metrics collection."""
        self.running = True
        asyncio.create_task(self._flush_metrics())
    
    async def shutdown(self):
        """Shutdown metrics collection."""
        self.running = False
        await self._flush_metrics()
    
    def generate_request_id(self) -> str:
        """Generate unique request ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def record_metrics(self, metrics_data: 'ServerMetrics'):
        """Record server metrics."""
        timestamp = datetime.now()
        
        # Record basic metrics
        self.metrics_buffer.extend([
            MetricPoint("requests_total", metrics_data.requests_total, timestamp),
            MetricPoint("requests_success", metrics_data.requests_success, timestamp),
            MetricPoint("requests_failed", metrics_data.requests_failed, timestamp),
            MetricPoint("response_time_avg", metrics_data.response_time_avg, timestamp),
            MetricPoint("memory_usage_mb", metrics_data.memory_usage_mb, timestamp),
            MetricPoint("cpu_usage_percent", metrics_data.cpu_usage_percent, timestamp),
            MetricPoint("uptime_seconds", metrics_data.uptime_seconds, timestamp)
        ])
    
    def record_request_duration(self, duration: float, tool_name: str):
        """Record request duration."""
        self.request_durations.append(duration)
        
        # Add to metrics buffer
        self.metrics_buffer.append(MetricPoint(
            name="request_duration",
            value=duration,
            timestamp=datetime.now(),
            tags={"tool": tool_name}
        ))
    
    def record_error(self, error_type: str, tool_name: str = None):
        """Record error occurrence."""
        self.error_counts[error_type] += 1
        
        # Add to metrics buffer
        tags = {"error_type": error_type}
        if tool_name:
            tags["tool"] = tool_name
        
        self.metrics_buffer.append(MetricPoint(
            name="error_count",
            value=1,
            timestamp=datetime.now(),
            tags=tags
        ))
    
    async def _flush_metrics(self):
        """Flush metrics to storage/monitoring system."""
        while self.running:
            try:
                if self.metrics_buffer:
                    # In production, send to monitoring system (e.g., Prometheus, CloudWatch)
                    await self._send_to_monitoring_system(self.metrics_buffer)
                    self.metrics_buffer.clear()
                
                await asyncio.sleep(30)  # Flush every 30 seconds
                
            except Exception as e:
                logger.error(f"Error flushing metrics: {str(e)}")
                await asyncio.sleep(5)
    
    async def _send_to_monitoring_system(self, metrics: List[MetricPoint]):
        """Send metrics to external monitoring system."""
        # Example: Send to Prometheus pushgateway
        # In production, implement actual monitoring system integration
        
        for metric in metrics:
            logger.debug(f"Metric: {metric.name} = {metric.value} @ {metric.timestamp}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of collected metrics."""
        return {
            "buffer_size": len(self.metrics_buffer),
            "recent_request_durations": list(self.request_durations)[-10:],
            "error_counts": dict(self.error_counts),
            "collection_running": self.running
        }

class HealthMonitor:
    """Monitors server health and performs health checks."""
    
    def __init__(self):
        self.health_checks: Dict[str, callable] = {}
        self.health_status: Dict[str, Any] = {}
        self.running = False
    
    async def start(self):
        """Start health monitoring."""
        self.running = True
        asyncio.create_task(self._run_health_checks())
    
    async def stop(self):
        """Stop health monitoring."""
        self.running = False
    
    def register_health_check(self, name: str, check_func: callable):
        """Register a health check function."""
        self.health_checks[name] = check_func
    
    async def _run_health_checks(self):
        """Run health checks periodically."""
        while self.running:
            try:
                for name, check_func in self.health_checks.items():
                    try:
                        result = await check_func()
                        self.health_status[name] = {
                            "status": "healthy" if result else "unhealthy",
                            "last_check": datetime.now().isoformat(),
                            "details": result if isinstance(result, dict) else {}
                        }
                    except Exception as e:
                        self.health_status[name] = {
                            "status": "error",
                            "last_check": datetime.now().isoformat(),
                            "error": str(e)
                        }
                
                await asyncio.sleep(60)  # Run health checks every minute
                
            except Exception as e:
                logger.error(f"Error running health checks: {str(e)}")
                await asyncio.sleep(10)
    
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall health status."""
        unhealthy_checks = [
            name for name, status in self.health_status.items()
            if status["status"] != "healthy"
        ]
        
        return {
            "overall_status": "healthy" if not unhealthy_checks else "unhealthy",
            "checks": self.health_status,
            "unhealthy_checks": unhealthy_checks,
            "last_update": datetime.now().isoformat()
        }
```

## Production Logging

### 1. Structured Logging System

```python
# logging_config.py - Production logging configuration
import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message']:
                log_entry[key] = value
        
        return json.dumps(log_entry)

class ProductionLogHandler(logging.Handler):
    """Custom log handler for production environment."""
    
    def __init__(self, log_file: str, max_size_mb: int = 10, backup_count: int = 5):
        super().__init__()
        
        # Setup rotating file handler
        self.file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        
        # Setup console handler
        self.console_handler = logging.StreamHandler(sys.stdout)
        
        # Set JSON formatter
        json_formatter = JSONFormatter()
        self.file_handler.setFormatter(json_formatter)
        self.console_handler.setFormatter(json_formatter)
    
    def emit(self, record: logging.LogRecord):
        """Emit log record to both file and console."""
        self.file_handler.emit(record)
        self.console_handler.emit(record)

def setup_production_logging(log_level: str = "INFO") -> logging.Logger:
    """Setup production logging configuration."""
    
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Add production handler
    production_handler = ProductionLogHandler(
        log_file=str(log_dir / "production.log"),
        max_size_mb=10,
        backup_count=5
    )
    logger.addHandler(production_handler)
    
    # Add error handler (separate file for errors)
    error_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_dir / "errors.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    logger.addHandler(error_handler)
    
    # Log startup
    logger.info("Production logging initialized", extra={
        "log_level": log_level,
        "log_file": str(log_dir / "production.log")
    })
    
    return logger

class RequestLogger:
    """Specialized logger for request/response logging."""
    
    def __init__(self):
        self.logger = logging.getLogger("mcp.requests")
    
    def log_request(self, request_id: str, tool_name: str, arguments: Dict[str, Any]):
        """Log incoming request."""
        self.logger.info("Request received", extra={
            "request_id": request_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "event_type": "request"
        })
    
    def log_response(self, request_id: str, tool_name: str, success: bool, 
                    response_time: float, error: str = None):
        """Log response."""
        self.logger.info("Request completed", extra={
            "request_id": request_id,
            "tool_name": tool_name,
            "success": success,
            "response_time_ms": response_time * 1000,
            "error": error,
            "event_type": "response"
        })
    
    def log_error(self, request_id: str, tool_name: str, error: Exception):
        """Log error."""
        self.logger.error("Request error", extra={
            "request_id": request_id,
            "tool_name": tool_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "event_type": "error"
        }, exc_info=True)
```

## Scaling and Performance

### 1. Performance Optimization

```python
# performance.py - Performance optimization for production
import asyncio
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

@dataclass
class PerformanceConfig:
    """Performance optimization configuration."""
    max_concurrent_requests: int = 100
    request_timeout: float = 30.0
    thread_pool_size: int = multiprocessing.cpu_count()
    connection_pool_size: int = 10
    cache_ttl: int = 3600
    enable_request_batching: bool = True
    batch_size: int = 10
    batch_timeout: float = 0.1

class PerformanceOptimizer:
    """Performance optimization manager."""
    
    def __init__(self, config: PerformanceConfig):
        self.config = config
        self.thread_pool = ThreadPoolExecutor(max_workers=config.thread_pool_size)
        self.request_semaphore = asyncio.Semaphore(config.max_concurrent_requests)
        self.request_batches: Dict[str, List[Any]] = {}
        self.running = False
    
    async def initialize(self):
        """Initialize performance optimization."""
        self.running = True
        
        if self.config.enable_request_batching:
            asyncio.create_task(self._process_batches())
    
    async def shutdown(self):
        """Shutdown performance optimization."""
        self.running = False
        self.thread_pool.shutdown(wait=True)
    
    async def execute_with_optimization(self, func: callable, *args, **kwargs):
        """Execute function with performance optimization."""
        async with self.request_semaphore:
            # Add timeout
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.request_timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError(f"Request timed out after {self.config.request_timeout}s")
    
    async def execute_cpu_bound(self, func: callable, *args, **kwargs):
        """Execute CPU-bound function in thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
    
    async def add_to_batch(self, batch_key: str, item: Any):
        """Add item to batch for processing."""
        if batch_key not in self.request_batches:
            self.request_batches[batch_key] = []
        
        self.request_batches[batch_key].append(item)
        
        # Process batch if it's full
        if len(self.request_batches[batch_key]) >= self.config.batch_size:
            await self._process_batch(batch_key)
    
    async def _process_batches(self):
        """Process batches periodically."""
        while self.running:
            try:
                # Process all batches
                for batch_key in list(self.request_batches.keys()):
                    if self.request_batches[batch_key]:
                        await self._process_batch(batch_key)
                
                await asyncio.sleep(self.config.batch_timeout)
                
            except Exception as e:
                logger.error(f"Error processing batches: {str(e)}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, batch_key: str):
        """Process a single batch."""
        if batch_key not in self.request_batches or not self.request_batches[batch_key]:
            return
        
        batch = self.request_batches[batch_key]
        self.request_batches[batch_key] = []
        
        # Process batch items
        # Implementation depends on specific use case
        logger.debug(f"Processing batch {batch_key} with {len(batch)} items")

class ConnectionPool:
    """Connection pool for external resources."""
    
    def __init__(self, factory: callable, max_connections: int = 10):
        self.factory = factory
        self.max_connections = max_connections
        self.available_connections = asyncio.Queue(maxsize=max_connections)
        self.total_connections = 0
        self.connection_stats = {
            "created": 0,
            "active": 0,
            "errors": 0
        }
    
    async def get_connection(self):
        """Get connection from pool."""
        try:
            # Try to get existing connection
            connection = self.available_connections.get_nowait()
            self.connection_stats["active"] += 1
            return connection
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if self.total_connections < self.max_connections:
                connection = await self.factory()
                self.total_connections += 1
                self.connection_stats["created"] += 1
                self.connection_stats["active"] += 1
                return connection
            else:
                # Wait for available connection
                connection = await self.available_connections.get()
                self.connection_stats["active"] += 1
                return connection
    
    async def return_connection(self, connection):
        """Return connection to pool."""
        try:
            self.available_connections.put_nowait(connection)
            self.connection_stats["active"] -= 1
        except asyncio.QueueFull:
            # Pool is full, close connection
            await self._close_connection(connection)
            self.total_connections -= 1
            self.connection_stats["active"] -= 1
    
    async def _close_connection(self, connection):
        """Close connection."""
        try:
            if hasattr(connection, 'close'):
                await connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
            self.connection_stats["errors"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        return {
            "total_connections": self.total_connections,
            "available_connections": self.available_connections.qsize(),
            "max_connections": self.max_connections,
            "stats": self.connection_stats
        }
```

## Deployment Strategies

### 1. Docker Deployment

```dockerfile
# Dockerfile - Production Docker image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MCP_ENVIRONMENT=production

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs config data \
    && chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run the application
CMD ["python", "production_server.py"]
```

```yaml
# docker-compose.yml - Production deployment
version: '3.8'

services:
  mcp-server:
    build: .
    restart: unless-stopped
    environment:
      - MCP_SERVER_NAME=production-mcp-server
      - MCP_LOG_LEVEL=INFO
      - MCP_AUTH_ENABLED=true
      - MCP_METRICS_ENABLED=true
    volumes:
      - ./config:/app/config:ro
      - ./logs:/app/logs
      - ./data:/app/data
    networks:
      - mcp-network
    depends_on:
      - redis
      - prometheus
    
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis-data:/data
    networks:
      - mcp-network
    
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - mcp-network
    
  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    ports:
      - "3000:3000"
    networks:
      - mcp-network
    depends_on:
      - prometheus

volumes:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  mcp-network:
    driver: bridge
```

### 2. Kubernetes Deployment

```yaml
# k8s-deployment.yaml - Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
  labels:
    app: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
      - name: mcp-server
        image: mcp-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: MCP_SERVER_NAME
          value: "production-mcp-server"
        - name: MCP_LOG_LEVEL
          value: "INFO"
        - name: MCP_AUTH_ENABLED
          value: "true"
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: config
          mountPath: /app/config
          readOnly: true
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: mcp-config
      - name: logs
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server-service
spec:
  selector:
    app: mcp-server
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mcp-config
data:
  production.json: |
    {
      "server_name": "production-mcp-server",
      "server_version": "1.0.0",
      "auth": {
        "enabled": true,
        "auth_type": "api_key"
      },
      "logging": {
        "level": "INFO",
        "json_format": true
      }
    }
```

## Production Tools and Scripts

### 1. Deployment Scripts

```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e

# Configuration
APP_NAME="mcp-server"
DOCKER_IMAGE="mcp-server:latest"
DEPLOY_ENV=${1:-production}

echo "Deploying $APP_NAME to $DEPLOY_ENV environment..."

# Build Docker image
echo "Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Run tests
echo "Running tests..."
docker run --rm $DOCKER_IMAGE python -m pytest tests/

# Deploy based on environment
if [ "$DEPLOY_ENV" = "production" ]; then
    echo "Deploying to production..."
    
    # Update production deployment
    docker-compose -f docker-compose.prod.yml down
    docker-compose -f docker-compose.prod.yml up -d
    
    # Wait for health check
    echo "Waiting for health check..."
    sleep 30
    
    # Verify deployment
    if curl -f http://localhost:8080/health; then
        echo "✅ Deployment successful!"
    else
        echo "❌ Deployment failed!"
        exit 1
    fi
    
elif [ "$DEPLOY_ENV" = "k8s" ]; then
    echo "Deploying to Kubernetes..."
    
    # Apply Kubernetes manifests
    kubectl apply -f k8s-deployment.yaml
    
    # Wait for rollout
    kubectl rollout status deployment/mcp-server
    
    echo "✅ Kubernetes deployment successful!"
    
else
    echo "Unknown environment: $DEPLOY_ENV"
    exit 1
fi

echo "Deployment completed successfully!"
```

```python
# deployment_manager.py - Deployment management tools
import subprocess
import json
import time
from typing import Dict, Any, List
from pathlib import Path

class DeploymentManager:
    """Manages production deployments."""
    
    def __init__(self, config_path: str = "config/deployment.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration."""
        if not self.config_path.exists():
            return {
                "environments": {
                    "production": {
                        "type": "docker-compose",
                        "config_file": "docker-compose.prod.yml"
                    },
                    "k8s": {
                        "type": "kubernetes",
                        "namespace": "mcp-server",
                        "config_file": "k8s-deployment.yaml"
                    }
                }
            }
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def deploy(self, environment: str) -> Dict[str, Any]:
        """Deploy to specified environment."""
        env_config = self.config["environments"].get(environment)
        
        if not env_config:
            return {
                "success": False,
                "error": f"Environment '{environment}' not found"
            }
        
        deploy_type = env_config["type"]
        
        if deploy_type == "docker-compose":
            return self._deploy_docker_compose(env_config)
        elif deploy_type == "kubernetes":
            return self._deploy_kubernetes(env_config)
        else:
            return {
                "success": False,
                "error": f"Unknown deployment type: {deploy_type}"
            }
    
    def _deploy_docker_compose(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy using Docker Compose."""
        config_file = config["config_file"]
        
        try:
            # Build and deploy
            subprocess.run(["docker-compose", "-f", config_file, "down"], check=True)
            subprocess.run(["docker-compose", "-f", config_file, "up", "-d"], check=True)
            
            # Wait for health check
            time.sleep(30)
            
            # Verify deployment
            result = subprocess.run(["curl", "-f", "http://localhost:8080/health"], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": "Docker Compose deployment successful"
                }
            else:
                return {
                    "success": False,
                    "error": "Health check failed"
                }
        
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Deployment failed: {str(e)}"
            }
    
    def _deploy_kubernetes(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy using Kubernetes."""
        config_file = config["config_file"]
        namespace = config.get("namespace", "default")
        
        try:
            # Apply manifests
            subprocess.run(["kubectl", "apply", "-f", config_file], check=True)
            
            # Wait for rollout
            subprocess.run([
                "kubectl", "rollout", "status", "deployment/mcp-server",
                "-n", namespace
            ], check=True)
            
            return {
                "success": True,
                "message": "Kubernetes deployment successful"
            }
        
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Kubernetes deployment failed: {str(e)}"
            }
    
    def get_deployment_status(self, environment: str) -> Dict[str, Any]:
        """Get deployment status."""
        env_config = self.config["environments"].get(environment)
        
        if not env_config:
            return {
                "status": "unknown",
                "error": f"Environment '{environment}' not found"
            }
        
        deploy_type = env_config["type"]
        
        if deploy_type == "docker-compose":
            return self._get_docker_compose_status(env_config)
        elif deploy_type == "kubernetes":
            return self._get_kubernetes_status(env_config)
        else:
            return {
                "status": "unknown",
                "error": f"Unknown deployment type: {deploy_type}"
            }
    
    def _get_docker_compose_status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get Docker Compose deployment status."""
        config_file = config["config_file"]
        
        try:
            result = subprocess.run([
                "docker-compose", "-f", config_file, "ps", "--format", "json"
            ], capture_output=True, text=True, check=True)
            
            services = json.loads(result.stdout)
            
            return {
                "status": "running",
                "services": services
            }
        
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _get_kubernetes_status(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get Kubernetes deployment status."""
        namespace = config.get("namespace", "default")
        
        try:
            result = subprocess.run([
                "kubectl", "get", "deployment", "mcp-server",
                "-n", namespace, "-o", "json"
            ], capture_output=True, text=True, check=True)
            
            deployment = json.loads(result.stdout)
            
            return {
                "status": "running",
                "deployment": deployment
            }
        
        except subprocess.CalledProcessError as e:
            return {
                "status": "error",
                "error": str(e)
            }
```

## Summary

This chapter covered:

1. **Production Architecture**: Complete production-ready server implementation with monitoring and health checks
2. **Configuration Management**: Comprehensive configuration system with environment overrides
3. **Monitoring and Metrics**: Full monitoring system with metrics collection and health monitoring
4. **Logging System**: Structured JSON logging with rotation and error handling
5. **Performance Optimization**: Connection pooling, batching, and performance monitoring
6. **Deployment Strategies**: Docker, Kubernetes, and deployment automation
7. **Production Tools**: Deployment scripts and management utilities

The production deployment system provides a robust foundation for running MCP servers in production environments with proper monitoring, logging, and operational support.

## Next Steps

This completes the comprehensive MCP tutorial series. The tutorial now provides:

- Complete understanding of MCP architecture and protocol
- Practical implementation examples
- Debugging and testing strategies
- Security and authentication
- State management and performance optimization
- Claude Desktop integration
- Production deployment strategies

The tutorial serves as both a learning resource and a practical reference for building and deploying MCP servers in production environments.
