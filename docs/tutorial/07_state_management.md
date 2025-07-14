# Chapter 7: State Management

## Overview

This chapter covers server state management patterns, resource handling, caching strategies, and performance optimization techniques for MCP servers that need to maintain state between requests.

## State Management Fundamentals

### 1. Stateless vs Stateful MCP Servers

```python
# Basic stateless server (our simple example)
class StatelessMCPServer:
    """Stateless MCP server - each request is independent."""
    
    def __init__(self):
        self.server = Server("stateless-mcp-server")
        # No persistent state between requests
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]):
        """Each tool call is independent."""
        # Process request without relying on previous state
        result = await self.execute_tool(name, arguments)
        return result

# Stateful server with session management
class StatefulMCPServer:
    """Stateful MCP server - maintains state between requests."""
    
    def __init__(self):
        self.server = Server("stateful-mcp-server")
        self.session_manager = SessionManager()
        self.cache = CacheManager()
        self.resource_manager = ResourceManager()
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any], session_id: str):
        """Tool calls can access and modify session state."""
        session = self.session_manager.get_session(session_id)
        
        # Process request with access to session state
        result = await self.execute_tool(name, arguments, session)
        
        # Update session state if needed
        self.session_manager.update_session(session_id, session)
        
        return result
```

### 2. Session Management

```python
# session.py - Session management for stateful MCP servers
import uuid
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class Session:
    """Represents a client session."""
    id: str
    created_at: datetime
    last_accessed: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    client_info: Dict[str, Any] = field(default_factory=dict)
    
    def touch(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session is expired."""
        return datetime.now() - self.last_accessed > timedelta(minutes=timeout_minutes)

class SessionManager:
    """Manages client sessions for stateful MCP servers."""
    
    def __init__(self, session_timeout: int = 30):
        self.sessions: Dict[str, Session] = {}
        self.session_timeout = session_timeout
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def create_session(self, client_info: Dict[str, Any] = None) -> str:
        """Create a new session."""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = Session(
            id=session_id,
            created_at=now,
            last_accessed=now,
            client_info=client_info or {}
        )
        
        self.sessions[session_id] = session
        self._cleanup_expired_sessions()
        
        logger.info(f"Created session {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        session = self.sessions.get(session_id)
        
        if session:
            if session.is_expired(self.session_timeout):
                self.delete_session(session_id)
                return None
            
            session.touch()
            return session
        
        return None
    
    def update_session(self, session_id: str, session: Session):
        """Update session data."""
        if session_id in self.sessions:
            self.sessions[session_id] = session
            session.touch()
    
    def delete_session(self, session_id: str):
        """Delete a session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session {session_id}")
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        if time.time() - self.last_cleanup < self.cleanup_interval:
            return
        
        expired_sessions = [
            session_id for session_id, session in self.sessions.items()
            if session.is_expired(self.session_timeout)
        ]
        
        for session_id in expired_sessions:
            self.delete_session(session_id)
        
        self.last_cleanup = time.time()
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_active_sessions(self) -> List[Session]:
        """Get all active sessions."""
        self._cleanup_expired_sessions()
        return list(self.sessions.values())
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        self._cleanup_expired_sessions()
        
        return {
            "total_sessions": len(self.sessions),
            "oldest_session": min(
                (s.created_at for s in self.sessions.values()),
                default=None
            ),
            "most_recent_access": max(
                (s.last_accessed for s in self.sessions.values()),
                default=None
            )
        }
```

## Resource Management

### 1. Resource Lifecycle Management

