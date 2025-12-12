"""
==============================================================================
🤖 AUTONOMOUS SOFTWARE ENGINEERING CREW - Orchestration Layer
==============================================================================
Version: 2.0.0 (Optimized with CrewAI Best Practices)
Last Updated: 2025-12-11

This module defines the CrewAI crew that orchestrates a team of 8 specialized
AI agents to autonomously build software applications from high-level requirements.

ARCHITECTURE:
- Hierarchical Process: A GPT-4o Manager supervises all agents
- Memory Enabled: Crew remembers past interactions and failures
- Planning Mode: Strategic thinking before execution
- Rate Limiting: Prevents API throttling

PHASES:
1. Discovery & Strategy (PM, CTO)
2. Environment Setup (DevOps)
3. Architecture & Design (Engineering Lead)
4. Implementation (Backend & Frontend Engineers)
5. Quality Assurance (Code Reviewer, Test Engineer)
==============================================================================
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import (
    SerperDevTool,
    ScrapeWebsiteTool,
    FileReadTool,
    DirectoryReadTool,
    FileWriterTool
)

# Import custom tools for Docker execution and MCP connectivity
from swe_team.tools.tools import DockerShellTool, SmartSearchTool
from swe_team.tools.docker_mcp import DockerMCPAdapter
# Import UTF-8 file tools as fallback for Windows encoding issues
from swe_team.tools.utf8_file_tools import UTF8FileReadTool, UTF8FileWriteTool, ListOutputFilesTool
# Import workflow tools for coordination (inspired by DeepAgents concepts)
from swe_team.tools.workflow_tools import TodoListTool, ProgressReporterTool, ValidationCheckpointTool


@CrewBase
class EngineeringTeam:
    """
    Autonomous Engineering Team Crew
    
    This crew orchestrates 8 specialized AI agents that collaborate to:
    1. Transform vague requirements into detailed PRDs
    2. Select and validate technology stacks
    3. Set up real Docker development environments
    4. Design comprehensive architectures
    5. Implement backend and frontend code
    6. Review code for security and quality
    7. Test applications in runtime
    
    The crew uses a hierarchical process with a GPT-4o manager that
    supervises all agents and handles task delegation and error recovery.
    """
    
    # Configuration file paths (relative to this file's directory)
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # ==========================================================================
    # TOOL CONFIGURATIONS
    # ==========================================================================
    # Tools are grouped by purpose and assigned to agents based on their roles.
    # This ensures each agent has exactly the capabilities they need.
    
    def tools_docker(self) -> list:
        """Docker execution tools for running commands in containers."""
        return [DockerShellTool()]
    
    def tools_file_operations(self) -> list:
        """
        File system tools for reading and exploring files.
        
        Includes both default CrewAI tools and UTF-8 fallback tools:
        - FileReadTool: Standard file reader (uses system encoding + PYTHONUTF8)
        - UTF8FileReadTool: Explicit UTF-8 reader (fallback for encoding issues)
        - UTF8FileWriteTool: Explicit UTF-8 writer (fallback for encoding issues)
        - DirectoryReadTool: Directory listing
        
        All tools are configured to read from swe_team/output/ directory.
        Agents can use UTF-8 tools if they encounter encoding errors with default tools.
        """
        # Get the absolute path to swe_team/output/ directory
        from pathlib import Path
        output_dir = str(Path(__file__).parent.parent.parent / "output")
        
        return [
            ListOutputFilesTool(base_dir=output_dir),     # Check what files exist first!
            FileReadTool(directory=output_dir),           # Primary - configured for output dir
            DirectoryReadTool(directory=output_dir),      # Directory listing for output dir
            UTF8FileReadTool(base_dir=output_dir),        # Fallback - explicit UTF-8 read
            UTF8FileWriteTool(base_dir=output_dir)        # Fallback - explicit UTF-8 write
        ]
    
    def tools_research(self) -> list:
        """Web research tools for searching and scraping documentation."""
        return [SmartSearchTool(), ScrapeWebsiteTool()]
    
    def tools_workflow(self) -> list:
        """
        Workflow coordination tools inspired by DeepAgents concepts.
        
        Provides:
        - TodoListTool: Track tasks as done/pending
        - ProgressReporterTool: Monitor task progress across the crew
        - ValidationCheckpointTool: Check if dependencies are met before proceeding
        
        These tools help agents coordinate, avoid "file not found" errors,
        and maintain awareness of overall progress.
        """
        return [
            TodoListTool(),
            ProgressReporterTool(),
            ValidationCheckpointTool()
        ]
    
    def tools_mcp(self) -> list:
        """
        MCP Gateway tools for memory and external context.
        
        Connects to Docker MCP Gateway at http://localhost:8000/mcp
        using Streamable HTTP transport.
        
        Returns filesystem, memory, playwright, and other Docker MCP tools.
        """
        try:
            adapter = DockerMCPAdapter(url="http://localhost:8000/mcp")
            adapter.connect()
            return adapter.get_tools()
        except Exception as e:
            print(f"⚠️  MCP tools unavailable: {e}")
            return []  # Return empty list if MCP is not available
    
    def tools_implementation(self) -> list:
        """
        Full toolset for agents that implement code.
        Uses Docker Shell for command execution, not MCP.
        """
        return (
            self.tools_docker() +  # Primary: Execute commands in Docker
            self.tools_file_operations()  # Secondary: Read specs/architecture
        )

    # ==========================================================================
    # AGENT DEFINITIONS
    # ==========================================================================
    # Each agent is configured via YAML and enhanced with specific tools.
    # The YAML defines role, goal, backstory, and LLM selection.
    # Tools are assigned here based on what each agent needs to do.
    
    @agent
    def product_manager(self) -> Agent:
        """
        Technical Product Manager - Transforms vague ideas into detailed PRDs.
        
        Tools: MCPBridgeTool for persisting project context to knowledge graph
        Model: GPT-4o (strategic thinking, documentation)
        """
        return Agent(
            config=self.agents_config['product_manager'],
            tools=self.tools_file_operations() + self.tools_workflow() + self.tools_mcp(),
        )

    @agent
    def cto(self) -> Agent:
        """
        Chief Technology Officer - Selects and validates technology stacks.
        
        Tools: 
        - Web Search (SerperDev) - General deprecation checks
        - MCP Context7 - Official library documentation
        - MCP Tavily - Deep web research and crawling
        Model: gpt-5-mini (strategic, research-oriented)
        """
        return Agent(
            config=self.agents_config['cto'],
            tools=self.tools_research() + self.tools_file_operations() + self.tools_workflow() + self.tools_mcp(),
        )

    @agent
    def devops_engineer(self) -> Agent:
        """
        DevOps Engineer - Sets up Docker environments and installs dependencies.
        
        Tools: Docker for execution, File tools for reading specs
        Model: Claude Sonnet 4 (execution-focused, detail-oriented)
        """
        return Agent(
            config=self.agents_config['devops_engineer'],
            tools=self.tools_docker() + self.tools_file_operations() + self.tools_workflow(),
        )

    @agent
    def engineering_lead(self) -> Agent:
        """
        Engineering Lead - Designs comprehensive software architectures.
        
        Tools: File tools for reading requirements and exploring structure
        Model: GPT-4o (architectural thinking, system design)
        """
        return Agent(
            config=self.agents_config['engineering_lead'],
            tools=self.tools_file_operations() + self.tools_workflow(),
        )

    @agent
    def backend_engineer(self) -> Agent:
        """
        Backend Engineer - Implements Python backend code.
        
        Tools: Full implementation toolset (Docker, Files, MCP)
        Model: Claude Sonnet 4 (code generation, syntax precision)
        """
        return Agent(
            config=self.agents_config['backend_engineer'],
            tools=self.tools_implementation(),
        )

    @agent
    def frontend_engineer(self) -> Agent:
        """
        Frontend Engineer - Implements UI/UX code.
        
        Tools: Docker for verification, File tools for reading specs
        Model: Claude Sonnet 4 (code generation, UI implementation)
        """
        return Agent(
            config=self.agents_config['frontend_engineer'],
            tools=self.tools_docker() + self.tools_file_operations() + self.tools_workflow(),
        )
    
    @agent
    def code_reviewer(self) -> Agent:
        """
        Code Reviewer - Audits code for security and correctness.
        
        Tools: File tools for reading and comparing code
        Model: GPT-4o (critical analysis, security awareness)
        """
        return Agent(
            config=self.agents_config['code_reviewer'],
            tools=self.tools_file_operations() + self.tools_workflow(),
        )

    @agent
    def test_engineer(self) -> Agent:
        """
        Test Engineer - Executes and validates applications in Docker.
        
        Tools: Docker for execution, File tools for reading code
        Model: Claude Sonnet 4 (runtime testing, diagnostics)
        """
        return Agent(
            config=self.agents_config['test_engineer'],
            tools=self.tools_docker() + self.tools_file_operations() + self.tools_workflow(),
        )

    # ==========================================================================
    # TASK DEFINITIONS
    # ==========================================================================
    # Tasks are defined in config/tasks.yaml with detailed descriptions,
    # expected outputs, context dependencies, and output files.
    # The decorator maps YAML config to Task objects automatically.
    
    @task
    def pm_task(self) -> Task:
        """Phase 1: Product Requirements Document generation."""
        return Task(config=self.tasks_config['pm_task'])
    
    @task
    def cto_task(self) -> Task:
        """Phase 1: Technology stack selection and validation."""
        return Task(config=self.tasks_config['cto_task'])
    
    @task
    def devops_task(self) -> Task:
        """Phase 2: Docker environment setup and dependency installation."""
        return Task(config=self.tasks_config['devops_task'])
    
    @task
    def design_task(self) -> Task:
        """Phase 2: Software architecture design."""
        return Task(config=self.tasks_config['design_task'])
    
    @task
    def backend_task(self) -> Task:
        """Phase 3: Backend implementation."""
        return Task(config=self.tasks_config['backend_task'])
    
    @task
    def frontend_task(self) -> Task:
        """Phase 3: Frontend/UI implementation."""
        return Task(config=self.tasks_config['frontend_task'])
    
    @task
    def review_task(self) -> Task:
        """Phase 4: Code review and security audit."""
        return Task(config=self.tasks_config['review_task'])
    
    @task
    def test_task(self) -> Task:
        """Phase 4: Runtime testing and validation."""
        return Task(config=self.tasks_config['test_task'])
    
    @task
    def fix_task(self) -> Task:
        """Phase 4B: Fix bugs identified by tests and re-verify."""
        return Task(config=self.tasks_config['fix_task'])

    # ==========================================================================
    # CREW CONFIGURATION
    # ==========================================================================
    
    @crew
    def crew(self) -> Crew:
        """
        Configure and return the autonomous engineering crew.
        
        PROCESS: Hierarchical
        - A GPT-5-mini Manager supervises all agents
        - Manager delegates tasks based on agent capabilities
        - Manager handles failures and reassigns work
        - Manager ensures proper task sequencing
        
        MEMORY: Enabled
        - Crew remembers past interactions
        - Learns from failures and successes
        - Maintains context across task executions
        
        PLANNING: Enabled
        - Strategic "thinking" step before execution
        - Helps with complex multi-step tasks
        
        RATE LIMITING: 100 RPM
        - Prevents API throttling
        - Ensures stable execution
        """
        return Crew(
            agents=self.agents,  # Auto-populated by @agent decorators
            tasks=self.tasks,    # Auto-populated by @task decorators
            
            # Hierarchical process with intelligent manager
            process=Process.hierarchical,
            manager_llm="gpt-5-mini",
            
            # Disable built-in memory to avoid token limit errors with embeddings
            # Use MCP memory tool for explicit saves when needed
            memory=False,
            
            # Disable planning to avoid JSON parsing issues with complex multi-line requirements
            # The hierarchical manager handles task delegation without needing upfront planning
            planning=False,
            planning_llm="gpt-5-mini",  # Commented out since planning is disabled
            
            # Verbose output for debugging and monitoring
            verbose=True,
            
            # Rate limiting to prevent API throttling
            max_rpm=100,
            
            # Additional configuration for robustness
            full_output=True,           # Return complete execution details
            share_crew=False,           # Don't share this crew publicly
            step_callback=None,         # Optional: Add step-by-step callbacks
            task_callback=None,         # Optional: Add task completion callbacks
        )