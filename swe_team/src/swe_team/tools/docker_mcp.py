"""
==============================================================================
Docker MCP Gateway Tool for CrewAI
==============================================================================
This tool provides proper integration with Docker MCP Gateway using the
Streamable HTTP transport, matching the working OpenAI Agents SDK implementation.

Based on the working implementation in lab1.ipynb which uses:
- MCPServerStreamableHttp from OpenAI Agents SDK
- URL: http://localhost:8081/mcp
- Streamable HTTP transport (not JSON-RPC)

This adapter makes Docker MCP tools (filesystem, memory, playwright, etc.)
available to CrewAI agents.
==============================================================================
"""

from crewai_tools import MCPServerAdapter
from typing import List, Optional
import os

class DockerMCPAdapter:
    """
    Adapter for Docker MCP Gateway using Streamable HTTP transport.
    
    This matches the working OpenAI Agents SDK implementation which uses:
    - MCPServerStreamableHttp
    - URL: http://localhost:8081/mcp
    - Timeout: 6000 seconds
    - Playwright timeouts: 6000000ms
    
    Usage:
        adapter = DockerMCPAdapter()
        tools = adapter.get_tools()
        agent = Agent(..., tools=tools)
    """
    
    def __init__(
        self,
        url: str = "http://localhost:8000/mcp",
        timeout: int = 6000,
    ):
        """
        Initialize Docker MCP adapter.
        
        Args:
            url: Docker MCP Gateway URL (default: http://localhost:8000/mcp)
            timeout: Connection timeout in seconds (default: 6000)
        """
        self.url = url
        self.timeout = timeout
        self.adapter: Optional[MCPServerAdapter] = None
        self._tools: Optional[List] = None
    
    def connect(self):
        """
        Connect to Docker MCP Gateway using Streamable HTTP transport.
        
        This uses CrewAI's MCPServerAdapter with Streamable HTTP configuration
        matching the OpenAI Agents SDK setup.
        """
        if self.adapter is not None:
            return  # Already connected
        
        # Configure server parameters for Streamable HTTP transport
        # Based on OpenAI Agents SDK MCPServerStreamableHttp documentation:
        # Valid params are: url, headers, timeout
        # Note: playwright timeouts are NOT supported in streamable-http transport
        server_params = {
            "url": self.url,
            "transport": "streamable-http",
            "timeout": self.timeout,
        }
        
        try:
            # Initialize MCPServerAdapter with Streamable HTTP config
            self.adapter = MCPServerAdapter(server_params)
            self._tools = self.adapter.tools
            print(f"✅ Connected to Docker MCP Gateway at {self.url}")
            print(f"📦 Available MCP tools: {len(self._tools)}")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to Docker MCP Gateway: {e}")
            print(f"   Make sure Docker MCP is running on {self.url}")
            print(f"   The system will continue without MCP tools.")
            self._tools = []
    
    def get_tools(self) -> List:
        """
        Get all available MCP tools from Docker Gateway.
        
        Returns:
            List of CrewAI-compatible tools from the MCP server
        """
        if self.adapter is None:
            self.connect()
        
        return self._tools or []
    
    def disconnect(self):
        """
        Disconnect from Docker MCP Gateway.
        
        Important: Always call this when done to clean up connections.
        """
        if self.adapter is not None:
            try:
                self.adapter.stop()
                print("✅ Disconnected from Docker MCP Gateway")
            except Exception as e:
                print(f"⚠️  Warning during MCP disconnect: {e}")
            finally:
                self.adapter = None
                self._tools = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Convenience function for quick usage
def get_docker_mcp_tools(
    url: str = "http://localhost:8000/mcp",
    timeout: int = 6000
) -> List:
    """
    Quick helper to get Docker MCP tools.
    
    Args:
        url: Docker MCP Gateway URL
        timeout: Connection timeout in seconds
    
    Returns:
        List of MCP tools ready to use with CrewAI agents
    
    Example:
        tools = get_docker_mcp_tools()
        agent = Agent(
            role="Research Agent",
            tools=tools + [other_tools],
            ...
        )
    """
    adapter = DockerMCPAdapter(url=url, timeout=timeout)
    adapter.connect()
    return adapter.get_tools()


# Example usage
if __name__ == "__main__":
    # Test connection
    print("Testing Docker MCP Gateway connection...")
    
    with DockerMCPAdapter() as adapter:
        tools = adapter.get_tools()
        print(f"\n📋 Available tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:80]}...")
