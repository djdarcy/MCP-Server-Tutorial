# Chapter 6: Authentication and Security

## Overview

This chapter covers MCP authentication mechanisms, security best practices, configuration management, and access control patterns for building secure MCP servers.

## MCP Authentication Fundamentals

### 1. Authentication Flow

MCP servers can implement various authentication mechanisms:

```python
# Authentication types in MCP
class AuthenticationType:
    NONE = "none"           # No authentication required
    API_KEY = "api_key"     # Simple API key authentication
    OAUTH2 = "oauth2"       # OAuth2 flow
    CUSTOM = "custom"       # Custom authentication scheme
```

### 2. Server Capabilities Declaration

```python
# server.py - Declare authentication capabilities
from mcp.server.models import InitializationOptions

class SecureMCPServer:
    def __init__(self):
        self.server = Server("secure-mcp-server")
        self.auth_enabled = os.getenv("MCP_AUTH_ENABLED", "false").lower() == "true"
        
        # Declare server capabilities
        self.capabilities = {
            "tools": {},
            "resources": {},
            "prompts": {},
            "experimental": {
                "authentication": {
                    "required": self.auth_enabled,
                    "types": ["api_key", "oauth2"]
                }
            }
        }
    
    async def handle_initialization(self, options: InitializationOptions):
        """Handle client initialization with authentication."""
        if self.auth_enabled:
            # Verify authentication credentials
            if not await self.authenticate_client(options):
                raise AuthenticationError("Authentication failed")
        
        return {
            "capabilities": self.capabilities,
            "serverInfo": {
                "name": "secure-mcp-server",
                "version": "1.0.0"
            }
        }
```

## API Key Authentication

### 1. API Key Configuration

```python
# auth.py - API key authentication implementation
import os
import hashlib
import hmac
import secrets
from typing import Optional, Dict, Any

class APIKeyAuth:
    """API key authentication for MCP servers."""
    
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.key_permissions = self._load_key_permissions()
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys from environment or configuration."""
        api_keys = {}
        
        # Load from environment variables
        if os.getenv("MCP_API_KEY"):
            api_keys["default"] = os.getenv("MCP_API_KEY")
        
        # Load from configuration file
        config_path = "config/api_keys.json"
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                api_keys.update(config.get("api_keys", {}))
        
        return api_keys
    
    def _load_key_permissions(self) -> Dict[str, List[str]]:
        """Load API key permissions."""
        return {
            "default": ["*"],  # Full access
            "readonly": ["get_*", "list_*"],  # Read-only tools
            "limited": ["hello_world", "echo"]  # Limited tool access
        }
    
    def generate_api_key(self, key_name: str, permissions: List[str] = None) -> str:
        """Generate a new API key."""
        api_key = secrets.token_urlsafe(32)
        
        # Store the key (in production, use secure storage)
        self.api_keys[key_name] = api_key
        
        if permissions:
            self.key_permissions[key_name] = permissions
        
        # Save to configuration
        self._save_api_keys()
        
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return key name."""
        for key_name, stored_key in self.api_keys.items():
            if hmac.compare_digest(api_key, stored_key):
                return key_name
        return None
    
    def check_tool_permission(self, key_name: str, tool_name: str) -> bool:
        """Check if API key has permission to use tool."""
        permissions = self.key_permissions.get(key_name, [])
        
        # Check for wildcard permission
        if "*" in permissions:
            return True
        
        # Check for exact tool name
        if tool_name in permissions:
            return True
        
        # Check for pattern matching
        for pattern in permissions:
            if pattern.endswith("*"):
                if tool_name.startswith(pattern[:-1]):
                    return True
        
        return False
    
    def _save_api_keys(self):
        """Save API keys to configuration file."""
        config = {
            "api_keys": self.api_keys,
            "key_permissions": self.key_permissions
        }
        
        os.makedirs("config", exist_ok=True)
        with open("config/api_keys.json", "w") as f:
            json.dump(config, f, indent=2)
```

### 2. Authentication Middleware

