"""
Custom File Tools with UTF-8 Encoding
Provides reliable file read/write operations for CrewAI agents on Windows.

These tools bypass Windows' default cp1252 encoding by explicitly using UTF-8,
preventing 'charmap codec can't decode byte' errors.
"""

import os
from pathlib import Path
from typing import Type, Optional
from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class FileReadInput(BaseModel):
    """Input schema for FileReadTool."""
    file_path: str = Field(
        ...,
        description="Path to the file to read (relative to output/ or absolute path)"
    )
    start_line: Optional[int] = Field(
        None,
        description="Starting line number (1-indexed). If None, reads from beginning."
    )
    line_count: Optional[int] = Field(
        None,
        description="Number of lines to read. If None, reads to end of file."
    )


class UTF8FileReadTool(BaseTool):
    """
    Custom file reading tool with UTF-8 encoding.
    
    This tool explicitly uses UTF-8 encoding to read files, preventing
    Windows charmap codec errors. It works with both relative paths (assumed
    to be in output/) and absolute paths.
    
    Example usage:
        tool = UTF8FileReadTool()
        content = tool._run(file_path="output/requirements.md")
    """
    
    name: str = "Read File (UTF-8)"
    description: str = (
        "Reads a file's content with UTF-8 encoding. "
        "Use this to read any text file, especially markdown, YAML, JSON, or Python files. "
        "Handles Windows encoding issues automatically. "
        "Provide file_path as 'output/filename' or absolute path."
    )
    args_schema: Type[BaseModel] = FileReadInput
    
    # Base directory for relative paths
    _base_dir: Optional[Path] = None
    
    def __init__(self, base_dir: Optional[str] = None, **kwargs):
        """
        Initialize the tool.
        
        Args:
            base_dir: Base directory for relative paths (defaults to swe_team/output)
        """
        super().__init__(**kwargs)
        if base_dir:
            self._base_dir = Path(base_dir).resolve()
        else:
            # Default to output directory
            current_file = Path(__file__).resolve()
            # Navigate up to swe_team root, then to output
            swe_team_root = current_file.parent.parent.parent.parent
            self._base_dir = swe_team_root / "output"
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path to absolute path."""
        path = Path(file_path)
        
        if path.is_absolute():
            return path
        else:
            # Relative path - assume it's relative to output/
            if str(path).startswith("output/") or str(path).startswith("output\\"):
                # Strip the "output/" prefix
                path = Path(str(path).replace("output/", "").replace("output\\", ""))
            return self._base_dir / path
    
    def _run(
        self,
        file_path: str,
        start_line: Optional[int] = None,
        line_count: Optional[int] = None
    ) -> str:
        """
        Read file content with UTF-8 encoding.
        
        Args:
            file_path: Path to file (relative to output/ or absolute)
            start_line: Starting line (1-indexed, optional)
            line_count: Number of lines to read (optional)
            
        Returns:
            str: File content or error message
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            if not resolved_path.exists():
                # List what files DO exist in the output directory
                existing_files = []
                if self._base_dir and self._base_dir.exists():
                    existing_files = [f.name for f in self._base_dir.iterdir() if f.is_file()]
                
                msg = f"File not found: {file_path}\n"
                msg += f"(Resolved path: {resolved_path})\n\n"
                
                if existing_files:
                    msg += f"Available files in output/:\n"
                    for f in sorted(existing_files):
                        msg += f"  - {f}\n"
                else:
                    msg += "No files exist in the output directory yet.\n"
                
                msg += "\nNote: This file may need to be created by a previous task. "
                msg += "Check task dependencies and ensure earlier tasks have completed."
                
                return msg
            
            if not resolved_path.is_file():
                return f"Error: Path is not a file: {resolved_path}"
            
            # Read with explicit UTF-8 encoding
            with open(resolved_path, 'r', encoding='utf-8', errors='replace') as f:
                if start_line is None and line_count is None:
                    # Read entire file
                    content = f.read()
                else:
                    # Read specific lines
                    lines = f.readlines()
                    start = (start_line - 1) if start_line else 0
                    end = (start + line_count) if line_count else len(lines)
                    content = ''.join(lines[start:end])
            
            return content
            
        except UnicodeDecodeError as e:
            return f"Error: Unicode decode error even with UTF-8: {str(e)}"
        except PermissionError:
            return f"Error: Permission denied reading file: {resolved_path}"
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"


class FileWriteInput(BaseModel):
    """Input schema for FileWriteTool."""
    file_path: str = Field(
        ...,
        description="Path where to write the file (relative to output/ or absolute path)"
    )
    content: str = Field(
        ...,
        description="Content to write to the file"
    )
    append: bool = Field(
        False,
        description="If True, append to file. If False, overwrite (default)."
    )


