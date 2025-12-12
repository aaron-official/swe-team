# 🤖 Autonomous Software Engineering Crew

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white)
![CrewAI](https://img.shields.io/badge/CrewAI-Multi--Agent-purple?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![Anthropic](https://img.shields.io/badge/Anthropic-Claude-orange?style=for-the-badge)

**An AI-powered software engineering team that autonomously builds complete applications from natural language descriptions.**

[Quick Start](#-quick-start) • [Architecture](#-architecture) • [How It Works](#-how-it-works) • [Features](#-features) • [Demo](#-demo)

</div>

---

## 🎯 What This Does

Describe what you want to build in plain English. Watch 8 specialized AI agents collaborate to design, implement, test, and deliver a working application—completely autonomously.

```
Input:  "Build a task tracker with dark mode, REST API, and SQLite storage"
Output: A fully functional web application with backend, frontend, and database
```

**No boilerplate. No scaffolding. No Stack Overflow. Just results.**

---

## ⚡ Quick Start

```powershell
# 1. Clone and setup
git clone https://github.com/aaron-official/swe-team.git
cd swe-team
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

# 2. Configure API keys (.env file)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SERPER_API_KEY=...

# 3. Define your project (edit this file)
notepad swe_team\src\swe_team\instructions.py

# 4. Run the crew
.\run.ps1
```

**Prerequisites:** Docker Desktop running, Python 3.11+, API keys for OpenAI & Anthropic

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          HIERARCHICAL CREW MANAGER                          │
│                     (GPT-4o orchestrating all agents)                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        ▼                             ▼                             ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│  PHASE 1:     │           │  PHASE 2:     │           │  PHASE 3:     │
│  DISCOVERY    │    ───►   │  DESIGN       │    ───►   │  BUILD        │
├───────────────┤           ├───────────────┤           ├───────────────┤
│ PM Agent      │           │ DevOps Agent  │           │ Backend Eng.  │
│ CTO Agent     │           │ Architect     │           │ Frontend Eng. │
└───────────────┘           └───────────────┘           └───────────────┘
                                                                │
                                      ┌─────────────────────────┘
                                      ▼
                            ┌───────────────┐
                            │  PHASE 4:     │
                            │  VERIFY       │
                            ├───────────────┤
                            │ Code Reviewer │
                            │ Test Engineer │
                            └───────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────┐
                    │     📦 OUTPUT: Working App      │
                    │  backend_app.py + frontend_app  │
                    │  + tests + documentation        │
                    └─────────────────────────────────┘
```

### The 8 Specialized Agents

> **Built with GPT-5-mini** — OpenAI's efficient reasoning model

| Agent | Role | Responsibility |
|-------|------|----------------|
| **Product Manager** | Strategic | Transform vague ideas → detailed PRDs |
| **CTO** | Research | Select & validate tech stack via web research |
| **DevOps Engineer** | Execution | Install packages in Docker, capture versions |
| **Engineering Lead** | Architecture | Design for *actual* installed versions |
| **Backend Engineer** | Implementation | Build Python/FastAPI backends |
| **Frontend Engineer** | Implementation | Build UI (Vanilla JS/React/Gradio) |
| **Code Reviewer** | Quality | Security audit & specification compliance |
| **Test Engineer** | Validation | Execute in Docker, validate functionality |

### 🚀 Future Potential

This demo was built using **GPT-5-mini** — a lightweight, cost-efficient model. 

**Imagine what's possible with frontier models:**

| Model | Provider | Released | Key Capability |
|-------|----------|----------|----------------|
| **GPT-5.2** | OpenAI | Dec 2025 | Long-running agents, professional reasoning |
| **Claude Opus 4.5** | Anthropic | Nov 2025 | Best-in-class coding & agentic workflows |
| **Gemini 3.0 Deep Think** | Google | Dec 2025 | Most intelligent, enhanced reasoning |
| **Grok 4.1** | xAI | Nov 2025 | Agent Tools API, real-time data processing |
| **Kimi K2 Thinking** | Moonshot | Nov 2025 | Open-source, optimized for agentic coding |

> *The architecture is model-agnostic. Swap in any model via `agents.yaml` and watch the quality scale.*

---

## 🔄 How It Works

### The "Reality-First" Development Pattern

Unlike traditional code generators, this system **executes in a real environment** and **designs for what's actually installed**:

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│  CTO decides:  │     │ DevOps runs:   │     │ Architect reads│
│  "Use FastAPI" │ ──► │ pip install... │ ──► │ lockfile.txt   │
│                │     │ pip freeze     │     │ sees: 0.115.0  │
└────────────────┘     └────────────────┘     └────────────────┘
                                                      │
            ┌─────────────────────────────────────────┘
            ▼
  ┌────────────────────────────────────────────────────────────┐
  │  Architect designs for FastAPI 0.115.0 specifically        │
  │  (Uses Annotated types, not deprecated patterns)           │
  │  Backend Engineer follows architecture exactly              │
  └────────────────────────────────────────────────────────────┘
```

**Why this matters:** No more "works on my machine" or deprecated API calls. The system adapts to the *actual runtime* it's deploying to.

### Self-Correction Loop

```
Test Engineer finds error ──► Manager analyzes failure
         ▲                            │
         │                            ▼
         │                   Identifies responsible agent
         │                            │
         └────── Re-runs task ◄───────┘
         
         (Max 3 retries before escalation)
```

---

## 🛠 Features

### Core Capabilities
- **🐳 Docker Sandboxing** — All code execution in isolated containers
- **🧠 Multi-Model Orchestration** — GPT-4o for strategy, Claude for implementation
- **🔍 Real-Time Research** — CTO validates libraries aren't deprecated
- **📝 Version-Aware Design** — Architecture matches installed package versions
- **🔄 Autonomous Recovery** — Self-corrects errors without human intervention

### Workflow Tools

| Tool | Purpose |
|------|---------|
| **To-Do List** | Agents track sub-tasks and mark completion |
| **Progress Reporter** | Real-time status across all crew tasks |
| **Validation Checkpoint** | Verify dependencies before proceeding |

```python
# Example: Agent checks if it can start
validator._run("check_ready", task_name="backend_task")
# Output: "✅ backend_task is ready. Dependencies complete: design_task"
```

### Built-in Resilience
- **UTF-8 Encoding** — Windows-safe file operations with fallback tools
- **Docker Volume Sync** — Consistent mount mode for Windows compatibility
- **MCP Memory Management** — Clears context between project runs

---

## 📁 Project Structure

```
swe-team/
├── swe_team/
│   ├── src/swe_team/
│   │   ├── main.py              # Entry point
│   │   ├── crew.py              # Agent orchestration (EngineeringTeam class)
│   │   ├── instructions.py      # 📝 YOUR PROJECT DEFINITION HERE
│   │   ├── config/
│   │   │   ├── agents.yaml      # Agent roles, goals, backstories
│   │   │   └── tasks.yaml       # Task definitions with dependencies
│   │   └── tools/
│   │       ├── tools.py         # DockerShellTool, SmartSearchTool
│   │       ├── workflow_tools.py # TodoList, Progress, Validation
│   │       └── utf8_file_tools.py
│   └── output/                  # 📦 GENERATED CODE APPEARS HERE
│       ├── requirements.md
│       ├── tech_stack.md
│       ├── architecture.md
│       ├── backend_app.py
│       └── frontend_app.py
├── run.ps1                      # One-click startup script
├── recover.ps1                  # Emergency recovery
└── docs/
    ├── SETUP.md                 # Environment setup guide
    └── ARCHITECTURE.md          # Deep technical dive
```

---

## 💡 Defining Your Project

Want to build something new? Here's how:

### Step 1: Open the Instructions File

```powershell
notepad swe_team\src\swe_team\instructions.py
```

### Step 2: Edit the REQUIREMENTS Variable

Replace the contents with your project description:

```python
REQUIREMENTS = """
Build a personal finance tracker with:
- Dashboard showing income vs expenses
- Transaction categorization  
- Monthly budget goals with progress bars
- Dark mode with purple accent (#7C3AED)
- Export to CSV functionality
- SQLite database for local storage
"""

# Optional: Add constraints
CONSTRAINTS = """
- Must work offline (no external APIs)
- Single-page application
- Mobile-responsive design
"""
```

### Step 3: Run the Crew

```powershell
.\run.ps1
```

### Step 4: Find Your Generated Code

```powershell
ls swe_team\output\
# Your app files will appear here!
```

> **Tip:** Be specific in your requirements! The more detail you provide, the better the output.

---

## 📦 Included Demo: Task Tracker App

This repo includes a complete working application generated by the crew — a **Task Tracker** with full CRUD functionality.

### What's in `swe_team/output/`:

| File | Description |
|------|-------------|
| `requirements.md` | Product requirements document |
| `tech_stack.md` | Technology decisions with rationale |
| `architecture.md` | System design and API contracts |
| `backend_app.py` | **FastAPI backend** (669 lines) |
| `frontend_app.py` | **Vanilla JS frontend generator** (434 lines) |
| `lockfile.txt` | Exact installed package versions |
| `test_report.md` | Execution test results |

### Run the Demo

```powershell
cd swe_team\output

# Terminal 1: Start backend
python backend_app.py
# → Runs on http://localhost:8081

# Terminal 2: Start frontend  
python frontend_app.py
# → Runs on http://localhost:3000, opens browser
```

### Demo Features
- ✅ Create, edit, delete tasks
- ✅ Filter by status (pending/in-progress/completed)
- ✅ Sort by priority or date
- ✅ Search functionality
- ✅ Export to JSON
- ✅ Dark mode UI
- ✅ SQLite persistence

> **This entire application was built autonomously by the AI crew from a single prompt.**

---

## 🎬 How It Was Built

### The Prompt
```
"Build a task management app with status tracking, priority levels, 
and a modern dark UI. Include REST API and vanilla JavaScript frontend."
```

### The Output (Generated in ~25 minutes)

**Backend (FastAPI):**
```python
@app.post("/api/tasks", status_code=201)
async def create_task(payload: TaskCreate) -> TaskOut:
    """Create a new task with validation."""
    created = create_task(payload)
    return TaskOut(**created)
```

**Frontend (Vanilla JS):**
```javascript
async function fetchTasks(filters = {}) {
  const params = new URLSearchParams();
  if(filters.status) params.set('status', filters.status);
  const url = API_BASE + '?' + params.toString();
  return await apiFetch(url);
}
```

**Result:** A fully working CRUD app with SQLite persistence, CORS handling, dark theme, and responsive design.

---

## 🔧 Technical Highlights

### Model Configuration (Easily Swappable)
```yaml
# agents.yaml - Current setup uses GPT-5-mini for all agents
product_manager:
  llm: openai/gpt-5-mini         # Cost-efficient reasoning
  
backend_engineer:
  llm: openai/gpt-5-mini         # Same model, consistent quality

# Want better results? Just change the model:
# llm: openai/gpt-5.2            # Frontier reasoning
# llm: anthropic/claude-opus-4.5 # Best coding model
# llm: google/gemini-2.0-flash   # 1M context window
```

### Docker Execution Layer
```python
class DockerShellTool(BaseTool):
    """Execute commands in persistent container."""
    
    def _run(self, command: str) -> str:
        container = client.containers.run(
            "nikolaik/python-nodejs",
            mounts=[Mount("/app", source=output_dir, consistency="consistent")],
            working_dir="/app"
        )
        return container.exec_run(f"bash -c '{command}'")
```

### Workflow State Management
```json
// .workflow_state.json (auto-generated)
{
  "progress": {
    "pm_task": {"status": "complete", "output_file": "requirements.md"},
    "backend_task": {"status": "running", "progress_percent": 60}
  },
  "files": {
    "requirements.md": {"created_by": "pm_task", "created_at": "..."}
  }
}
```

---

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Average Build Time** | 15-45 minutes |
| **Cost per Run** | ~$0.50 - $2.00 (API tokens) |
| **Success Rate** | ~85% first-run, ~95% with retries |
| **Supported Outputs** | Python backends, JS/TS frontends, Gradio UIs |

---

## 🚀 Roadmap

- [ ] **Streaming Output** — Watch agents work in real-time
- [ ] **Web UI** — Browser-based project configuration
- [ ] **Git Integration** — Auto-commit with meaningful messages
- [ ] **Test Coverage** — Agents write unit tests
- [ ] **Multi-Repo** — Monorepo and microservice patterns

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the crew to test (`.\run.ps1`)
5. Submit a Pull Request

---

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [CrewAI](https://docs.crewai.com) — Multi-agent orchestration framework
- [LangChain DeepAgents](https://blog.langchain.dev) — Workflow tool inspiration
- [OpenAI](https://openai.com) & [Anthropic](https://anthropic.com) — LLM providers

---

<div align="center">

**Built with ❤️ and a lot of API costs**

*If this impressed you, imagine what we could build together.*

[⬆ Back to Top](#-autonomous-software-engineering-crew)

</div>