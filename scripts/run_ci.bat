@echo off
REM
REM Comprehensive CI Workflow Runner for Warp Content Processor (Windows)
REM
REM This script provides easy access to all our quality and security tooling.
REM Usage: scripts\run_ci.bat [command]
REM
REM Commands:
REM   quality  - Run code quality checks and fixes
REM   security - Run security scanning  
REM   ci       - Run full CI workflow
REM   help     - Show this help message
REM

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Function to print colored output (basic Windows version)
goto :main

:print_info
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

:check_python
python --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Python is not installed or not in PATH"
    exit /b 1
)
goto :eof

:show_help
echo Warp Content Processor CI Workflow Runner (Windows)
echo.
echo Usage: scripts\run_ci.bat [command]
echo.
echo Commands:
echo   quality   - Run code quality checks and automated fixes
echo             - Includes: isort, black, ruff, mypy, pylint, trunk
echo.
echo   security  - Run comprehensive security scanning
echo             - Includes: bandit, safety, trufflehog, osv-scanner, pip-audit
echo.
echo   ci        - Run complete CI workflow
echo             - Includes: quality checks + security scans + tests
echo.
echo   help      - Show this help message
echo.
echo Examples:
echo   scripts\run_ci.bat quality    # Run only quality checks
echo   scripts\run_ci.bat security   # Run only security scans
echo   scripts\run_ci.bat ci         # Run full CI pipeline
goto :eof

:run_quality
call :print_info "Starting code quality checks and automated fixes..."
cd /d "%PROJECT_ROOT%"
python scripts\quality_check.py

if !errorlevel! equ 0 (
    call :print_success "Code quality checks completed successfully!"
) else (
    call :print_error "Code quality checks failed. Please review the output above."
    exit /b 1
)
goto :eof

:run_security
call :print_info "Starting comprehensive security scanning..."
cd /d "%PROJECT_ROOT%"
python scripts\security_scan.py

if !errorlevel! equ 0 (
    call :print_success "Security scanning completed successfully!"
) else (
    call :print_warning "Some security scans failed. Please review the output above."
    REM Don't exit on security scan failures - they might be warnings
)
goto :eof

:run_ci
call :print_info "Starting comprehensive CI workflow..."
cd /d "%PROJECT_ROOT%"
python scripts\ci_workflow.py

if !errorlevel! equ 0 (
    call :print_success "Full CI workflow completed successfully!"
    call :print_success "Your code is ready for deployment!"
) else (
    call :print_error "CI workflow failed. Please review the output above."
    exit /b 1
)
goto :eof

:main
call :check_python

set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=ci

if "%COMMAND%"=="quality" (
    call :run_quality
) else if "%COMMAND%"=="security" (
    call :run_security
) else if "%COMMAND%"=="ci" (
    call :run_ci
) else if "%COMMAND%"=="help" (
    call :show_help
) else if "%COMMAND%"=="-h" (
    call :show_help
) else if "%COMMAND%"=="--help" (
    call :show_help
) else (
    call :print_error "Unknown command: %COMMAND%"
    echo.
    call :show_help
    exit /b 1
)

endlocal