```python
# auth.py - Authentication middleware
class AuthenticationMiddleware:
    """Middleware for handling authentication."""
    
    def __init__(self, auth_handler: APIKeyAuth):
        self.auth_handler = auth_handler
        self.current_user = None
    
    async def authenticate_request(self, request: Dict[str, Any]) -> bool:
        """Authenticate an incoming request."""
        # Extract authentication header
        auth_header = request.get("auth", {})
        
        if not auth_header:
            # Check for API key in request params
            auth_header = request.get("params", {}).get("auth", {})
        
        if not auth_header:
            return False
        
        auth_type = auth_header.get("type")
        
        if auth_type == "api_key":
            api_key = auth_header.get("api_key")
            key_name = self.auth_handler.validate_api_key(api_key)
            
            if key_name:
                self.current_user = {
                    "key_name": key_name,
                    "auth_type": "api_key",
                    "authenticated_at": datetime.now().isoformat()
                }
                return True
        
        return False
    
    async def authorize_tool_call(self, tool_name: str) -> bool:
        """Authorize tool call for current user."""
        if not self.current_user:
            return False
        
        if self.current_user["auth_type"] == "api_key":
            return self.auth_handler.check_tool_permission(
                self.current_user["key_name"], 
                tool_name
            )
        
        return False
```

## OAuth2 Authentication

### 1. OAuth2 Configuration

```python
# oauth2.py - OAuth2 authentication
import requests
from urllib.parse import urlencode
from typing import Optional, Dict, Any

class OAuth2Auth:
    """OAuth2 authentication for MCP servers."""
    
    def __init__(self):
        self.client_id = os.getenv("OAUTH2_CLIENT_ID")
        self.client_secret = os.getenv("OAUTH2_CLIENT_SECRET")
        self.auth_server_url = os.getenv("OAUTH2_AUTH_SERVER", "https://auth.example.com")
        self.token_cache = {}
    
    def get_authorization_url(self, redirect_uri: str, state: str = None) -> str:
        """Generate OAuth2 authorization URL."""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": "mcp:server:access",
            "state": state or secrets.token_urlsafe(16)
        }
        
        return f"{self.auth_server_url}/oauth/authorize?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token."""
        token_url = f"{self.auth_server_url}/oauth/token"
        
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            
            # Cache the token
            self.token_cache[token_data["access_token"]] = {
                "token_data": token_data,
                "expires_at": time.time() + token_data.get("expires_in", 3600)
            }
            
            return token_data
            
        except requests.RequestException as e:
            logger.error(f"OAuth2 token exchange failed: {str(e)}")
            return None
    
    async def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Validate OAuth2 access token."""
        # Check cache first
        if access_token in self.token_cache:
            cached_token = self.token_cache[access_token]
            if time.time() < cached_token["expires_at"]:
                return cached_token["token_data"]
            else:
                # Token expired, remove from cache
                del self.token_cache[access_token]
        
        # Validate with auth server
        try:
            response = requests.get(
                f"{self.auth_server_url}/oauth/tokeninfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            
            token_info = response.json()
            
            # Cache the validated token
            self.token_cache[access_token] = {
                "token_data": token_info,
                "expires_at": time.time() + token_info.get("expires_in", 3600)
            }
            
            return token_info
            
        except requests.RequestException as e:
            logger.error(f"OAuth2 token validation failed: {str(e)}")
            return None
```

## Security Best Practices

### 1. Secure Configuration Management

```python
# config.py - Secure configuration management
import os
import json
from typing import Any, Dict, Optional
from cryptography.fernet import Fernet

class SecureConfig:
    """Secure configuration management for MCP servers."""
    
    def __init__(self):
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.config_path = "config/secure_config.json"
        self.config = self._load_config()
    
    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key."""
        key_path = "config/encryption.key"
        
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            os.makedirs("config", exist_ok=True)
            with open(key_path, "wb") as f:
                f.write(key)
            return key
    
    def _load_config(self) -> Dict[str, Any]:
        """Load encrypted configuration."""
        if not os.path.exists(self.config_path):
            return {}
        
        with open(self.config_path, "r") as f:
            encrypted_config = json.load(f)
        
        config = {}
        for key, encrypted_value in encrypted_config.items():
            if key.startswith("encrypted_"):
                # Decrypt sensitive values
                decrypted_value = self.cipher_suite.decrypt(
                    encrypted_value.encode()
                ).decode()
                config[key[10:]] = decrypted_value  # Remove "encrypted_" prefix
            else:
                config[key] = encrypted_value
        
        return config
    
    def set_sensitive_value(self, key: str, value: str):
        """Set sensitive configuration value with encryption."""
        encrypted_value = self.cipher_suite.encrypt(value.encode()).decode()
        self.config[key] = value
        
        # Save encrypted version
        self._save_config(key, encrypted_value)
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def _save_config(self, key: str, encrypted_value: str):
        """Save encrypted configuration."""
        # Load existing config
        encrypted_config = {}
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                encrypted_config = json.load(f)
        
        # Add encrypted value
        encrypted_config[f"encrypted_{key}"] = encrypted_value
        
        # Save to file
        os.makedirs("config", exist_ok=True)
        with open(self.config_path, "w") as f:
            json.dump(encrypted_config, f, indent=2)
```

