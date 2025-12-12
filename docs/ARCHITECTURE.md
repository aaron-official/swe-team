# 🔬 Technical Architecture

Deep dive into the system internals of the Autonomous Software Engineering Crew.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                     │
│                    "Build a task tracker with..."                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CREWAI FRAMEWORK                                  │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    HIERARCHICAL MANAGER (GPT-4o)                      │  │
│  │  • Delegates tasks to specialized agents                             │  │
│  │  • Monitors progress via workflow tools                              │  │
│  │  • Routes failures to responsible agents                             │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐          ┌─────────────┐          ┌─────────────┐          │
│  │   Agent 1   │◄────────►│   Agent 2   │◄────────►│   Agent N   │          │
│  │  (+ Tools)  │  Context │  (+ Tools)  │  Context │  (+ Tools)  │          │
│  └─────────────┘          └─────────────┘          └─────────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
           │ DockerShell  │  │  MCP Gateway │  │  Web Search  │
           │    Tool      │  │    Tools     │  │    Tool      │
           └──────────────┘  └──────────────┘  └──────────────┘
                    │                 │                 │
                    ▼                 ▼                 ▼
           ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
           │   Docker     │  │   Memory     │  │   Serper     │
           │  Container   │  │   Server     │  │     API      │
           └──────────────┘  └──────────────┘  └──────────────┘
```

## Core Components

### 1. EngineeringTeam Class (`crew.py`)

The central orchestrator that defines agents, tools, and workflow.

```python
@CrewBase
class EngineeringTeam:
    """Autonomous Engineering Team Crew"""
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'
    
    # Tool Groups (organized by capability)
    def tools_docker(self) -> list
    def tools_file_operations(self) -> list
    def tools_research(self) -> list
    def tools_workflow(self) -> list
    def tools_mcp(self) -> list
    
    # 8 Agent Definitions
    @agent
    def product_manager(self) -> Agent
    @agent
    def cto(self) -> Agent
    # ... etc
    
    # 8 Task Definitions
    @task
    def pm_task(self) -> Task
    @task
    def cto_task(self) -> Task
    # ... etc
    
    # Crew Assembly
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm="openai/gpt-4o",
            planning=False  # Disabled to avoid JSON parsing issues
        )
```

### 2. Task Flow & Dependencies

Tasks are defined in YAML with explicit dependencies:

```yaml
# tasks.yaml structure
pm_task:
  description: "Transform user request into PRD..."
  agent: product_manager
  output_file: output/requirements.md

cto_task:
  description: "Select technology stack..."
  agent: cto
  context: [pm_task]  # ← Depends on PM's output
  output_file: output/tech_stack.md

devops_task:
  context: [cto_task]  # ← Depends on CTO's decisions
  output_file: output/lockfile.txt

design_task:
  context: [pm_task, devops_task]  # ← Multiple dependencies
  output_file: output/architecture.md
```

### 3. Tool Architecture

#### DockerShellTool

Executes commands in an isolated, persistent container:

```python
class DockerShellTool(BaseTool):
    container_name = "autonomous_dev_env"
    image_name = "nikolaik/python-nodejs:latest"
    
    def _run(self, command: str) -> str:
        # Container lifecycle management
        try:
            container = client.containers.get(self.container_name)
        except docker.errors.NotFound:
            container = client.containers.run(
                self.image_name,
                mounts=[Mount(
                    target="/app",
                    source=self.mount_dir,
                    type="bind",
                    consistency="consistent"  # Critical for Windows
                )],
                working_dir="/app",
                detach=True
            )
        
        # Execute command
        result = container.exec_run(f"bash -c '{command}'")
        return result.output.decode('utf-8')
```

#### Workflow Tools (DeepAgents-Inspired)

```python
class TodoListTool(BaseTool):
    """Shared to-do list for agent coordination."""
    
    def _run(self, action: str, item: str = None) -> str:
        state = load_state()  # From .workflow_state.json
        
        if action == "add":
            state["todo"].append({"task": item, ...})
        elif action == "complete":
            # Move from todo to done
        elif action == "list":
            # Return formatted list
            
        save_state(state)

class ValidationCheckpointTool(BaseTool):
    """Verify dependencies before proceeding."""
    
    TASK_OUTPUTS = {
        "pm_task": "requirements.md",
        "devops_task": "lockfile.txt",
        # ...
    }
    
    def _run(self, action: str, file_name: str = None) -> str:
        if action == "check_file":
            if not Path(file_name).exists():
                creator = self._find_creator(file_name)
                return f"❌ File not found. Created by: {creator}"
