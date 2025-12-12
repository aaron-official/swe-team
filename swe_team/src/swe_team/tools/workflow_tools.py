"""
Workflow Tools - To-Do List, Progress Reporter, and Validation Checkpoints

These tools help agents coordinate work, track progress, and validate dependencies.
Inspired by DeepAgents' strategic planning concepts.
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Type, Optional, List, Dict, Any, ClassVar
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


# ==============================================================================
# SHARED STATE
# ==============================================================================

def get_output_dir() -> Path:
    """Get the output directory path."""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent.parent / "output"


def get_state_file() -> Path:
    """Get the workflow state file path."""
    return get_output_dir() / ".workflow_state.json"


def load_state() -> Dict[str, Any]:
    """Load workflow state from file."""
    state_file = get_state_file()
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    
    # Default state structure
    return {
        "todo": [],
        "done": [],
        "progress": {},
        "files": {},
        "notes": [],
        "last_updated": None
    }


def save_state(state: Dict[str, Any]) -> None:
    """Save workflow state to file."""
    state["last_updated"] = datetime.now().isoformat()
    state_file = get_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


# ==============================================================================
# 1. TO-DO LIST TOOL
# ==============================================================================

class TodoInput(BaseModel):
    """Input for To-Do operations."""
    action: str = Field(
        ..., 
        description="Action: 'add', 'complete', 'list', or 'clear'"
    )
    item: Optional[str] = Field(
        None, 
        description="Task description (required for 'add' and 'complete')"
    )
    priority: Optional[str] = Field(
        "medium",
        description="Priority: 'high', 'medium', 'low' (for 'add' action)"
    )


class TodoListTool(BaseTool):
    """
    Manage a shared to-do list for the crew.
    
    Agents can add tasks, mark them complete, and see what's pending.
    This helps coordinate work and track progress across the team.
    """
    
    name: str = "To-Do List"
    description: str = (
        "Manage the crew's shared to-do list. "
        "Actions: 'add' (add a task), 'complete' (mark done), 'list' (show all), 'clear' (remove all). "
        "Use this to track what needs to be done and what's finished."
    )
    args_schema: Type[BaseModel] = TodoInput
    
    def _run(self, action: str, item: Optional[str] = None, priority: str = "medium") -> str:
        state = load_state()
        
        if action == "add":
            if not item:
                return "Error: 'item' is required for 'add' action"
            
            task = {
                "id": len(state["todo"]) + len(state["done"]) + 1,
                "task": item,
                "priority": priority,
                "added_at": datetime.now().isoformat(),
                "status": "pending"
            }
            state["todo"].append(task)
            save_state(state)
            return f"✅ Added to-do #{task['id']}: {item} [{priority}]"
        
        elif action == "complete":
            if not item:
                return "Error: 'item' description is required to mark complete"
            
            # Find matching task
            for i, task in enumerate(state["todo"]):
                if item.lower() in task["task"].lower():
                    task["status"] = "done"
                    task["completed_at"] = datetime.now().isoformat()
                    state["done"].append(task)
                    state["todo"].pop(i)
                    save_state(state)
                    return f"✅ Completed: {task['task']}"
            
            return f"⚠️ No pending task matching '{item}' found"
        
        elif action == "list":
            result = "📋 **To-Do List**\n\n"
            
            if state["todo"]:
                result += "**Pending:**\n"
                for task in state["todo"]:
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(task["priority"], "⚪")
                    result += f"  {priority_icon} #{task['id']}: {task['task']}\n"
            else:
                result += "**Pending:** None\n"
            
            result += "\n"
            
            if state["done"]:
                result += f"**Completed ({len(state['done'])}):**\n"
                for task in state["done"][-5:]:  # Show last 5 completed
                    result += f"  ✅ #{task['id']}: {task['task']}\n"
                if len(state["done"]) > 5:
                    result += f"  ... and {len(state['done']) - 5} more\n"
            else:
                result += "**Completed:** None yet\n"
            
            return result
        
        elif action == "clear":
            state["todo"] = []
            state["done"] = []
            save_state(state)
            return "🗑️ To-do list cleared"
        
        else:
            return f"Unknown action: {action}. Use 'add', 'complete', 'list', or 'clear'."


# ==============================================================================
# 2. PROGRESS REPORTER TOOL
# ==============================================================================

class ProgressInput(BaseModel):
    """Input for Progress operations."""
    action: str = Field(
        ..., 
        description="Action: 'update', 'get', or 'summary'"
    )
    task_name: Optional[str] = Field(
        None, 
        description="Task name (e.g., 'pm_task', 'cto_task')"
    )
    status: Optional[str] = Field(
        None,
        description="Status: 'pending', 'running', 'complete', 'failed', 'blocked'"
    )
    progress_percent: Optional[int] = Field(
        None,
        description="Progress percentage (0-100)"
    )
    output_file: Optional[str] = Field(
        None,
        description="Output file created by this task"
    )
    notes: Optional[str] = Field(
        None,
        description="Notes about the task progress"
    )


class ProgressReporterTool(BaseTool):
    """
    Track and report progress of crew tasks.
    
    Helps monitor which tasks are complete, running, or blocked.
    Great for debugging and understanding crew execution flow.
    """
    
    name: str = "Progress Reporter"
    description: str = (
        "Track task progress across the crew. "
        "Actions: 'update' (set task status), 'get' (get task status), 'summary' (overview of all tasks). "
        "Use to report your progress and check on other tasks."
    )
    args_schema: Type[BaseModel] = ProgressInput
    
    # Expected task order
    TASK_ORDER: ClassVar[List[str]] = [
        "pm_task", "cto_task", "devops_task", "design_task",
        "backend_task", "frontend_task", "review_task", "test_task"
    ]
    
    def _run(
        self, 
        action: str, 
        task_name: Optional[str] = None,
        status: Optional[str] = None,
        progress_percent: Optional[int] = None,
        output_file: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        state = load_state()
        
        if action == "update":
            if not task_name:
                return "Error: 'task_name' is required for 'update' action"
            
            task_progress = state["progress"].get(task_name, {})
            
            if status:
                task_progress["status"] = status
            if progress_percent is not None:
                task_progress["progress_percent"] = progress_percent
            if output_file:
                task_progress["output_file"] = output_file
                # Also track in files registry
                state["files"][output_file] = {
                    "created_by": task_name,
                    "status": "created",
                    "created_at": datetime.now().isoformat()
                }
            if notes:
                task_progress["notes"] = notes
            
            task_progress["updated_at"] = datetime.now().isoformat()
            state["progress"][task_name] = task_progress
            save_state(state)
            
            return f"📊 Updated {task_name}: {status or 'updated'}"
        
        elif action == "get":
            if not task_name:
                return "Error: 'task_name' is required for 'get' action"
            
            task_progress = state["progress"].get(task_name)
            if not task_progress:
                return f"No progress recorded for {task_name} yet"
            
            result = f"📊 **{task_name}**\n"
            result += f"  Status: {task_progress.get('status', 'unknown')}\n"
            if task_progress.get('progress_percent'):
                result += f"  Progress: {task_progress['progress_percent']}%\n"
            if task_progress.get('output_file'):
                result += f"  Output: {task_progress['output_file']}\n"
            if task_progress.get('notes'):
                result += f"  Notes: {task_progress['notes']}\n"
            
            return result
        
        elif action == "summary":
            result = "📊 **Crew Progress Summary**\n\n"
            
            for task in self.TASK_ORDER:
                task_progress = state["progress"].get(task, {})
                status = task_progress.get("status", "pending")
                
                icon = {
                    "complete": "✅",
                    "running": "🔄",
                    "failed": "❌",
                    "blocked": "🚫",
                    "pending": "⏳"
                }.get(status, "❓")
                
                output = task_progress.get("output_file", "-")
                result += f"{icon} **{task}**: {status}"
                if output != "-":
                    result += f" → {output}"
                result += "\n"
            
            # File registry
            if state["files"]:
                result += "\n📁 **Created Files:**\n"
                for filename, info in state["files"].items():
                    result += f"  - {filename} (by {info.get('created_by', 'unknown')})\n"
            
            return result
        
        else:
            return f"Unknown action: {action}. Use 'update', 'get', or 'summary'."


# ==============================================================================
# 3. VALIDATION CHECKPOINT TOOL
# ==============================================================================

class ValidationInput(BaseModel):
    """Input for Validation operations."""
    action: str = Field(
        ..., 
        description="Action: 'check_file', 'check_task', 'check_ready', 'register_file'"
    )
    file_name: Optional[str] = Field(
        None, 
        description="File name to check (e.g., 'lockfile.txt')"
    )
    task_name: Optional[str] = Field(
        None, 
        description="Task name to check status"
    )
    required_files: Optional[List[str]] = Field(
        None,
        description="List of files that must exist before proceeding"
    )


class ValidationCheckpointTool(BaseTool):
    """
    Validate that dependencies are met before proceeding.
    
    Checks if required files exist and if prerequisite tasks are complete.
    Prevents "file not found" errors by validating before reading.
    """
    
    name: str = "Validation Checkpoint"
    description: str = (
        "Validate dependencies before proceeding. "
        "Actions: 'check_file' (verify file exists), 'check_task' (verify task complete), "
        "'check_ready' (verify multiple dependencies), 'register_file' (mark file as created). "
        "Use BEFORE trying to read files to avoid errors."
    )
    args_schema: Type[BaseModel] = ValidationInput
    
    # Task dependencies map
    TASK_DEPENDENCIES: ClassVar[Dict[str, List[str]]] = {
        "pm_task": [],
        "cto_task": ["pm_task"],
        "devops_task": ["cto_task"],
        "design_task": ["pm_task", "devops_task"],
        "backend_task": ["design_task"],
        "frontend_task": ["design_task", "backend_task"],
        "review_task": ["backend_task", "frontend_task"],
        "test_task": ["backend_task", "frontend_task"]
    }
    
    # Expected output files per task
    TASK_OUTPUTS: ClassVar[Dict[str, str]] = {
        "pm_task": "requirements.md",
        "cto_task": "tech_stack.md",
        "devops_task": "lockfile.txt",
        "design_task": "architecture.md",
        "backend_task": "backend_app.py",
        "frontend_task": "frontend_app.py",
        "review_task": "review_report.md",
        "test_task": "test_report.md"
    }
    
    def _check_file_exists(self, file_name: str) -> bool:
        """Check if a file exists in the output directory."""
        output_dir = get_output_dir()
        file_path = output_dir / file_name
        return file_path.exists()
    
    def _run(
        self, 
        action: str, 
        file_name: Optional[str] = None,
        task_name: Optional[str] = None,
        required_files: Optional[List[str]] = None
    ) -> str:
        state = load_state()
        output_dir = get_output_dir()
        
        if action == "check_file":
            if not file_name:
                return "Error: 'file_name' is required for 'check_file' action"
            
            exists = self._check_file_exists(file_name)
            
            if exists:
                file_path = output_dir / file_name
                size = file_path.stat().st_size
                return f"✅ File exists: {file_name} ({size} bytes)"
            else:
                # Find which task creates this file
                creator_task = None
                for task, output in self.TASK_OUTPUTS.items():
                    if output == file_name:
                        creator_task = task
                        break
                
                msg = f"❌ File not found: {file_name}\n"
                if creator_task:
                    task_status = state["progress"].get(creator_task, {}).get("status", "pending")
                    msg += f"   Created by: {creator_task} (status: {task_status})\n"
                    msg += f"   Wait for {creator_task} to complete before reading this file."
                else:
                    msg += "   This file is not in the expected task outputs."
                
                return msg
        
        elif action == "check_task":
            if not task_name:
                return "Error: 'task_name' is required for 'check_task' action"
            
            task_status = state["progress"].get(task_name, {}).get("status", "pending")
            
            if task_status == "complete":
                output = self.TASK_OUTPUTS.get(task_name, "unknown")
                return f"✅ {task_name} is complete (output: {output})"
            else:
                return f"⏳ {task_name} is {task_status}. Dependencies not yet met."
        
        elif action == "check_ready":
            if not task_name:
                return "Error: 'task_name' is required for 'check_ready' action"
            
            dependencies = self.TASK_DEPENDENCIES.get(task_name, [])
            
            if not dependencies:
                return f"✅ {task_name} has no dependencies. Ready to proceed."
            
            missing = []
            complete = []
            
            for dep_task in dependencies:
                dep_status = state["progress"].get(dep_task, {}).get("status", "pending")
                dep_output = self.TASK_OUTPUTS.get(dep_task)
                
                if dep_status == "complete" and (not dep_output or self._check_file_exists(dep_output)):
                    complete.append(dep_task)
                else:
                    missing.append(dep_task)
            
            if not missing:
                return f"✅ {task_name} is ready. All dependencies complete: {', '.join(complete)}"
            else:
                result = f"🚫 {task_name} is BLOCKED\n"
                result += f"   Waiting for: {', '.join(missing)}\n"
                result += f"   Complete: {', '.join(complete) if complete else 'none'}"
                return result
        
        elif action == "register_file":
            if not file_name:
                return "Error: 'file_name' is required for 'register_file' action"
            
            state["files"][file_name] = {
                "created_by": task_name or "unknown",
                "status": "created",
                "created_at": datetime.now().isoformat()
            }
            save_state(state)
            
            return f"📝 Registered file: {file_name}"
        
        else:
            return f"Unknown action: {action}. Use 'check_file', 'check_task', 'check_ready', or 'register_file'."


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def get_workflow_tools(base_dir: Optional[str] = None) -> List[BaseTool]:
    """
    Get all workflow tools as a list.
    
    Returns:
        list: [TodoListTool, ProgressReporterTool, ValidationCheckpointTool]
    """
    return [
        TodoListTool(),
        ProgressReporterTool(),
        ValidationCheckpointTool()
    ]


def reset_workflow_state() -> None:
    """Reset the workflow state file (useful for new runs)."""
    state_file = get_state_file()
    if state_file.exists():
        state_file.unlink()
    
    # Create fresh state
    save_state({
        "todo": [],
        "done": [],
        "progress": {},
        "files": {},
        "notes": [],
        "last_updated": None
    })


# ==============================================================================
# TEST
# ==============================================================================

if __name__ == "__main__":
    print("Testing Workflow Tools...\n")
    
    # Reset state for testing
    reset_workflow_state()
    
    # Test Todo List
    print("=== Todo List ===")
    todo = TodoListTool()
    print(todo._run("add", "Create requirements document", "high"))
    print(todo._run("add", "Define tech stack", "high"))
    print(todo._run("add", "Setup Docker environment", "medium"))
    print(todo._run("list"))
    print(todo._run("complete", "requirements"))
    print(todo._run("list"))
    
    # Test Progress Reporter
    print("\n=== Progress Reporter ===")
    progress = ProgressReporterTool()
    print(progress._run("update", "pm_task", "complete", 100, "requirements.md", "3 user stories defined"))
    print(progress._run("update", "cto_task", "running", 50))
    print(progress._run("summary"))
    
    # Test Validation Checkpoint
    print("\n=== Validation Checkpoint ===")
    validator = ValidationCheckpointTool()
    print(validator._run("check_ready", task_name="devops_task"))
    print(validator._run("check_file", file_name="requirements.md"))
    print(validator._run("check_file", file_name="lockfile.txt"))
    
    print("\n✅ All tests complete!")
