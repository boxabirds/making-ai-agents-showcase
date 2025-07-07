@echo off
REM Tech Writer Agent Launcher Script for C implementation (Windows)

set SCRIPT_DIR=%~dp0

REM Check if executable exists
if not exist "%SCRIPT_DIR%tech-writer.exe" (
    echo Building tech-writer...
    cd /d "%SCRIPT_DIR%"
    nmake clean
    nmake
    if errorlevel 1 exit /b 1
)

REM Execute the tech writer
"%SCRIPT_DIR%tech-writer.exe" %*