@echo off
REM Setup script for MCP Debug Test Project on Windows

echo ========================================
echo MCP Debug Test Setup
echo ========================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo Found Python: 
python --version

REM Check if pip is available
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo Found pip:
python -m pip --version

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
python -m pip install mcp

REM Create logs directory
if not exist "logs" (
    echo Creating logs directory...
    mkdir logs
)

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To run the MCP server:
echo   1. Activate the virtual environment: venv\Scripts\activate.bat
echo   2. Run the server: python simple_mcp_server\server.py
echo.
echo To test the server:
echo   1. Activate the virtual environment: venv\Scripts\activate.bat
echo   2. Run tests: python tests\test_server.py
echo.
echo To debug in VS Code:
echo   1. Open this folder in VS Code
echo   2. Go to Run and Debug (Ctrl+Shift+D)
echo   3. Select "Debug MCP Server" and press F5
echo.
echo To register with Claude Code:
echo   1. Copy config\claude_desktop.json content
echo   2. Add to your Claude Desktop configuration
echo   3. Restart Claude Desktop
echo.
pause