```python
# resources.py - Resource management for MCP servers
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, AsyncGenerator
import asyncio
import weakref

class ManagedResource(ABC):
    """Base class for managed resources."""
    
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.reference_count = 0
        
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the resource."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up the resource."""
        pass
    
    def touch(self):
        """Update last accessed time."""
        self.last_accessed = datetime.now()
    
    def add_reference(self):
        """Add a reference to this resource."""
        self.reference_count += 1
    
    def remove_reference(self):
        """Remove a reference from this resource."""
        self.reference_count = max(0, self.reference_count - 1)
    
    def is_idle(self, idle_timeout: int = 300) -> bool:
        """Check if resource is idle."""
        return (
            self.reference_count == 0 and
            (datetime.now() - self.last_accessed).total_seconds() > idle_timeout
        )

class DatabaseConnection(ManagedResource):
    """Example managed database connection."""
    
    def __init__(self, resource_id: str, connection_string: str):
        super().__init__(resource_id)
        self.connection_string = connection_string
        self.connection = None
    
    async def initialize(self) -> bool:
        """Initialize database connection."""
        try:
            # Simulate database connection
            await asyncio.sleep(0.1)
            self.connection = f"Connected to {self.connection_string}"
            logger.info(f"Database connection {self.resource_id} initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up database connection."""
        if self.connection:
            # Simulate connection cleanup
            await asyncio.sleep(0.05)
            self.connection = None
            logger.info(f"Database connection {self.resource_id} cleaned up")

class FileHandle(ManagedResource):
    """Example managed file handle."""
    
    def __init__(self, resource_id: str, file_path: str, mode: str = "r"):
        super().__init__(resource_id)
        self.file_path = file_path
        self.mode = mode
        self.file_handle = None
    
    async def initialize(self) -> bool:
        """Initialize file handle."""
        try:
            self.file_handle = open(self.file_path, self.mode)
            logger.info(f"File handle {self.resource_id} initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize file handle: {str(e)}")
            return False
    
    async def cleanup(self):
        """Clean up file handle."""
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
            logger.info(f"File handle {self.resource_id} cleaned up")

class ResourceManager:
    """Manages server resources with lifecycle and cleanup."""
    
    def __init__(self):
        self.resources: Dict[str, ManagedResource] = {}
        self.resource_factories: Dict[str, callable] = {}
        self.cleanup_task = None
        self.cleanup_interval = 60  # 1 minute
        
    def register_resource_factory(self, resource_type: str, factory: callable):
        """Register a resource factory."""
        self.resource_factories[resource_type] = factory
    
    async def get_resource(self, resource_type: str, resource_id: str, **kwargs) -> Optional[ManagedResource]:
        """Get or create a resource."""
        full_id = f"{resource_type}:{resource_id}"
        
        # Check if resource already exists
        if full_id in self.resources:
            resource = self.resources[full_id]
            resource.add_reference()
            resource.touch()
            return resource
        
        # Create new resource
        factory = self.resource_factories.get(resource_type)
        if not factory:
            logger.error(f"No factory registered for resource type: {resource_type}")
            return None
        
        resource = factory(resource_id, **kwargs)
        
        # Initialize resource
        if await resource.initialize():
            self.resources[full_id] = resource
            resource.add_reference()
            self.start_cleanup_task()
            return resource
        else:
            logger.error(f"Failed to initialize resource {full_id}")
            return None
    
    async def release_resource(self, resource_type: str, resource_id: str):
        """Release a resource reference."""
        full_id = f"{resource_type}:{resource_id}"
        
        if full_id in self.resources:
            resource = self.resources[full_id]
            resource.remove_reference()
    
    @asynccontextmanager
    async def use_resource(self, resource_type: str, resource_id: str, **kwargs) -> AsyncGenerator[ManagedResource, None]:
        """Context manager for using resources."""
        resource = await self.get_resource(resource_type, resource_id, **kwargs)
        
        if resource:
            try:
                yield resource
            finally:
                await self.release_resource(resource_type, resource_id)
        else:
            yield None
    
    async def cleanup_idle_resources(self):
        """Clean up idle resources."""
        idle_resources = [
            (resource_id, resource) for resource_id, resource in self.resources.items()
            if resource.is_idle()
        ]
        
        for resource_id, resource in idle_resources:
            await resource.cleanup()
            del self.resources[resource_id]
            logger.info(f"Cleaned up idle resource {resource_id}")
    
    def start_cleanup_task(self):
        """Start background cleanup task."""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Background cleanup loop."""
        while self.resources:
            await asyncio.sleep(self.cleanup_interval)
            await self.cleanup_idle_resources()
    
    async def shutdown(self):
        """Shutdown resource manager and clean up all resources."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Clean up all resources
        for resource_id, resource in self.resources.items():
            await resource.cleanup()
        
        self.resources.clear()
        logger.info("Resource manager shutdown complete")
```

