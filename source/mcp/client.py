import asyncio
import json
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient:
    def __init__(self, server_command: List[str], server_args: List[str] = None):
        self.server_command = server_command
        self.server_args = server_args or []
        self.session: Optional[ClientSession] = None
        self.connected = False
    
    async def connect(self):
        """Connect to MCP server"""
        try:
            server_params = StdioServerParameters(
                command=self.server_command[0],
                args=self.server_command[1:] + self.server_args
            )
            
            self.session = await stdio_client(server_params)
            await self.session.initialize()
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from MCP server"""
        if self.session:
            await self.session.close()
            self.connected = False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools from the MCP server"""
        if not self.connected or not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.session.list_tools()
            return response.tools
        except Exception as e:
            print(f"Error listing tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with arguments"""
        if not self.connected or not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.session.call_tool(tool_name, arguments)
            return {
                "success": True,
                "result": response.content,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": str(e)
            }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server"""
        if not self.connected or not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.session.list_resources()
            return response.resources
        except Exception as e:
            print(f"Error listing resources: {e}")
            return []
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a specific resource"""
        if not self.connected or not self.session:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            response = await self.session.read_resource(uri)
            return {
                "success": True,
                "content": response.contents,
                "error": None
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "error": str(e)
            }