### 2. Rate Limiting and Throttling

```python
# security.py - Rate limiting and security controls
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional

class RateLimiter:
    """Rate limiting for MCP server requests."""
    
    def __init__(self):
        self.request_counts = defaultdict(deque)
        self.limits = {
            "default": {"requests": 100, "window": 60},  # 100 requests per minute
            "api_key": {"requests": 1000, "window": 60}, # 1000 requests per minute
            "oauth2": {"requests": 500, "window": 60}    # 500 requests per minute
        }
    
    def is_allowed(self, client_id: str, auth_type: str = "default") -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        limit_config = self.limits.get(auth_type, self.limits["default"])
        
        # Clean old requests
        request_times = self.request_counts[client_id]
        while request_times and request_times[0] < now - limit_config["window"]:
            request_times.popleft()
        
        # Check if under limit
        if len(request_times) >= limit_config["requests"]:
            return False
        
        # Add current request
        request_times.append(now)
        return True
    
    def get_remaining_requests(self, client_id: str, auth_type: str = "default") -> int:
        """Get remaining requests in current window."""
        limit_config = self.limits.get(auth_type, self.limits["default"])
        used_requests = len(self.request_counts[client_id])
        return max(0, limit_config["requests"] - used_requests)

class SecurityValidator:
    """Security validation for MCP requests."""
    
    def __init__(self):
        self.blocked_ips = set()
        self.suspicious_patterns = [
            r"\.\.\/",  # Directory traversal
            r"<script",  # XSS attempts
            r"union.*select",  # SQL injection
            r"eval\(",  # Code injection
        ]
    
    def validate_request(self, request: Dict[str, Any], client_info: Dict[str, Any]) -> bool:
        """Validate request for security issues."""
        # Check blocked IPs
        client_ip = client_info.get("ip")
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked request from {client_ip}")
            return False
        
        # Check for suspicious patterns
        request_str = json.dumps(request)
        for pattern in self.suspicious_patterns:
            if re.search(pattern, request_str, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
        
        # Validate request size
        if len(request_str) > 1024 * 1024:  # 1MB limit
            logger.warning("Request too large")
            return False
        
        return True
    
    def block_ip(self, ip: str):
        """Block IP address."""
        self.blocked_ips.add(ip)
        logger.info(f"IP {ip} has been blocked")
```

## Secure Server Implementation

### 1. Authenticated Server Class

```python
# secure_server.py - Secure MCP server implementation
class SecureMCPServer:
    """Secure MCP server with authentication and authorization."""
    
    def __init__(self):
        self.server = Server("secure-mcp-server")
        self.auth_handler = APIKeyAuth()
        self.oauth2_handler = OAuth2Auth()
        self.rate_limiter = RateLimiter()
        self.security_validator = SecurityValidator()
        self.secure_config = SecureConfig()
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Set up secure request handlers."""
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, 
            arguments: Dict[str, Any]
        ) -> types.CallToolResult:
            """Handle tool calls with authentication and authorization."""
            
            # Get client context (this would be provided by MCP framework)
            client_info = self.get_client_info()
            
            # Validate request security
            if not self.security_validator.validate_request(
                {"tool": name, "arguments": arguments}, 
                client_info
            ):
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text="Security validation failed"
                    )],
                    isError=True
                )
            
            # Check rate limiting
            client_id = client_info.get("id", "unknown")
            if not self.rate_limiter.is_allowed(client_id):
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text="Rate limit exceeded"
                    )],
                    isError=True
                )
            
            # Authenticate request
            auth_result = await self.authenticate_request(client_info)
            if not auth_result:
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text="Authentication required"
                    )],
                    isError=True
                )
            
            # Authorize tool access
            if not await self.authorize_tool_call(name, auth_result):
                return types.CallToolResult(
                    content=[types.TextContent(
                        type="text",
                        text="Access denied"
                    )],
                    isError=True
                )
            
            # Execute tool
            return await self.execute_tool(name, arguments)
    
    async def authenticate_request(self, client_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate incoming request."""
        auth_header = client_info.get("auth", {})
        
        if not auth_header:
            return None
        
        auth_type = auth_header.get("type")
        
        if auth_type == "api_key":
            api_key = auth_header.get("api_key")
            key_name = self.auth_handler.validate_api_key(api_key)
            
            if key_name:
                return {
                    "key_name": key_name,
                    "auth_type": "api_key",
                    "authenticated_at": datetime.now().isoformat()
                }
        
        elif auth_type == "oauth2":
            access_token = auth_header.get("access_token")
            token_info = await self.oauth2_handler.validate_token(access_token)
            
            if token_info:
                return {
                    "token_info": token_info,
                    "auth_type": "oauth2",
                    "authenticated_at": datetime.now().isoformat()
                }
        
        return None
    
    async def authorize_tool_call(self, tool_name: str, auth_result: Dict[str, Any]) -> bool:
        """Authorize tool call for authenticated user."""
        if auth_result["auth_type"] == "api_key":
            return self.auth_handler.check_tool_permission(
                auth_result["key_name"], 
                tool_name
            )
        
        elif auth_result["auth_type"] == "oauth2":
            # Check OAuth2 scopes
            token_info = auth_result["token_info"]
            scopes = token_info.get("scope", "").split()
            
            # Check if user has required scope for tool
            required_scope = f"mcp:tool:{tool_name}"
            return required_scope in scopes or "mcp:tool:*" in scopes
        
        return False
```