## Caching Strategies

### 1. Multi-Level Caching

```python
# cache.py - Caching strategies for MCP servers
from typing import Any, Optional, Dict, List
import time
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

class CacheLevel(Enum):
    MEMORY = "memory"
    DISK = "disk"
    REDIS = "redis"

@dataclass
class CacheEntry:
    """Represents a cache entry."""
    key: str
    value: Any
    created_at: float
    expires_at: Optional[float] = None
    access_count: int = 0
    last_accessed: float = 0
    size: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()

class MemoryCache:
    """In-memory cache with LRU eviction."""
    
    def __init__(self, max_size: int = 1000, max_memory: int = 100 * 1024 * 1024):  # 100MB
        self.max_size = max_size
        self.max_memory = max_memory
        self.cache: Dict[str, CacheEntry] = {}
        self.access_order: List[str] = []
        self.current_memory = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # Check if expired
        if entry.is_expired():
            self.delete(key)
            return None
        
        # Update access statistics
        entry.touch()
        
        # Update LRU order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        # Calculate entry size
        entry_size = len(json.dumps(value, default=str))
        
        # Create cache entry
        entry = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            expires_at=time.time() + ttl if ttl else None,
            size=entry_size
        )
        
        # Remove existing entry if present
        if key in self.cache:
            self.delete(key)
        
        # Check if we need to evict entries
        self._evict_if_needed(entry_size)
        
        # Add new entry
        self.cache[key] = entry
        self.access_order.append(key)
        self.current_memory += entry_size
    
    def delete(self, key: str):
        """Delete entry from cache."""
        if key in self.cache:
            entry = self.cache[key]
            del self.cache[key]
            self.current_memory -= entry.size
            
            if key in self.access_order:
                self.access_order.remove(key)
    
    def _evict_if_needed(self, new_entry_size: int):
        """Evict entries if needed to make room."""
        # Check size limit
        while len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Check memory limit
        while self.current_memory + new_entry_size > self.max_memory:
            self._evict_lru()
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if self.access_order:
            lru_key = self.access_order[0]
            self.delete(lru_key)
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.access_order.clear()
        self.current_memory = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "entries": len(self.cache),
            "memory_usage": self.current_memory,
            "memory_limit": self.max_memory,
            "size_limit": self.max_size,
            "hit_rate": self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        if total_accesses == 0:
            return 0.0
        
        # This is a simplified calculation
        # In practice, you'd track hits and misses separately
        return min(1.0, total_accesses / max(1, len(self.cache)))

class CacheManager:
    """Multi-level cache manager."""
    
    def __init__(self):
        self.memory_cache = MemoryCache()
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first)."""
        # Try memory cache first
        value = self.memory_cache.get(key)
        
        if value is not None:
            self.cache_stats["hits"] += 1
            return value
        
        # Could add disk cache, Redis, etc. here
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        self.memory_cache.set(key, value, ttl)
        self.cache_stats["sets"] += 1
    
    def delete(self, key: str):
        """Delete value from cache."""
        self.memory_cache.delete(key)
        self.cache_stats["deletes"] += 1
    
    def clear(self):
        """Clear all caches."""
        self.memory_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_stats = self.memory_cache.get_stats()
        
        return {
            "memory_cache": memory_stats,
            "operations": self.cache_stats,
            "hit_rate": self._calculate_hit_rate()
        }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate overall hit rate."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        if total_requests == 0:
            return 0.0
        
        return self.cache_stats["hits"] / total_requests
```

## Stateful Tool Implementation

### 1. Counter Tool with State

