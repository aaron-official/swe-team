"""
Clear MCP Memory Script
Deletes all entities from the Docker MCP Gateway knowledge graph before starting a new crew run.
"""

import sys
import os

# Add the swe_team package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'swe_team', 'src'))

def clear_mcp_memory():
    """
    Clear all stored entities from the MCP Gateway memory.
    
    This prevents old project data from polluting new crew runs.
    """
    try:
        from swe_team.tools.docker_mcp import DockerMCPAdapter
        
        print("🧹 Clearing MCP memory from previous runs...")
        
        # Connect to MCP Gateway
        adapter = DockerMCPAdapter(url="http://localhost:8000/mcp")
        adapter.connect()
        
        if not adapter._tools:
            print("ℹ️  MCP Gateway not running (memory clearing skipped)")
            print("   This is fine - the system works without MCP\n")
            return True
        
        # Find the memory tools
        read_graph_tool = None
        delete_tool = None
        
        for tool in adapter._tools:
            if hasattr(tool, 'name'):
                if tool.name == 'read_graph':
                    read_graph_tool = tool
                elif tool.name == 'delete_entities':
                    delete_tool = tool
        
        if not read_graph_tool:
            print("⚠️  Memory tools not available in MCP Gateway")
            print("   Continuing without clearing...\n")
            adapter.disconnect()
            return True
        
        # Read the knowledge graph
        try:
            result = read_graph_tool._run()
            
            # Parse the result (it might be JSON or plain text)
            if isinstance(result, str):
                import json
                try:
                    data = json.loads(result)
                    entities = data.get("entities", [])
                except json.JSONDecodeError:
                    # Result might be plain text, check if it says "no entities"
                    if "no entities" in result.lower() or not result.strip():
                        print("✅ MCP memory is already empty\n")
                        adapter.disconnect()
                        return True
                    entities = []
            elif isinstance(result, dict):
                entities = result.get("entities", [])
            else:
                entities = []
            
            if not entities:
                print("✅ MCP memory is already empty\n")
                adapter.disconnect()
                return True
            
            print(f"📦 Found {len(entities)} entities in memory")
            
            # Delete each entity if delete tool is available
            if delete_tool:
                deleted_count = 0
                for entity in entities:
                    entity_name = entity.get("name", "unknown")
                    try:
                        # delete_entities expects entityNames as an array
                        delete_tool._run(entityNames=[entity_name])
                        deleted_count += 1
                        print(f"   🗑️  Deleted: {entity_name}")
                    except Exception as e:
                        print(f"   ⚠️  Could not delete {entity_name}: {e}")
                
                print(f"✅ Cleared {deleted_count} entities from MCP memory\n")
            else:
                print("⚠️  Delete tool not available, cannot clear memory")
                print("   Try restarting the MCP Gateway\n")
            
            adapter.disconnect()
            return True
            
        except Exception as e:
            print(f"⚠️  Error listing entities: {e}")
            adapter.disconnect()
            return True
        
    except ImportError:
        print("⚠️  Could not import MCP adapter (swe_team not installed)")
        print("   Install with: pip install -e ./swe_team\n")
        return True
    except Exception as e:
        print(f"ℹ️  MCP Gateway not available: {e}")
        print("   This is fine - the system works without MCP\n")
        return True

if __name__ == "__main__":
    success = clear_mcp_memory()
    sys.exit(0 if success else 1)