## Configuration Examples

### 1. Secure Claude Desktop Configuration

```json
{
  "mcpServers": {
    "secure-mcp-server": {
      "command": "python",
      "args": ["secure_server.py"],
      "env": {
        "MCP_AUTH_ENABLED": "true",
        "MCP_API_KEY": "your-secure-api-key-here",
        "MCP_DEBUG": "false"
      }
    }
  }
}
```

### 2. API Key Configuration

```json
{
  "api_keys": {
    "production": "sk-prod-1234567890abcdef",
    "development": "sk-dev-abcdef1234567890",
    "readonly": "sk-ro-fedcba0987654321"
  },
  "key_permissions": {
    "production": ["*"],
    "development": ["hello_world", "echo", "get_time", "debug_info"],
    "readonly": ["get_*", "list_*", "debug_info"]
  }
}
```

## Security Testing

### 1. Authentication Tests

```python
# tests/test_security.py - Security testing
import pytest
from secure_server import SecureMCPServer
from auth import APIKeyAuth

class TestAuthentication:
    """Test authentication mechanisms."""
    
    def setup_method(self):
        self.server = SecureMCPServer()
        self.auth_handler = APIKeyAuth()
    
    def test_api_key_validation(self):
        """Test API key validation."""
        # Generate test API key
        api_key = self.auth_handler.generate_api_key("test", ["hello_world"])
        
        # Test valid key
        key_name = self.auth_handler.validate_api_key(api_key)
        assert key_name == "test"
        
        # Test invalid key
        invalid_key = self.auth_handler.validate_api_key("invalid-key")
        assert invalid_key is None
    
    def test_tool_permissions(self):
        """Test tool permission checking."""
        # Generate limited API key
        api_key = self.auth_handler.generate_api_key("limited", ["hello_world"])
        
        # Test allowed tool
        assert self.auth_handler.check_tool_permission("limited", "hello_world") is True
        
        # Test denied tool
        assert self.auth_handler.check_tool_permission("limited", "debug_info") is False
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from security import RateLimiter
        
        rate_limiter = RateLimiter()
        
        # Test normal usage
        for i in range(50):
            assert rate_limiter.is_allowed("test_client") is True
        
        # Test rate limit exceeded
        rate_limiter.limits["default"]["requests"] = 10
        
        for i in range(5):
            assert rate_limiter.is_allowed("test_client2") is True
        
        # Should be blocked after limit
        assert rate_limiter.is_allowed("test_client2") is False
```

## Summary

This chapter covered:

1. **Authentication Mechanisms**: API key and OAuth2 authentication implementation
2. **Security Configuration**: Secure configuration management and encryption
3. **Access Control**: Permission-based tool access and authorization
4. **Rate Limiting**: Request throttling and abuse prevention
5. **Security Validation**: Input validation and security pattern detection
6. **Secure Server**: Complete secure server implementation
7. **Testing**: Comprehensive security testing approach

The security implementation provides multiple layers of protection while maintaining usability and flexibility for different deployment scenarios.

## Next Steps

- **Chapter 7**: State Management - Handle server state and resources
- **Chapter 8**: Claude Integration - Deep dive into Claude Desktop integration
- **Chapter 9**: Production Deployment - Production-ready deployment strategies