```python
# stateful_tools.py - Tools that maintain state between calls
class CounterTool:
    """Tool that maintains a counter state."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    async def handle_counter(self, arguments: Dict[str, Any], session_id: str) -> types.CallToolResult:
        """Handle counter operations."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text="Session not found. Please start a new session."
                )],
                isError=True
            )
        
        operation = arguments.get("operation", "get")
        
        # Initialize counter if not exists
        if "counter" not in session.data:
            session.data["counter"] = 0
        
        if operation == "get":
            value = session.data["counter"]
            
        elif operation == "increment":
            step = arguments.get("step", 1)
            session.data["counter"] += step
            value = session.data["counter"]
            
        elif operation == "decrement":
            step = arguments.get("step", 1)
            session.data["counter"] -= step
            value = session.data["counter"]
            
        elif operation == "reset":
            session.data["counter"] = 0
            value = session.data["counter"]
            
        else:
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text=f"Unknown operation: {operation}"
                )],
                isError=True
            )
        
        # Update session
        self.session_manager.update_session(session_id, session)
        
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Counter {operation}: {value}"
            )]
        )

class HistoryTool:
    """Tool that maintains command history."""
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
    
    async def handle_history(self, arguments: Dict[str, Any], session_id: str) -> types.CallToolResult:
        """Handle history operations."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text="Session not found. Please start a new session."
                )],
                isError=True
            )
        
        operation = arguments.get("operation", "list")
        
        # Initialize history if not exists
        if "history" not in session.data:
            session.data["history"] = []
        
        if operation == "list":
            history = session.data["history"]
            if not history:
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text="No history available"
                    )]
                )
            
            history_text = "\n".join([
                f"{i+1}. {entry}" for i, entry in enumerate(history)
            ])
            
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text=f"Command History:\n{history_text}"
                )]
            )
        
        elif operation == "add":
            command = arguments.get("command")
            if not command:
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text="Command is required for add operation"
                    )],
                    isError=True
                )
            
            session.data["history"].append(command)
            
            # Keep only last 20 commands
            if len(session.data["history"]) > 20:
                session.data["history"] = session.data["history"][-20:]
            
            self.session_manager.update_session(session_id, session)
            
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text=f"Added to history: {command}"
                )]
            )
        
        elif operation == "clear":
            session.data["history"] = []
            self.session_manager.update_session(session_id, session)
            
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text="History cleared"
                )]
            )
        
        else:
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text=f"Unknown operation: {operation}"
                )],
                isError=True
            )
```

## Performance Optimization

### 1. Async Processing and Queues

```python
# performance.py - Performance optimization for MCP servers
import asyncio
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from queue import Queue
import time

@dataclass
class TaskResult:
    """Result of an async task."""
    task_id: str
    result: Any
    error: Optional[Exception] = None
    completed_at: float = 0

class AsyncTaskManager:
    """Manages async tasks for performance optimization."""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_results: Dict[str, TaskResult] = {}
        self.task_queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.running = False
    
    async def start(self):
        """Start the task manager."""
        self.running = True
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
    
    async def stop(self):
        """Stop the task manager."""
        self.running = False
        
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        
        # Cancel any remaining tasks
        for task in self.active_tasks.values():
            task.cancel()
    
    async def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> str:
        """Submit a task for async execution."""
        await self.task_queue.put((task_id, func, args, kwargs))
        return task_id
    
    async def get_result(self, task_id: str, timeout: Optional[float] = None) -> TaskResult:
        """Get result of a task."""
        start_time = time.time()
        
        while True:
            if task_id in self.task_results:
                return self.task_results[task_id]
            
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError(f"Task {task_id} timed out")
            
            await asyncio.sleep(0.1)
    
    async def _worker(self, worker_id: str):
        """Worker task that processes the queue."""
        while self.running:
            try:
                task_id, func, args, kwargs = await asyncio.wait_for(
                    self.task_queue.get(), 
                    timeout=1.0
                )
                
                # Execute the task
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    # Store result
                    self.task_results[task_id] = TaskResult(
                        task_id=task_id,
                        result=result,
                        completed_at=time.time()
                    )
                    
                except Exception as e:
                    # Store error
                    self.task_results[task_id] = TaskResult(
                        task_id=task_id,
                        result=None,
                        error=e,
                        completed_at=time.time()
                    )
                
                # Mark task as done
                self.task_queue.task_done()
                
            except asyncio.TimeoutError:
                # Queue timeout - continue
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {str(e)}")
```

### 2. Connection Pooling

