"""
List available MCP tools to see what memory management tools exist
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'swe_team', 'src'))

try:
    from swe_team.tools.docker_mcp import DockerMCPAdapter
    
    print("🔍 Listing all MCP tools...\n")
    
    adapter = DockerMCPAdapter(url="http://localhost:8000/mcp")
    adapter.connect()
    
    if not adapter._tools:
        print("❌ No MCP tools available")
    else:
        print(f"📦 Found {len(adapter._tools)} tools:\n")
        for i, tool in enumerate(adapter._tools, 1):
            if hasattr(tool, 'name') and hasattr(tool, 'description'):
                print(f"{i}. {tool.name}")
                print(f"   Description: {tool.description[:100]}...")
                print()
    
    adapter.disconnect()

except Exception as e:
    print(f"❌ Error: {e}")
