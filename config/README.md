# Claude Desktop Configuration

This folder contains configuration files for integrating the MCP Server Tutorial with Claude Desktop.

## Files

### `claude_desktop.json`

This is the **local development configuration** used by the project maintainer. It contains absolute paths specific to the development environment and should not be used directly by new users.

### `claude_desktop.sample.json`

This is the **template configuration** that new users should copy and modify for their setup. It contains placeholder paths that need to be updated with your actual project location.

## Setup Instructions

1. **Copy the sample configuration:**

   ```bash
   cp config/claude_desktop.sample.json config/claude_desktop.json
   ```

2. **Locate your Claude Desktop configuration file:**
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. **Update the paths in your new `claude_desktop.json`:**
   - Replace `/path/to/your/MCP-Server-Tutorial/` with the actual path to your tutorial project
   - For example, if you cloned to `C:\projects\MCP-Server-Tutorial\`, use:

     ```json
     "args": ["C:\\projects\\MCP-Server-Tutorial\\simple_mcp_server\\server.py"]
     ```

   - For Unix-like systems, use forward slashes:

     ```json
     "args": ["/home/user/MCP-Server-Tutorial/simple_mcp_server/server.py"]
     ```

4. **Copy the configuration:**
   - Open your Claude Desktop configuration file
   - Add the `mcpServers` section from your updated `claude_desktop.json` to your configuration
   - If you already have `mcpServers`, add the `mcp-server-tutorial` entry to it

5. **Example complete configuration:**

   ```json
   {
     "mcpServers": {
       "mcp-server-tutorial": {
         "command": "python",
         "args": [
           "/YOUR/ACTUAL/PATH/MCP-Server-Tutorial/simple_mcp_server/server.py"
         ],
         "env": {
           "PYTHONPATH": "/YOUR/ACTUAL/PATH/MCP-Server-Tutorial/simple_mcp_server",
           "PYTHONUNBUFFERED": "1",
           "LOG_LEVEL": "INFO"
         }
       }
     }
   }
   ```

6. **Restart Claude Desktop** for the changes to take effect.

## Troubleshooting

- **Server not appearing**: Check that the paths are correct and Python can be found
- **Import errors**: Verify the `PYTHONPATH` is set correctly
- **Permission issues**: Ensure Claude Desktop has permission to execute Python and access the project files
- **Logs**: Check the server logs in the `logs/` directory for detailed error information

## Alternative: Using Virtual Environment

If you're using a virtual environment, you can specify the Python interpreter from your venv:

```json
{
  "mcpServers": {
    "mcp-server-tutorial": {
      "command": "/path/to/your/MCP-Server-Tutorial/venv/bin/python",
      "args": [
        "/path/to/your/MCP-Server-Tutorial/simple_mcp_server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/your/MCP-Server-Tutorial/simple_mcp_server",
        "PYTHONUNBUFFERED": "1",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

For Windows with virtual environment:

```json
{
  "mcpServers": {
    "mcp-server-tutorial": {
      "command": "C:\\path\\to\\your\\MCP-Server-Tutorial\\venv\\Scripts\\python.exe",
      "args": [
        "C:\\path\\to\\your\\MCP-Server-Tutorial\\simple_mcp_server\\server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\your\\MCP-Server-Tutorial\\simple_mcp_server",
        "PYTHONUNBUFFERED": "1",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```
