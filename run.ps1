# Run CrewAI System - Startup Script
# 
# This script ensures the virtual environment is activated and runs the system.

Write-Host "`n Starting CrewAI Autonomous Engineering Team`n" -ForegroundColor Cyan

# CRITICAL FIX: Force UTF-8 encoding to prevent Windows charmap codec errors
$env:PYTHONUTF8 = "1"
Write-Host " UTF-8 encoding enabled (fixes file reading errors)`n" -ForegroundColor Green

# Check if we're in the right directory
if (-not (Test-Path ".\swe_team\src\swe_team\main.py")) {
    Write-Host " Error: Please run this script from the swe-team root directory" -ForegroundColor Red
    Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "   Expected: C:\Users\OFFICIAL\Desktop\swe-team" -ForegroundColor Yellow
    exit 1
}

# Check if venv exists
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host " Error: Virtual environment not found at .venv" -ForegroundColor Red
    Write-Host "   Please create it with: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Activate virtual environment
Write-Host " Activating virtual environment..." -ForegroundColor Green
& .\.venv\Scripts\Activate.ps1

# Check if activation worked
if ($env:VIRTUAL_ENV) {
    Write-Host " Virtual environment activated: $env:VIRTUAL_ENV`n" -ForegroundColor Green
} else {
    Write-Host " Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}

# Check if swe_team package is installed
Write-Host " Checking if swe_team package is installed..." -ForegroundColor Green
cd swe_team
$packageCheck = pip show swe_team 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Package not installed. Installing now..." -ForegroundColor Yellow
    pip install -e .
    if ($LASTEXITCODE -ne 0) {
        Write-Host " Failed to install package" -ForegroundColor Red
        cd ..
        exit 1
    }
    Write-Host " Package installed successfully!`n" -ForegroundColor Green
} else {
    Write-Host " Package already installed`n" -ForegroundColor Green
}
cd ..

# Check if Docker is running
Write-Host " Checking Docker..." -ForegroundColor Green
try {
    docker info | Out-Null
    Write-Host " Docker is running`n" -ForegroundColor Green
} catch {
    Write-Host " Docker is not running!" -ForegroundColor Red
    Write-Host "   Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Check if Docker MCP Gateway is running (optional)
Write-Host " Checking Docker MCP Gateway..." -ForegroundColor Green
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/mcp" -Method POST -TimeoutSec 2 -ErrorAction SilentlyContinue
    Write-Host " Docker MCP Gateway is running (optional features available)" -ForegroundColor Green
    
    # Clear MCP memory to avoid pollution from previous projects
    Write-Host " Clearing MCP memory from previous runs..." -ForegroundColor Yellow
    python clear_mcp_memory.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host " MCP memory cleared`n" -ForegroundColor Green
    } else {
        Write-Host " Warning: Could not clear MCP memory (continuing anyway)`n" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  Docker MCP Gateway not running (optional features unavailable)" -ForegroundColor Yellow
    Write-Host "   To start: docker mcp gateway run --transport streaming --port 8000`n" -ForegroundColor Yellow
}

# Navigate to swe_team directory
Write-Host " Navigating to project directory..." -ForegroundColor Green
cd swe_team

# Reset workflow state for fresh run
Write-Host " Resetting workflow state (to-do list, progress tracker)..." -ForegroundColor Yellow
$resetResult = python -c "from swe_team.tools.workflow_tools import reset_workflow_state; reset_workflow_state(); print('Workflow state reset')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host " Workflow state reset`n" -ForegroundColor Green
} else {
    Write-Host " Warning: Could not reset workflow state (continuing anyway)`n" -ForegroundColor Yellow
}

# Run the system
Write-Host " Launching CrewAI system...`n" -ForegroundColor Cyan
Write-Host "=" * 70 -ForegroundColor Cyan
python -m swe_team.main

# Return to original directory
cd ..

Write-Host "`n CrewAI execution complete!" -ForegroundColor Green

