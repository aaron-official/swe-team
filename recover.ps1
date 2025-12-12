# Emergency Recovery Script for Failed CrewAI Runs
# Use this when the crew run fails due to encoding or Docker issues

Write-Host ""
Write-Host "[RECOVERY] CrewAI Emergency Recovery" -ForegroundColor Yellow
Write-Host ""

# Step 1: Stop any running containers
Write-Host "1. Stopping autonomous_dev_env container..." -ForegroundColor Cyan
$stopResult = docker stop autonomous_dev_env 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Container stopped" -ForegroundColor Green
} else {
    Write-Host "   [INFO] Container not running" -ForegroundColor Gray
}

# Step 2: Remove the container
Write-Host "2. Removing container..." -ForegroundColor Cyan
$rmResult = docker rm autonomous_dev_env 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Container removed" -ForegroundColor Green
} else {
    Write-Host "   [INFO] Container already removed" -ForegroundColor Gray
}

# Step 3: Force UTF-8 encoding
Write-Host "3. Setting UTF-8 encoding..." -ForegroundColor Cyan
$env:PYTHONUTF8 = "1"
Write-Host "   [OK] PYTHONUTF8=1 set" -ForegroundColor Green

# Step 4: Clear MCP memory if available
Write-Host "4. Clearing MCP memory..." -ForegroundColor Cyan
$mcpResult = python clear_mcp_memory.py 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] MCP memory operation complete" -ForegroundColor Green
} else {
    Write-Host "   [WARN] MCP memory clear skipped (MCP not available)" -ForegroundColor Yellow
}

# Step 5: Verify setup
Write-Host ""
Write-Host "5. Verifying setup..." -ForegroundColor Cyan

# Check Docker
$dockerCheck = docker info 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   [OK] Docker is running" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Docker is NOT running!" -ForegroundColor Red
    Write-Host "      Please start Docker Desktop first" -ForegroundColor Yellow
    exit 1
}

# Check virtual environment
if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    Write-Host "   [OK] Virtual environment exists" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Virtual environment missing!" -ForegroundColor Red
    Write-Host "      Run: python -m venv .venv" -ForegroundColor Yellow
    exit 1
}

# Check swe_team directory
if (Test-Path ".\swe_team\src\swe_team\main.py") {
    Write-Host "   [OK] Project structure correct" -ForegroundColor Green
} else {
    Write-Host "   [ERROR] Wrong directory!" -ForegroundColor Red
    Write-Host "      cd to swe-team root" -ForegroundColor Yellow
    exit 1
}

# Check output directory
$outputDir = ".\swe_team\output"
if (Test-Path $outputDir) {
    $fileCount = (Get-ChildItem -Path $outputDir -File).Count
    Write-Host "   [OK] Output directory exists with $fileCount files" -ForegroundColor Green
} else {
    Write-Host "   [WARN] Output directory will be created on first run" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[OK] Recovery complete! You can now run:" -ForegroundColor Green
Write-Host "   .\run.ps1" -ForegroundColor Cyan
Write-Host ""

# Optional: Ask if user wants to run immediately
$response = Read-Host "Run the crew now? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    Write-Host ""
    Write-Host "[STARTING] Launching crew..." -ForegroundColor Cyan
    Write-Host ""
    & .\run.ps1
}