class UTF8FileWriteTool(BaseTool):
    """
    Custom file writing tool with UTF-8 encoding.
    
    This tool explicitly uses UTF-8 encoding to write files, ensuring
    compatibility across platforms and preventing encoding issues.
    
    Example usage:
        tool = UTF8FileWriteTool()
        result = tool._run(
            file_path="output/test.md",
            content="# Test\\nContent here"
        )
    """
    
    name: str = "Write File (UTF-8)"
    description: str = (
        "Writes content to a file with UTF-8 encoding. "
        "Use this to create or update any text file. "
        "Automatically creates parent directories if needed. "
        "Provide file_path as 'output/filename' or absolute path."
    )
    args_schema: Type[BaseModel] = FileWriteInput
    
    # Base directory for relative paths
    _base_dir: Optional[Path] = None
    
    def __init__(self, base_dir: Optional[str] = None, **kwargs):
        """
        Initialize the tool.
        
        Args:
            base_dir: Base directory for relative paths (defaults to swe_team/output)
        """
        super().__init__(**kwargs)
        if base_dir:
            self._base_dir = Path(base_dir).resolve()
        else:
            # Default to output directory
            current_file = Path(__file__).resolve()
            swe_team_root = current_file.parent.parent.parent.parent
            self._base_dir = swe_team_root / "output"
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path to absolute path."""
        path = Path(file_path)
        
        if path.is_absolute():
            return path
        else:
            # Relative path - assume it's relative to output/
            if str(path).startswith("output/") or str(path).startswith("output\\"):
                path = Path(str(path).replace("output/", "").replace("output\\", ""))
            return self._base_dir / path
    
    def _run(
        self,
        file_path: str,
        content: str,
        append: bool = False
    ) -> str:
        """
        Write content to file with UTF-8 encoding.
        
        Args:
            file_path: Path to file (relative to output/ or absolute)
            content: Content to write
            append: If True, append; if False, overwrite
            
        Returns:
            str: Success message or error
        """
        try:
            resolved_path = self._resolve_path(file_path)
            
            # Ensure parent directory exists
            resolved_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write mode
            mode = 'a' if append else 'w'
            
            # Write with explicit UTF-8 encoding
            with open(resolved_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            action = "Appended to" if append else "Wrote"
            bytes_written = len(content.encode('utf-8'))
            return f"{action} {resolved_path} ({bytes_written} bytes)"
            
        except PermissionError:
            return f"Error: Permission denied writing to: {resolved_path}"
        except Exception as e:
            return f"Error writing file {file_path}: {str(e)}"


class ListOutputFilesInput(BaseModel):
    """Input schema for ListOutputFilesTool."""
    include_sizes: bool = Field(
        False,
        description="If True, include file sizes in the output."
    )


class ListOutputFilesTool(BaseTool):
    """
    Tool to list available files in the output directory.
    
    Use this tool to check what files exist before trying to read them.
    This helps avoid "file not found" errors by showing what's available.
    """
    
    name: str = "List files in directory"
    description: str = (
        "Lists all files in the output directory. "
        "Use this BEFORE trying to read files to see what exists. "
        "Returns a list of available files with optional sizes."
    )
    args_schema: Type[BaseModel] = ListOutputFilesInput
    
    # Base directory (output/)
    _base_dir: Optional[Path] = None
    
    def __init__(self, base_dir: Optional[str] = None, **kwargs):
        """Initialize with output directory."""
        super().__init__(**kwargs)
        if base_dir:
            self._base_dir = Path(base_dir).resolve()
        else:
            current_file = Path(__file__).resolve()
            swe_team_root = current_file.parent.parent.parent.parent
            self._base_dir = swe_team_root / "output"
    
    def _run(self, include_sizes: bool = False) -> str:
        """
        List files in the output directory.
        
        Args:
            include_sizes: Include file sizes in the listing
            
        Returns:
            str: Formatted list of files
        """
        try:
            if not self._base_dir or not self._base_dir.exists():
                return f"Output directory does not exist yet: {self._base_dir}"
            
            files = []
            for item in sorted(self._base_dir.iterdir()):
                if item.is_file():
                    if include_sizes:
                        size = item.stat().st_size
                        files.append(f"  - {item.name} ({size} bytes)")
                    else:
                        files.append(f"  - {item.name}")
            
            if not files:
                return (
                    "No files in output/ directory yet.\n\n"
                    "Files are created as tasks complete:\n"
                    "  1. pm_task → requirements.md\n"
                    "  2. cto_task → tech_stack.md\n"
                    "  3. devops_task → lockfile.txt\n"
                    "  4. design_task → architecture.md\n"
                    "  5. backend_task → backend_app.py\n"
                    "  6. frontend_task → frontend_app.py"
                )
            
            result = f"Files in output/ ({len(files)} total):\n"
            result += "\n".join(files)
            return result
            
        except Exception as e:
            return f"Error listing files: {str(e)}"


# Convenience function to get both tools
def get_utf8_file_tools(base_dir: Optional[str] = None) -> list:
    """
    Get both UTF-8 file tools as a list.
    
    Args:
        base_dir: Base directory for relative paths
        
    Returns:
        list: [UTF8FileReadTool, UTF8FileWriteTool]
    
    Example:
        tools = get_utf8_file_tools()
        agent = Agent(..., tools=tools)
    """
    return [
        UTF8FileReadTool(base_dir=base_dir),
        UTF8FileWriteTool(base_dir=base_dir)
    ]


# Test function
if __name__ == "__main__":
    import tempfile
    
    print("Testing UTF8FileWriteTool...")
    write_tool = UTF8FileWriteTool()
    
    # Create temp file
    temp_dir = Path(tempfile.gettempdir())
    test_file = temp_dir / "test_utf8.txt"
    
    # Test write
    result = write_tool._run(
        file_path=str(test_file),
        content="Test content with UTF-8: 你好 🎉\n"
    )
    print(f"Write result: {result}")
    
    # Test read
    print("\nTesting UTF8FileReadTool...")
    read_tool = UTF8FileReadTool()
    content = read_tool._run(file_path=str(test_file))
    print(f"Read result: {content}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print(f"\nCleaned up test file: {test_file}")