```python
# connection_pool.py - Connection pooling for external services
class ConnectionPool:
    """Generic connection pool for external services."""
    
    def __init__(self, factory: Callable, max_connections: int = 10):
        self.factory = factory
        self.max_connections = max_connections
        self.available_connections = asyncio.Queue(maxsize=max_connections)
        self.total_connections = 0
        self.stats = {
            "created": 0,
            "borrowed": 0,
            "returned": 0,
            "errors": 0
        }
    
    async def get_connection(self):
        """Get a connection from the pool."""
        try:
            # Try to get an existing connection
            connection = self.available_connections.get_nowait()
            self.stats["borrowed"] += 1
            return connection
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if self.total_connections < self.max_connections:
                connection = await self.factory()
                self.total_connections += 1
                self.stats["created"] += 1
                self.stats["borrowed"] += 1
                return connection
            else:
                # Wait for available connection
                connection = await self.available_connections.get()
                self.stats["borrowed"] += 1
                return connection
    
    async def return_connection(self, connection):
        """Return a connection to the pool."""
        try:
            self.available_connections.put_nowait(connection)
            self.stats["returned"] += 1
        except asyncio.QueueFull:
            # Pool is full, close the connection
            await self._close_connection(connection)
            self.total_connections -= 1
    
    async def _close_connection(self, connection):
        """Close a connection."""
        try:
            if hasattr(connection, 'close'):
                await connection.close()
        except Exception as e:
            logger.error(f"Error closing connection: {str(e)}")
    
    async def close_all(self):
        """Close all connections in the pool."""
        while not self.available_connections.empty():
            connection = await self.available_connections.get()
            await self._close_connection(connection)
        
        self.total_connections = 0
```

## Complete Stateful Server Example

```python
# stateful_server.py - Complete stateful MCP server implementation
class StatefulMCPServer:
    """Complete stateful MCP server with state management."""
    
    def __init__(self):
        self.server = Server("stateful-mcp-server")
        self.session_manager = SessionManager()
        self.resource_manager = ResourceManager()
        self.cache_manager = CacheManager()
        self.task_manager = AsyncTaskManager()
        
        # Register resource factories
        self.resource_manager.register_resource_factory(
            "database", 
            lambda resource_id, connection_string: DatabaseConnection(resource_id, connection_string)
        )
        self.resource_manager.register_resource_factory(
            "file",
            lambda resource_id, file_path, mode="r": FileHandle(resource_id, file_path, mode)
        )
        
        # Initialize stateful tools
        self.counter_tool = CounterTool(self.session_manager)
        self.history_tool = HistoryTool(self.session_manager)
        
        self.setup_handlers()
    
    async def start(self):
        """Start the server and all components."""
        await self.task_manager.start()
        logger.info("Stateful MCP server started")
    
    async def stop(self):
        """Stop the server and clean up resources."""
        await self.task_manager.stop()
        await self.resource_manager.shutdown()
        logger.info("Stateful MCP server stopped")
    
    def setup_handlers(self):
        """Set up stateful request handlers."""
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Dict[str, Any]
        ) -> types.CallToolResult:
            """Handle tool calls with state management."""
            
            # Get or create session
            session_id = arguments.get("session_id")
            if not session_id:
                session_id = self.session_manager.create_session()
                # In a real implementation, this would be handled by the client
            
            # Handle stateful tools
            if name == "counter":
                return await self.counter_tool.handle_counter(arguments, session_id)
            elif name == "history":
                return await self.history_tool.handle_history(arguments, session_id)
            elif name == "session_info":
                return await self.handle_session_info(arguments, session_id)
            elif name == "cache_stats":
                return await self.handle_cache_stats(arguments)
            elif name == "resource_stats":
                return await self.handle_resource_stats(arguments)
            else:
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )],
                    isError=True
                )
    
    async def handle_session_info(self, arguments: Dict[str, Any], session_id: str) -> types.CallToolResult:
        """Handle session info requests."""
        session = self.session_manager.get_session(session_id)
        if not session:
            return types.CallToolResult(
                content=[types.TextContent(
                    type="text",
                    text="Session not found"
                )],
                isError=True
            )
        
        info = {
            "session_id": session.id,
            "created_at": session.created_at.isoformat(),
            "last_accessed": session.last_accessed.isoformat(),
            "data_keys": list(session.data.keys())
        }
        
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Session Info:\n{json.dumps(info, indent=2)}"
            )]
        )
    
    async def handle_cache_stats(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """Handle cache statistics requests."""
        stats = self.cache_manager.get_stats()
        
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Cache Statistics:\n{json.dumps(stats, indent=2)}"
            )]
        )
    
    async def handle_resource_stats(self, arguments: Dict[str, Any]) -> types.CallToolResult:
        """Handle resource statistics requests."""
        stats = {
            "active_resources": len(self.resource_manager.resources),
            "resource_types": list(set(
                r.split(":")[0] for r in self.resource_manager.resources.keys()
            ))
        }
        
        return types.CallToolResult(
            content=[types.TextContent(
                type="text",
                text=f"Resource Statistics:\n{json.dumps(stats, indent=2)}"
            )]
        )

# Example usage
async def main():
    server = StatefulMCPServer()
    await server.start()
    
    try:
        # Run the server
        await server.server.run()
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Testing State Management

```python
# tests/test_state_management.py - Tests for state management
import pytest
from session import SessionManager, Session
from cache import CacheManager
from resources import ResourceManager, DatabaseConnection

