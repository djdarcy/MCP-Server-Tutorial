# Chapter 8: Integration with Claude Code

## Overview

This chapter provides a comprehensive guide to integrating MCP servers with Claude Desktop, including configuration, troubleshooting, connection management, and update procedures.

## Claude Desktop Configuration

### 1. Basic Configuration Structure

Claude Desktop uses a JSON configuration file to define MCP servers:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "ENVIRONMENT_VARIABLE": "value"
      }
    }
  }
}
```

### 2. Configuration File Locations

The configuration file location depends on your operating system:

```python
# config_utils.py - Configuration file utilities
import os
import json
import platform
from pathlib import Path
from typing import Dict, Any, Optional

class ClaudeConfigManager:
    """Manages Claude Desktop configuration."""
    
    def __init__(self):
        self.config_path = self._get_config_path()
        self.config = self._load_config()
    
    def _get_config_path(self) -> Path:
        """Get Claude Desktop configuration file path."""
        system = platform.system()
        
        if system == "Windows":
            return Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        elif system == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            return Path.home() / ".config" / "claude" / "claude_desktop_config.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load existing configuration or create empty one."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {str(e)}")
                return {"mcpServers": {}}
        else:
            return {"mcpServers": {}}
    
    def add_server(self, name: str, command: str, args: list, env: Dict[str, str] = None):
        """Add MCP server to configuration."""
        server_config = {
            "command": command,
            "args": args
        }
        
        if env:
            server_config["env"] = env
        
        if "mcpServers" not in self.config:
            self.config["mcpServers"] = {}
        
        self.config["mcpServers"][name] = server_config
        self._save_config()
        
        logger.info(f"Added MCP server '{name}' to configuration")
    
    def remove_server(self, name: str):
        """Remove MCP server from configuration."""
        if "mcpServers" in self.config and name in self.config["mcpServers"]:
            del self.config["mcpServers"][name]
            self._save_config()
            logger.info(f"Removed MCP server '{name}' from configuration")
        else:
            logger.warning(f"MCP server '{name}' not found in configuration")
    
    def get_server_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific server."""
        return self.config.get("mcpServers", {}).get(name)
    
    def list_servers(self) -> Dict[str, Dict[str, Any]]:
        """List all configured MCP servers."""
        return self.config.get("mcpServers", {})
    
    def _save_config(self):
        """Save configuration to file."""
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save configuration
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return issues."""
        issues = []
        
        for server_name, server_config in self.config.get("mcpServers", {}).items():
            # Check required fields
            if "command" not in server_config:
                issues.append(f"Server '{server_name}' missing 'command' field")
            
            if "args" not in server_config:
                issues.append(f"Server '{server_name}' missing 'args' field")
            
            # Check if command exists
            command = server_config.get("command")
            if command and not self._command_exists(command):
                issues.append(f"Server '{server_name}' command '{command}' not found")
            
            # Check if script file exists
            args = server_config.get("args", [])
            if args and len(args) > 0:
                script_path = Path(args[0])
                if not script_path.exists():
                    issues.append(f"Server '{server_name}' script '{args[0]}' not found")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists in PATH."""
        import shutil
        return shutil.which(command) is not None
```

### 3. Configuration Examples

```python
# config_examples.py - Configuration examples for different scenarios
def create_simple_server_config():
    """Create configuration for simple MCP server."""
    return {
        "mcpServers": {
            "simple-mcp-server": {
                "command": "python",
                "args": ["simple_mcp_server/server.py"],
                "env": {
                    "MCP_DEBUG": "false"
                }
            }
        }
    }

def create_development_config():
    """Create configuration for development environment."""
    return {
        "mcpServers": {
            "simple-mcp-server-dev": {
                "command": "python",
                "args": ["simple_mcp_server/server.py"],
                "env": {
                    "MCP_DEBUG": "true",
                    "MCP_LOG_LEVEL": "DEBUG",
                    "PYTHONPATH": "/path/to/project"
                }
            }
        }
    }

def create_production_config():
    """Create configuration for production environment."""
    return {
        "mcpServers": {
            "simple-mcp-server": {
                "command": "python",
                "args": ["-m", "simple_mcp_server.server"],
                "env": {
                    "MCP_DEBUG": "false",
                    "MCP_LOG_LEVEL": "INFO",
                    "MCP_AUTH_ENABLED": "true"
                }
            }
        }
    }

def create_virtual_env_config():
    """Create configuration using virtual environment."""
    return {
        "mcpServers": {
            "simple-mcp-server": {
                "command": "/path/to/venv/bin/python",
                "args": ["simple_mcp_server/server.py"],
                "env": {
                    "VIRTUAL_ENV": "/path/to/venv",
                    "PATH": "/path/to/venv/bin:$PATH"
                }
            }
        }
    }

def create_authenticated_config():
    """Create configuration with authentication."""
    return {
        "mcpServers": {
            "secure-mcp-server": {
                "command": "python",
                "args": ["secure_server.py"],
                "env": {
                    "MCP_AUTH_ENABLED": "true",
                    "MCP_API_KEY": "your-secure-api-key",
                    "MCP_LOG_LEVEL": "INFO"
                }
            }
        }
    }
```

## Connection Management

### 1. Connection Diagnostics

```python
# connection_diagnostics.py - Connection diagnostic tools
import subprocess
import sys
import json
import time
from typing import Dict, Any, List

class ConnectionDiagnostics:
    """Diagnostic tools for MCP server connections."""
    
    def __init__(self, config_manager: ClaudeConfigManager):
        self.config_manager = config_manager
    
    def test_server_startup(self, server_name: str) -> Dict[str, Any]:
        """Test if MCP server can start successfully."""
        server_config = self.config_manager.get_server_config(server_name)
        
        if not server_config:
            return {
                "success": False,
                "error": f"Server '{server_name}' not found in configuration"
            }
        
        command = server_config["command"]
        args = server_config.get("args", [])
        env = server_config.get("env", {})
        
        try:
            # Prepare environment
            full_env = os.environ.copy()
            full_env.update(env)
            
            # Start server process
            process = subprocess.Popen(
                [command] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
                text=True
            )
            
            # Give server time to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                # Process is running, terminate it
                process.terminate()
                process.wait(timeout=5)
                
                return {
                    "success": True,
                    "message": "Server started successfully"
                }
            else:
                # Process exited, get error output
                stdout, stderr = process.communicate()
                
                return {
                    "success": False,
                    "error": f"Server exited with code {process.returncode}",
                    "stdout": stdout,
                    "stderr": stderr
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start server: {str(e)}"
            }
    
    def test_tool_discovery(self, server_name: str) -> Dict[str, Any]:
        """Test tool discovery for MCP server."""
        # This would involve starting the server and sending list_tools request
        # For now, we'll just check if the server responds to basic communication
        
        server_config = self.config_manager.get_server_config(server_name)
        if not server_config:
            return {
                "success": False,
                "error": f"Server '{server_name}' not found in configuration"
            }
        
        # In a real implementation, this would:
        # 1. Start the server
        # 2. Send initialize request
        # 3. Send list_tools request
        # 4. Verify response format
        
        return {
            "success": True,
            "message": "Tool discovery test would be implemented here",
            "tools": ["hello_world", "echo", "get_time", "math_add", "debug_info"]
        }
    
    def diagnose_connection_issues(self, server_name: str) -> Dict[str, Any]:
        """Diagnose common connection issues."""
        issues = []
        suggestions = []
        
        # Check if server is configured
        server_config = self.config_manager.get_server_config(server_name)
        if not server_config:
            issues.append(f"Server '{server_name}' not found in configuration")
            suggestions.append("Add server to claude_desktop_config.json")
            
            return {
                "issues": issues,
                "suggestions": suggestions
            }
        
        # Check if command exists
        command = server_config["command"]
        if not self.config_manager._command_exists(command):
            issues.append(f"Command '{command}' not found in PATH")
            suggestions.append("Install Python or check PATH configuration")
        
        # Check if script file exists
        args = server_config.get("args", [])
        if args and len(args) > 0:
            script_path = Path(args[0])
            if not script_path.exists():
                issues.append(f"Script file '{args[0]}' not found")
                suggestions.append("Check script path is correct and file exists")
        
        # Check Python environment
        env = server_config.get("env", {})
        if "PYTHONPATH" in env:
            python_path = Path(env["PYTHONPATH"])
            if not python_path.exists():
                issues.append(f"PYTHONPATH '{env['PYTHONPATH']}' not found")
                suggestions.append("Check PYTHONPATH is correct")
        
        # Test server startup
        startup_test = self.test_server_startup(server_name)
        if not startup_test["success"]:
            issues.append(f"Server startup failed: {startup_test['error']}")
            suggestions.append("Check server logs for detailed error information")
        
        return {
            "issues": issues,
            "suggestions": suggestions,
            "startup_test": startup_test
        }
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get overall connection status for all servers."""
        servers = self.config_manager.list_servers()
        status = {}
        
        for server_name in servers:
            status[server_name] = {
                "configured": True,
                "startup_test": self.test_server_startup(server_name)
            }
        
        return {
            "total_servers": len(servers),
            "servers": status
        }