```

### 4. Multi-Model Strategy

Different models for different purposes:

| Model | Agents | Reasoning |
|-------|--------|-----------|
| **GPT-4o** | PM, CTO, Architect, Reviewer | Strong reasoning, planning, analysis |
| **Claude Sonnet** | DevOps, Backend, Frontend, Tester | Precise code generation, execution |

Configured in `agents.yaml`:

```yaml
product_manager:
  role: "Technical Product Manager"
  llm: openai/gpt-4o
  max_iter: 5

backend_engineer:
  role: "Senior Python Developer"
  llm: anthropic/claude-sonnet-4-20250514
  max_iter: 10
```

## Data Flow

### Phase 1: Discovery

```
User Requirements
      │
      ▼
┌─────────────┐      ┌─────────────┐
│  PM Agent   │ ──►  │   CTO Agent │
│  Creates:   │      │   Creates:  │
│  - PRD      │      │  - Stack    │
│  - Stories  │      │  - Research │
└─────────────┘      └─────────────┘
      │                    │
      ▼                    ▼
 requirements.md      tech_stack.md
```

### Phase 2: Environment Setup

```
tech_stack.md
      │
      ▼
┌─────────────────────────────────────────────┐
│              DevOps Agent                   │
│  1. pip install [packages from tech_stack]  │
│  2. pip freeze > lockfile.txt               │
│  3. Verify all imports work                 │
└─────────────────────────────────────────────┘
      │
      ▼
 lockfile.txt (ACTUAL installed versions)
```

### Phase 3: Design

```
requirements.md + lockfile.txt
            │
            ▼
┌─────────────────────────────────────────────┐
│           Engineering Lead                  │
│  Designs architecture for:                  │
│  - FastAPI 0.115.0 (not "latest")          │
│  - Pydantic 2.6.2 (use v2 patterns)        │
│  - Specific API contracts                   │
└─────────────────────────────────────────────┘
            │
            ▼
      architecture.md
```

### Phase 4: Implementation

```
architecture.md
      │
      ├──────────────────────┐
      ▼                      ▼
┌─────────────┐      ┌─────────────┐
│  Backend    │      │  Frontend   │
│  Engineer   │      │  Engineer   │
└─────────────┘      └─────────────┘
      │                      │
      ▼                      ▼
backend_app.py        frontend_app.py
```

### Phase 5: Verification

```
backend_app.py + frontend_app.py
            │
            ├──────────────────────┐
            ▼                      ▼
┌─────────────────────┐   ┌─────────────────────┐
│   Code Reviewer     │   │   Test Engineer     │
│   - Security audit  │   │   - Execute in      │
│   - Spec compliance │   │     Docker          │
│   - Best practices  │   │   - Verify behavior │
└─────────────────────┘   └─────────────────────┘
            │                      │
            ▼                      ▼
     review_report.md       test_report.md
```

## Error Recovery

### Self-Correction Protocol

```python
# In manager's decision loop
if test_report.status == "FAILED":
    error = parse_error(test_report.output)
    
    if "ModuleNotFoundError" in error:
        delegate_to("devops_engineer", "Install missing module")
    elif "SyntaxError" in error:
        delegate_to("backend_engineer", "Fix syntax error")
    elif "500 Internal Server Error" in error:
        delegate_to("backend_engineer", "Debug runtime error")
    
    retry_count += 1
    if retry_count > MAX_RETRIES:
        escalate_to_user()
```

### File Validation

Before any file read, agents can validate:

```python
# Agent's thought process
result = validation_tool("check_file", "lockfile.txt")

if "❌ File not found" in result:
    # Wait or request dependency task completion
else:
    # Safe to proceed with file read
```

## Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUTF8` | `1` | Forces UTF-8 encoding |
| `OPENAI_API_KEY` | — | Required for GPT models |
| `ANTHROPIC_API_KEY` | — | Required for Claude |
| `SERPER_API_KEY` | — | Web search capability |
| `PORT` | `8080` | Backend server port |
| `FRONTEND_PORT` | `3000` | Frontend server port |

### Key Files

| File | Purpose |
|------|---------|
| `instructions.py` | User project definition |
| `agents.yaml` | Agent personalities and models |
| `tasks.yaml` | Task descriptions and dependencies |
| `.workflow_state.json` | Runtime coordination state |

## Performance Tuning

### Token Optimization

```yaml
# agents.yaml
backend_engineer:
  max_iter: 10        # Max reasoning loops
  max_tokens: 4096    # Response limit
  temperature: 0.3    # Lower = more deterministic
```

### Container Reuse

The Docker container persists between commands, so:
- Installed packages remain available
- File system state is preserved
- No cold-start penalty after first command

### Parallel Execution

Some tasks can run in parallel (if no dependencies):
```yaml
review_task:
  context: [backend_task, frontend_task]

test_task:
  context: [backend_task, frontend_task]
  # Both review and test can start simultaneously
```
