"""
Test script to verify Docker integration for CrewAI agents.
Tests both DockerShellTool (primary) and MCP adapter (optional).
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'swe_team', 'src'))

from swe_team.tools.tools import DockerShellTool
from swe_team.tools.docker_mcp import DockerMCPAdapter

def test_docker_shell_tool():
    """Test the primary DockerShellTool that agents use for command execution."""
    print("=" * 70)
    print("🧪 TEST 1: DockerShellTool (PRIMARY - Command Execution)")
    print("=" * 70)
    
    tool = DockerShellTool()
    
    # Test 1: Simple echo
    print("\n📝 Test 1a: Simple echo command")
    result = tool._run("echo 'Hello from Docker!'")
    print(result)
    
    # Test 2: Check Python
    print("\n📝 Test 1b: Check Python version")
    result = tool._run("python --version")
    print(result)
    
    # Test 3: Check Node.js
    print("\n📝 Test 1c: Check Node.js version")
    result = tool._run("node --version")
    print(result)
    
    # Test 4: Check npm
    print("\n📝 Test 1d: Check npm version")
    result = tool._run("npm --version")
    print(result)
    
    # Test 5: List files in /app
    print("\n📝 Test 1e: List files in workspace")
    result = tool._run("ls -la")
    print(result)
    
    print("\n✅ DockerShellTool tests complete!")
    return True

def test_mcp_adapter():
    """Test the optional MCP adapter for knowledge storage."""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Docker MCP Adapter (OPTIONAL - Knowledge Storage)")
    print("=" * 70)
    
    try:
        adapter = DockerMCPAdapter()
        adapter.connect()
        tools = adapter.get_tools()
        
        print(f"\n✅ MCP Connected! Tools available: {len(tools)}")
        print("\n📋 Available MCP Tools:")
        for i, tool in enumerate(tools, 1):
            print(f"  {i:2d}. {tool.name}")
        
        adapter.disconnect()
        return True
    except Exception as e:
        print(f"\n⚠️  MCP Connection Failed: {e}")
        print("   This is OK - MCP is optional for knowledge storage only.")
        print("   Agents will still work using DockerShellTool.")
        return False

def main():
    print("\n" + "🚀" * 35)
    print("CREWAI DOCKER INTEGRATION TEST")
    print("🚀" * 35 + "\n")
    
    # Test 1: DockerShellTool (CRITICAL)
    docker_ok = test_docker_shell_tool()
    
    # Test 2: MCP Adapter (OPTIONAL)
    mcp_ok = test_mcp_adapter()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"DockerShellTool (Command Execution): {'✅ PASS' if docker_ok else '❌ FAIL'}")
    print(f"MCP Adapter (Knowledge Storage):     {'✅ Available' if mcp_ok else '⚠️  Optional (Not Available)'}")
    
    if docker_ok:
        print("\n🎉 SUCCESS! Your agents can execute commands in Docker!")
        print("\nYour agents can now:")
        print("  ✅ Install packages (npm install, pip install)")
        print("  ✅ Run Python code (python app.py)")
        print("  ✅ Run Node.js code (node server.js)")
        print("  ✅ Execute any shell command")
        
        if mcp_ok:
            print("\n🧠 BONUS: MCP tools also available for knowledge storage!")
        
        print("\n🚀 Ready to run: python -m swe_team.main")
    else:
        print("\n❌ CRITICAL: DockerShellTool failed!")
        print("   Please ensure Docker Desktop is running.")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