class TestSessionManager:
    """Test session management functionality."""
    
    def setup_method(self):
        self.session_manager = SessionManager(session_timeout=1)  # 1 minute timeout
    
    def test_create_session(self):
        """Test session creation."""
        session_id = self.session_manager.create_session()
        assert session_id
        assert len(session_id) > 0
        
        session = self.session_manager.get_session(session_id)
        assert session is not None
        assert session.id == session_id
    
    def test_session_expiry(self):
        """Test session expiry."""
        import time
        
        # Create session with very short timeout
        session_manager = SessionManager(session_timeout=0.01)  # 0.6 seconds
        session_id = session_manager.create_session()
        
        # Wait for expiry
        time.sleep(0.02)
        
        # Session should be expired
        session = session_manager.get_session(session_id)
        assert session is None
    
    def test_session_data_persistence(self):
        """Test session data persistence."""
        session_id = self.session_manager.create_session()
        session = self.session_manager.get_session(session_id)
        
        # Add data to session
        session.data["test_key"] = "test_value"
        self.session_manager.update_session(session_id, session)
        
        # Retrieve session and check data
        retrieved_session = self.session_manager.get_session(session_id)
        assert retrieved_session.data["test_key"] == "test_value"

class TestCacheManager:
    """Test cache management functionality."""
    
    def setup_method(self):
        self.cache_manager = CacheManager()
    
    def test_cache_set_get(self):
        """Test basic cache operations."""
        self.cache_manager.set("test_key", "test_value")
        value = self.cache_manager.get("test_key")
        assert value == "test_value"
    
    def test_cache_expiry(self):
        """Test cache expiry."""
        import time
        
        self.cache_manager.set("test_key", "test_value", ttl=1)
        
        # Should be available immediately
        value = self.cache_manager.get("test_key")
        assert value == "test_value"
        
        # Wait for expiry
        time.sleep(1.1)
        
        # Should be expired
        value = self.cache_manager.get("test_key")
        assert value is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        self.cache_manager.set("key1", "value1")
        self.cache_manager.get("key1")
        self.cache_manager.get("nonexistent")
        
        stats = self.cache_manager.get_stats()
        assert stats["operations"]["hits"] == 1
        assert stats["operations"]["misses"] == 1
        assert stats["operations"]["sets"] == 1
```

## Summary

This chapter covered:

1. **State Management**: Session management and stateful vs stateless servers
2. **Resource Management**: Lifecycle management and resource pooling
3. **Caching Strategies**: Multi-level caching with TTL and LRU eviction
4. **Performance Optimization**: Async processing, connection pooling, and task management
5. **Stateful Tools**: Implementation of tools that maintain state between calls
6. **Complete Implementation**: Full stateful server with all components integrated
7. **Testing**: Comprehensive testing for state management components

The state management system provides a robust foundation for building complex MCP servers that need to maintain context and optimize performance across multiple client interactions.

## Next Steps

- **Chapter 8**: Claude Integration - Deep dive into Claude Desktop integration
- **Chapter 9**: Production Deployment - Production-ready deployment strategies
