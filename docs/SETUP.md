# 🛠 Setup Guide

Complete environment setup for the Autonomous Software Engineering Crew.

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.11+ | Core runtime |
| **Docker Desktop** | Latest | Isolated code execution |
| **Git** | Any | Version control |

## Step 1: Clone & Create Environment

```powershell
git clone https://github.com/aaron-official/swe-team.git
cd swe-team

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Linux/Mac)
source .venv/bin/activate
```

## Step 2: Install Dependencies

```powershell
# Install the project in editable mode
pip install -e .

# Verify installation
python -c "from swe_team.crew import EngineeringTeam; print('✅ Installation successful')"
```

## Step 3: Configure API Keys

Create a `.env` file in the project root:

```bash
# Required - LLM Providers
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-api03-...

# Required - Web Search
SERPER_API_KEY=...

# Optional - MCP Gateway (for advanced features)
MCP_GATEWAY_URL=http://localhost:8000/mcp
```

**Also copy to `swe_team/.env`** (CrewAI reads from both locations):
```powershell
Copy-Item .env swe_team\.env
```

## Step 4: Docker Setup

### Start Docker Desktop

1. Open Docker Desktop application
2. Wait for "Docker Desktop is running" status
3. Verify in terminal:

```powershell
docker info
# Should show Docker version and system info
```

### First Run Container Setup

The system automatically creates a container named `autonomous_dev_env` on first run. To manually prepare:

```powershell
# Pull the base image (optional, done automatically)
docker pull nikolaik/python-nodejs:latest

# Verify image
docker images | Select-String "nikolaik"
```

### Container Lifecycle

| Command | Purpose |
|---------|---------|
| `docker ps` | Check if container is running |
| `docker stop autonomous_dev_env` | Stop container |
| `docker rm autonomous_dev_env` | Remove container (fresh start) |
| `docker exec -it autonomous_dev_env bash` | Shell into container |

## Step 5: Verify Setup

Run the verification command:

```powershell
.\run.ps1
```

You should see:
```
✅ Starting CrewAI Autonomous Engineering Team
✅ UTF-8 encoding enabled
✅ Activating virtual environment...
✅ Docker is running
✅ Workflow state reset
✅ Launching CrewAI system...
```

## Troubleshooting

### ❌ "Docker is not running"

```powershell
# Start Docker Desktop, then verify:
docker info
```

### ❌ Virtual environment not found

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

### ❌ API key errors

```powershell
# Verify .env exists and has correct format:
Get-Content .env

# Keys should NOT have quotes:
# ✅ OPENAI_API_KEY=sk-proj-abc123
# ❌ OPENAI_API_KEY="sk-proj-abc123"
```

### ❌ File encoding errors (Windows)

The system auto-sets `PYTHONUTF8=1`. If you see encoding errors:

```powershell
$env:PYTHONUTF8 = "1"
.\run.ps1
```

### ❌ Container mount issues

Reset the container:

```powershell
docker stop autonomous_dev_env
docker rm autonomous_dev_env
.\run.ps1
```

## Optional: MCP Gateway

For advanced features like memory persistence and external tools:

```powershell
# Start MCP Gateway (if you have it configured)
docker mcp gateway run --transport streaming --port 8000
```

The system works without MCP—it gracefully degrades.

---

## Quick Reference

| Task | Command |
|------|---------|
| Start the crew | `.\run.ps1` |
| Emergency recovery | `.\recover.ps1` |
| Enter container | `docker exec -it autonomous_dev_env bash` |
| View generated code | `ls swe_team\output\` |
| Clear output | `Remove-Item swe_team\output\* -Recurse` |
