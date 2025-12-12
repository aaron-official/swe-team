import os
import json
import docker
import requests
from pathlib import Path
from typing import Type, Any, Dict, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

# ==============================================================================
# 1. DOCKER SHELL TOOL (The "Hands")
# ==============================================================================
# Why: Allows agents to execute shell commands, install npm/pip packages, 
# and run code in a safe, isolated environment that persists files.

class DockerShellInput(BaseModel):
    command: str = Field(..., description="The shell command to run (e.g., 'npm install axios', 'ls -la', 'python output/main.py').")

class DockerShellTool(BaseTool):
    name: str = "Docker Shell Execution"
    description: str = (
        "Executes shell commands in a persistent Docker container. "
        "The environment has Python, Node.js, and npm installed. "
        "Files created in the 'output' directory are strictly preserved. "
        "Use this to run code, install dependencies, or manage the file system."
    )
    args_schema: Type[BaseModel] = DockerShellInput

    # Configuration
    container_name: str = "autonomous_dev_env"
    image_name: str = "nikolaik/python-nodejs:latest"
    
    # Use pathlib for more reliable path calculation
    # Navigate from tools.py → tools/ → swe_team/ → src/ → swe_team/ (root) → output/
    _tools_file: Path = Path(__file__).resolve()
    _project_root: Path = _tools_file.parent.parent.parent.parent  # swe_team/
    mount_dir: str = str(_project_root / "output")  # swe_team/output

    def _get_docker_client(self):
        try:
            return docker.from_env()
        except docker.errors.DockerException:
            return None

    def _run(self, command: str) -> str:
        client = self._get_docker_client()
        if not client:
            return "ERROR: Docker is not running. Please start Docker Desktop."

        # 1. Prepare Workspace
        os.makedirs(self.mount_dir, exist_ok=True)

        # 2. Manage Container Lifecycle
        try:
            # Check if container exists
            container = client.containers.get(self.container_name)
            if container.status != 'running':
                container.start()
        except docker.errors.NotFound:
            # Create if missing (Only happens once)
            print(f"🛠️  Initializing Dev Environment ({self.image_name})...")
            print(f"📁 Mounting: {self.mount_dir} → /app")
            try:
                client.images.get(self.image_name)
            except docker.errors.ImageNotFound:
                print("⬇️  Pulling image (this may take a minute)...")
                client.images.pull(self.image_name)
            
            # Start persistent container with 'consistent' mount mode
            # On Windows, 'consistent' ensures files are synced immediately between host and container
            container = client.containers.run(
                self.image_name,
                command="tail -f /dev/null",  # Keep alive command
                name=self.container_name,
                detach=True,
                # Use Docker mount syntax for better Windows compatibility
                mounts=[
                    docker.types.Mount(
                        target="/app",
                        source=self.mount_dir,
                        type="bind",
                        read_only=False,
                        consistency="consistent"  # Force immediate sync on Windows
                    )
                ],
                working_dir="/app",
                auto_remove=False
            )
            print(f"✅ Container created with mount: {self.mount_dir} → /app")

        # 3. Execute Command
        try:
            # Wrapping in bash allows for pipes (|) and chains (&&)
            exec_result = container.exec_run(
                f"bash -c '{command}'", 
                workdir="/app"
            )
            
            output = exec_result.output.decode('utf-8').strip()
            exit_code = exec_result.exit_code

            if exit_code != 0:
                return f"❌ COMMAND FAILED (Exit Code {exit_code}):\n{output}"
            
            return f"✅ SUCCESS:\n{output}"

        except Exception as e:
            return f"SYSTEM ERROR: {str(e)}"

# ==============================================================================
# 2. MCP GATEWAY BRIDGE (The "Brain Connector")
# ==============================================================================
# Why: Connects to your Docker MCP Gateway to access external tools like 
# 'fetch' (web reader), 'memory' (knowledge graph), or 'context7'.

class MCPCallInput(BaseModel):
    tool_name: str = Field(..., description="The name of the MCP tool to call (e.g., 'fetch', 'memorize').")
    arguments: str = Field(..., description="A valid JSON string of arguments for the tool.")

class MCPBridgeTool(BaseTool):
    name: str = "MCP Gateway Bridge"
    description: str = (
        "Access external tools provided by the Docker MCP Gateway. "
        "Common tools: 'fetch' (get URL content), 'memorize' (save info), 'read_graph' (recall info). "
        "You MUST provide a valid JSON string for arguments."
    )
    args_schema: Type[BaseModel] = MCPCallInput
    
    # URL of your MCP Gateway (Server-Sent Events / HTTP Bridge)
    # Ensure your gateway is running on this port
    gateway_url: str = "http://localhost:8000/message" 

    def _run(self, tool_name: str, arguments: str) -> str:
        try:
            # 1. Parse JSON Arguments (Robustness Check)
            if isinstance(arguments, str):
                try:
                    args_dict = json.loads(arguments)
                except json.JSONDecodeError:
                    return "ERROR: 'arguments' must be a valid JSON string."
            else:
                args_dict = arguments

            # 2. Construct JSON-RPC Payload
            payload = {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": args_dict
                },
                "id": 1
            }

            # 3. Send Request to Gateway
            response = requests.post(self.gateway_url, json=payload, timeout=30)
            response.raise_for_status()
            
            # 4. Parse Response
            # Depending on your gateway implementation, the result might be wrapped differently.
            # This assumes a standard JSON-RPC response.
            data = response.json()
            
            if "error" in data:
                return f"MCP ERROR: {data['error'].get('message', 'Unknown error')}"
            
            result = data.get("result", {})
            # Content is often a list of text/image blocks
            content = result.get("content", [])
            
            # Convert content list to string for the Agent
            text_output = ""
            for item in content:
                if item.get("type") == "text":
                    text_output += item.get("text", "") + "\n"
            
            return text_output.strip() if text_output else "Success (No content returned)"

        except requests.exceptions.ConnectionError:
            return "CONNECTION ERROR: Could not reach Docker MCP Gateway at localhost:8000. Is it running?"
        except Exception as e:
            return f"SYSTEM ERROR: {str(e)}"

# ==============================================================================
# 3. SERPER SEARCH WRAPPER (The "Eyes")
# ==============================================================================
# Why: Standard SerperDevTool is great, but sometimes we want to force it 
# to return JUST links so the MCP 'fetch' tool can consume them easily.

from crewai_tools import SerperDevTool

class SmartSearchInput(BaseModel):
    query: str = Field(..., description="The search query.")

class SmartSearchTool(SerperDevTool):
    name: str = "Google Search (Serper)"
    description: str = (
        "Search the web for documentation, libraries, or real-time data. "
        "Use this to find URLs that you can then feed into the 'fetch' MCP tool."
    )
    args_schema: Type[BaseModel] = SmartSearchInput

    def _run(self, query: str) -> str:
        # We use the parent class's run method but could add post-processing here
        # to filter for specific domains (like pypi.org or npmjs.com) if needed.
        try:
            return super()._run(search_query=query)
        except Exception as e:
            return f"SEARCH ERROR: {str(e)}"