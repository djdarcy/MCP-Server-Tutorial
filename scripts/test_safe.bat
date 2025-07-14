@echo off
REM Simple test runner for Windows that avoids Unicode issues

echo ==========================================
echo MCP Debug Test - Windows Safe Test Runner
echo ==========================================

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Set console to use UTF-8 encoding
chcp 65001 > nul

REM Run test with output redirection to avoid Unicode issues
echo Running tests...
python tests\test_simple.py > test_output.log 2>&1

REM Check if tests passed
if %errorlevel% equ 0 (
    echo [PASS] Tests completed successfully
    echo Check test_output.log for details
) else (
    echo [FAIL] Tests failed with errors
    echo Check test_output.log for details
)

echo.
echo Test output saved to: test_output.log
echo Log files available in: logs\
echo.

pause