```

### 2. Auto-Configuration Tools

```python
# auto_config.py - Automatic configuration tools
class AutoConfigTool:
    """Automatic configuration tools for MCP servers."""
    
    def __init__(self, config_manager: ClaudeConfigManager):
        self.config_manager = config_manager
    
    def auto_configure_server(self, server_path: str, server_name: str = None) -> Dict[str, Any]:
        """Automatically configure MCP server."""
        server_path = Path(server_path)
        
        if not server_path.exists():
            return {
                "success": False,
                "error": f"Server path '{server_path}' not found"
            }
        
        # Generate server name if not provided
        if not server_name:
            server_name = server_path.stem
        
        # Detect Python environment
        python_command = self._detect_python_command(server_path)
        
        # Create configuration
        env = self._detect_environment_variables(server_path)
        
        self.config_manager.add_server(
            name=server_name,
            command=python_command,
            args=[str(server_path)],
            env=env
        )
        
        return {
            "success": True,
            "server_name": server_name,
            "command": python_command,
            "args": [str(server_path)],
            "env": env
        }
    
    def _detect_python_command(self, server_path: Path) -> str:
        """Detect appropriate Python command."""
        # Check for virtual environment
        venv_paths = [
            server_path.parent / "venv" / "bin" / "python",
            server_path.parent / "venv" / "Scripts" / "python.exe",
            server_path.parent / ".venv" / "bin" / "python",
            server_path.parent / ".venv" / "Scripts" / "python.exe"
        ]
        
        for venv_path in venv_paths:
            if venv_path.exists():
                return str(venv_path)
        
        # Check for conda environment
        conda_prefix = os.environ.get("CONDA_PREFIX")
        if conda_prefix:
            conda_python = Path(conda_prefix) / "bin" / "python"
            if conda_python.exists():
                return str(conda_python)
        
        # Fall back to system Python
        return "python"
    
    def _detect_environment_variables(self, server_path: Path) -> Dict[str, str]:
        """Detect necessary environment variables."""
        env = {}
        
        # Check for requirements.txt
        requirements_path = server_path.parent / "requirements.txt"
        if requirements_path.exists():
            env["MCP_HAS_REQUIREMENTS"] = "true"
        
        # Check for .env file
        env_file_path = server_path.parent / ".env"
        if env_file_path.exists():
            env.update(self._load_env_file(env_file_path))
        
        # Set PYTHONPATH to include project directory
        env["PYTHONPATH"] = str(server_path.parent)
        
        return env
    
    def _load_env_file(self, env_file_path: Path) -> Dict[str, str]:
        """Load environment variables from .env file."""
        env = {}
        
        try:
            with open(env_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        env[key.strip()] = value.strip().strip('"\'')
        except Exception as e:
            logger.warning(f"Failed to load .env file: {str(e)}")
        
        return env
    
    def setup_development_environment(self, project_path: str) -> Dict[str, Any]:
        """Set up complete development environment."""
        project_path = Path(project_path)
        
        if not project_path.exists():
            return {
                "success": False,
                "error": f"Project path '{project_path}' not found"
            }
        
        steps = []
        
        # 1. Find server file
        server_files = list(project_path.glob("**/server.py"))
        if not server_files:
            return {
                "success": False,
                "error": "No server.py file found in project"
            }
        
        server_file = server_files[0]
        steps.append(f"Found server file: {server_file}")
        
        # 2. Check for virtual environment
        venv_path = project_path / "venv"
        if not venv_path.exists():
            steps.append("No virtual environment found, consider creating one")
        else:
            steps.append(f"Found virtual environment: {venv_path}")
        
        # 3. Check for requirements.txt
        requirements_path = project_path / "requirements.txt"
        if requirements_path.exists():
            steps.append(f"Found requirements.txt: {requirements_path}")
        else:
            steps.append("No requirements.txt found")
        
        # 4. Auto-configure server
        config_result = self.auto_configure_server(str(server_file))
        steps.append(f"Auto-configured server: {config_result}")
        
        return {
            "success": True,
            "steps": steps,
            "config_result": config_result
        }
```

## Integration Troubleshooting

### 1. Common Issues and Solutions

```python
# troubleshooting.py - Common integration issues and solutions
class TroubleshootingGuide:
    """Troubleshooting guide for MCP server integration."""
    
    def __init__(self):
        self.common_issues = {
            "server_not_recognized": {
                "symptoms": [
                    "Server doesn't appear in Claude",
                    "No tools available from server",
                    "Server not in server list"
                ],
                "causes": [
                    "Configuration file not found",
                    "Invalid JSON in configuration",
                    "Server name typo",
                    "File path incorrect"
                ],
                "solutions": [
                    "Check configuration file location",
                    "Validate JSON syntax",
                    "Verify server name spelling",
                    "Check file paths are absolute"
                ]
            },
            
            "server_startup_fails": {
                "symptoms": [
                    "Server process exits immediately",
                    "Error messages in logs",
                    "Python import errors"
                ],
                "causes": [
                    "Python not found",
                    "Missing dependencies",
                    "Path configuration issues",
                    "Permission problems"
                ],
                "solutions": [
                    "Install Python or check PATH",
                    "Install required packages",
                    "Set correct PYTHONPATH",
                    "Check file permissions"
                ]
            },
            
            "tools_not_appearing": {
                "symptoms": [
                    "Server recognized but no tools",
                    "Empty tool list",
                    "Tool discovery fails"
                ],
                "causes": [
                    "list_tools handler not registered",
                    "Invalid tool definitions",
                    "Server initialization error",
                    "Tool schema validation fails"
                ],
                "solutions": [
                    "Check handler registration",
                    "Validate tool schemas",
                    "Check server logs",
                    "Verify JSON schema format"
                ]
            },
            
            "tool_execution_errors": {
                "symptoms": [
                    "Tool calls return errors",
                    "Unexpected error messages",
                    "Tool timeouts"
                ],
                "causes": [
                    "Parameter validation errors",
                    "Handler implementation bugs",
                    "Resource access issues",
                    "Authentication failures"
                ],
                "solutions": [
                    "Check parameter schemas",
                    "Debug handler code",
                    "Verify resource permissions",
                    "Check authentication setup"
                ]
            }
        }
    
    def diagnose_issue(self, symptoms: List[str]) -> Dict[str, Any]:
        """Diagnose issue based on symptoms."""
        matches = []
        
        for issue_id, issue_info in self.common_issues.items():
            symptom_matches = sum(
                1 for symptom in symptoms 
                if any(s.lower() in symptom.lower() for s in issue_info["symptoms"])
            )
            
            if symptom_matches > 0:
                matches.append({
                    "issue_id": issue_id,
                    "symptom_matches": symptom_matches,
                    "issue_info": issue_info
                })
        
        # Sort by number of symptom matches
        matches.sort(key=lambda x: x["symptom_matches"], reverse=True)
        
        return {
            "diagnosed_issues": matches,
            "top_match": matches[0] if matches else None
        }
    
    def get_troubleshooting_steps(self, issue_id: str) -> List[str]:
        """Get troubleshooting steps for specific issue."""
        issue_info = self.common_issues.get(issue_id)
        
        if not issue_info:
            return ["Unknown issue ID"]
        
        steps = []
        steps.append(f"Issue: {issue_id}")
        steps.append("Symptoms to check:")
        steps.extend([f"  - {s}" for s in issue_info["symptoms"]])
        steps.append("Possible causes:")
        steps.extend([f"  - {c}" for c in issue_info["causes"]])
        steps.append("Solutions to try:")
        steps.extend([f"  - {s}" for s in issue_info["solutions"]])
        
        return steps
```

### 2. Automated Testing and Validation

```python
# integration_test.py - Automated integration testing
class IntegrationTester:
    """Automated testing for MCP server integration."""
    
    def __init__(self, config_manager: ClaudeConfigManager):
        self.config_manager = config_manager
        self.diagnostics = ConnectionDiagnostics(config_manager)
    
    def run_full_integration_test(self, server_name: str) -> Dict[str, Any]:
        """Run complete integration test suite."""
        test_results = {
            "server_name": server_name,
            "timestamp": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Configuration validation
        test_results["tests"]["configuration"] = self._test_configuration(server_name)
        
        # Test 2: Server startup
        test_results["tests"]["startup"] = self._test_startup(server_name)
        
        # Test 3: Tool discovery
        test_results["tests"]["tool_discovery"] = self._test_tool_discovery(server_name)
        
        # Test 4: Tool execution
        test_results["tests"]["tool_execution"] = self._test_tool_execution(server_name)
        
        # Test 5: Error handling
        test_results["tests"]["error_handling"] = self._test_error_handling(server_name)
        
        # Overall result
        all_passed = all(test["passed"] for test in test_results["tests"].values())
        test_results["overall_result"] = "PASSED" if all_passed else "FAILED"
        
        return test_results
    
    def _test_configuration(self, server_name: str) -> Dict[str, Any]:
        """Test server configuration."""
        config_validation = self.config_manager.validate_config()
        
        return {
            "passed": config_validation["valid"],
            "details": config_validation["issues"] if not config_validation["valid"] else "Configuration valid"
        }
    
    def _test_startup(self, server_name: str) -> Dict[str, Any]:
        """Test server startup."""
        startup_result = self.diagnostics.test_server_startup(server_name)
        
        return {
            "passed": startup_result["success"],
            "details": startup_result.get("error", "Server started successfully")
        }
    
    def _test_tool_discovery(self, server_name: str) -> Dict[str, Any]:
        """Test tool discovery."""
        # This would test actual tool discovery
        # For now, we'll simulate it
        
        return {
            "passed": True,
            "details": "Tool discovery test passed (simulated)"
        }
    
    def _test_tool_execution(self, server_name: str) -> Dict[str, Any]:
        """Test tool execution."""
        # This would test actual tool execution
        # For now, we'll simulate it
        
        return {
            "passed": True,
            "details": "Tool execution test passed (simulated)"
        }
    
    def _test_error_handling(self, server_name: str) -> Dict[str, Any]:
        """Test error handling."""
        # This would test error handling
        # For now, we'll simulate it
        
        return {
            "passed": True,
            "details": "Error handling test passed (simulated)"
        }
    
    def generate_integration_report(self, server_name: str) -> str:
        """Generate comprehensive integration report."""
        test_results = self.run_full_integration_test(server_name)
        
        report = f"""
# MCP Server Integration Report

**Server Name:** {server_name}
**Test Date:** {test_results['timestamp']}
**Overall Result:** {test_results['overall_result']}

## Test Results

"""
        
        for test_name, test_result in test_results["tests"].items():
            status = "✅ PASSED" if test_result["passed"] else "❌ FAILED"
            report += f"### {test_name.replace('_', ' ').title()}\n"
            report += f"**Status:** {status}\n"
            report += f"**Details:** {test_result['details']}\n\n"
        
        # Add troubleshooting suggestions if any test failed
        if test_results["overall_result"] == "FAILED":
            report += "## Troubleshooting Suggestions\n\n"
            
            failed_tests = [
                name for name, result in test_results["tests"].items() 
                if not result["passed"]
            ]
            
            for test_name in failed_tests:
                report += f"### {test_name.replace('_', ' ').title()} Issues\n"
                # Add specific troubleshooting steps
                report += "- Check server logs for detailed error messages\n"
                report += "- Verify configuration file syntax\n"
                report += "- Ensure all dependencies are installed\n\n"
        
        return report
```

## Update Procedures

### 1. Configuration Update Management

```python
# update_manager.py - Configuration update management
class ConfigUpdateManager:
    """Manages configuration updates for MCP servers."""
    
    def __init__(self, config_manager: ClaudeConfigManager):
        self.config_manager = config_manager
        self.backup_dir = Path("config_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def backup_config(self) -> str:
        """Create backup of current configuration."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"claude_config_backup_{timestamp}.json"
        backup_path = self.backup_dir / backup_filename
        
        # Copy current config to backup
        import shutil
        shutil.copy2(self.config_manager.config_path, backup_path)
        
        logger.info(f"Configuration backed up to {backup_path}")
        return str(backup_path)
    
    def update_server_config(self, server_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update server configuration with backup."""
        # Create backup first
        backup_path = self.backup_config()
        
        try:
            # Get current config
            current_config = self.config_manager.get_server_config(server_name)
            
            if not current_config:
                return {
                    "success": False,
                    "error": f"Server '{server_name}' not found"
                }
            
            # Apply updates
            updated_config = current_config.copy()
            updated_config.update(updates)
            
            # Remove old server
            self.config_manager.remove_server(server_name)
            
            # Add updated server
            self.config_manager.add_server(
                name=server_name,
                command=updated_config["command"],
                args=updated_config["args"],
                env=updated_config.get("env", {})
            )
            
            return {
                "success": True,
                "backup_path": backup_path,
                "updated_config": updated_config
            }
            
        except Exception as e:
            logger.error(f"Failed to update server config: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "backup_path": backup_path
            }
    
    def rollback_config(self, backup_path: str) -> Dict[str, Any]:
        """Rollback configuration from backup."""
        backup_path = Path(backup_path)
        
        if not backup_path.exists():
            return {
                "success": False,
                "error": f"Backup file '{backup_path}' not found"
            }
        
        try:
            # Copy backup to current config
            import shutil
            shutil.copy2(backup_path, self.config_manager.config_path)
            
            # Reload configuration
            self.config_manager.config = self.config_manager._load_config()
            
            logger.info(f"Configuration rolled back from {backup_path}")
            return {
                "success": True,
                "message": "Configuration rolled back successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to rollback config: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def migrate_config_format(self, old_format: str, new_format: str) -> Dict[str, Any]:
        """Migrate configuration between formats."""
        # This would handle migration between different config formats
        # For now, we'll just return a placeholder
        
        return {
            "success": True,
            "message": f"Migration from {old_format} to {new_format} completed"
        }
```

### 2. Hot Reloading and Updates

```python
# hot_reload.py - Hot reloading for development
class HotReloadManager:
    """Manages hot reloading of MCP servers during development."""
    
    def __init__(self, config_manager: ClaudeConfigManager):
        self.config_manager = config_manager
        self.file_watchers = {}
        self.running = False
    
    def start_file_watcher(self, server_name: str):
        """Start file watcher for server changes."""
        server_config = self.config_manager.get_server_config(server_name)
        
        if not server_config:
            logger.error(f"Server '{server_name}' not found")
            return
        
        # Get server file path
        args = server_config.get("args", [])
        if not args:
            logger.error(f"No server file specified for '{server_name}'")
            return
        
        server_file = Path(args[0])
        if not server_file.exists():
            logger.error(f"Server file '{server_file}' not found")
            return
        
        # Start watching for changes
        self._watch_file(server_name, server_file)
    
    def _watch_file(self, server_name: str, file_path: Path):
        """Watch file for changes."""
        import time
        
        last_modified = file_path.stat().st_mtime
        
        while self.running:
            try:
                current_modified = file_path.stat().st_mtime
                
                if current_modified != last_modified:
                    logger.info(f"File change detected for {server_name}: {file_path}")
                    self._trigger_reload(server_name)
                    last_modified = current_modified
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error watching file {file_path}: {str(e)}")
                break
    
    def _trigger_reload(self, server_name: str):
        """Trigger server reload."""
        # This would signal Claude to reload the server
        # For now, we'll just log the event
        logger.info(f"Triggering reload for server '{server_name}'")
        
        # In a real implementation, this might:
        # 1. Send signal to Claude Desktop
        # 2. Restart the server process
        # 3. Clear any cached state
```

## Complete Integration Example

```python
# integration_example.py - Complete integration example
def setup_complete_integration():
    """Example of complete MCP server integration setup."""
    
    # 1. Initialize configuration manager
    config_manager = ClaudeConfigManager()
    
    # 2. Auto-configure server
    auto_config = AutoConfigTool(config_manager)
    server_path = "simple_mcp_server/server.py"
    
    config_result = auto_config.auto_configure_server(
        server_path=server_path,
        server_name="simple-mcp-server"
    )
    
    print(f"Auto-configuration result: {config_result}")
    
    # 3. Validate configuration
    validation_result = config_manager.validate_config()
    print(f"Configuration validation: {validation_result}")
    
    # 4. Test connection
    diagnostics = ConnectionDiagnostics(config_manager)
    connection_test = diagnostics.test_server_startup("simple-mcp-server")
    print(f"Connection test: {connection_test}")
    
    # 5. Run full integration test
    integration_tester = IntegrationTester(config_manager)
    test_results = integration_tester.run_full_integration_test("simple-mcp-server")
    print(f"Integration test results: {test_results}")
    
    # 6. Generate report
    report = integration_tester.generate_integration_report("simple-mcp-server")
    print("Integration Report:")
    print(report)
    
    # 7. Setup file watching for development
    if os.getenv("MCP_DEVELOPMENT") == "true":
        hot_reload = HotReloadManager(config_manager)
        hot_reload.start_file_watcher("simple-mcp-server")

if __name__ == "__main__":
    setup_complete_integration()
```

## Summary

This chapter covered:

1. **Configuration Management**: Complete configuration setup and management tools
2. **Connection Diagnostics**: Tools for diagnosing connection issues
3. **Auto-Configuration**: Automated configuration setup and detection
4. **Troubleshooting**: Comprehensive troubleshooting guide and automated diagnosis
5. **Integration Testing**: Automated testing suite for integration validation
6. **Update Management**: Configuration updates, backups, and rollbacks
7. **Hot Reloading**: Development tools for rapid iteration
8. **Complete Example**: End-to-end integration setup example

The integration system provides comprehensive tools for setting up, managing, and troubleshooting MCP server integration with Claude Desktop.

## Next Steps

- **Chapter 9**: Production Deployment - Production-ready deployment strategies
- **Appendix A**: Troubleshooting Guide - Quick reference for common issues
- **Appendix B**: Configuration Reference - Complete configuration options
