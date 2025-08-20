import asyncio
from typing import Dict, List, Any, Optional
from .client import MCPClient


class MCPHost:
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
        self.connected_clients: List[str] = []
    
    async def add_client(self, name: str, server_command: List[str], server_args: List[str] = None) -> bool:
        """Add a new MCP client"""
        try:
            client = MCPClient(server_command, server_args)
            success = await client.connect()
            
            if success:
                self.clients[name] = client
                self.connected_clients.append(name)
                print(f"Successfully connected MCP client: {name}")
                return True
            else:
                print(f"Failed to connect MCP client: {name}")
                return False
        except Exception as e:
            print(f"Error adding MCP client {name}: {e}")
            return False
    
    async def remove_client(self, name: str):
        """Remove an MCP client"""
        if name in self.clients:
            await self.clients[name].disconnect()
            del self.clients[name]
            if name in self.connected_clients:
                self.connected_clients.remove(name)
            print(f"Disconnected MCP client: {name}")
    
    async def list_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """List tools from all connected clients"""
        all_tools = {}
        
        for name, client in self.clients.items():
            if client.connected:
                try:
                    tools = await client.list_tools()
                    all_tools[name] = tools
                except Exception as e:
                    print(f"Error listing tools from {name}: {e}")
                    all_tools[name] = []
        
        return all_tools
    
    async def call_tool(self, client_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool from a specific client"""
        if client_name not in self.clients:
            return {
                "success": False,
                "result": None,
                "error": f"Client {client_name} not found"
            }
        
        client = self.clients[client_name]
        if not client.connected:
            return {
                "success": False,
                "result": None,
                "error": f"Client {client_name} not connected"
            }
        
        return await client.call_tool(tool_name, arguments)
    
    async def find_tool(self, tool_name: str) -> Optional[str]:
        """Find which client has a specific tool"""
        all_tools = await self.list_all_tools()
        
        for client_name, tools in all_tools.items():
            for tool in tools:
                if tool.get("name") == tool_name:
                    return client_name
        
        return None
    
    async def call_any_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool from any client that has it"""
        client_name = await self.find_tool(tool_name)
        
        if client_name:
            return await self.call_tool(client_name, tool_name, arguments)
        else:
            return {
                "success": False,
                "result": None,
                "error": f"Tool {tool_name} not found in any connected client"
            }
    
    async def list_all_resources(self) -> Dict[str, List[Dict[str, Any]]]:
        """List resources from all connected clients"""
        all_resources = {}
        
        for name, client in self.clients.items():
            if client.connected:
                try:
                    resources = await client.list_resources()
                    all_resources[name] = resources
                except Exception as e:
                    print(f"Error listing resources from {name}: {e}")
                    all_resources[name] = []
        
        return all_resources
    
    async def read_resource(self, client_name: str, uri: str) -> Dict[str, Any]:
        """Read a resource from a specific client"""
        if client_name not in self.clients:
            return {
                "success": False,
                "content": None,
                "error": f"Client {client_name} not found"
            }
        
        client = self.clients[client_name]
        if not client.connected:
            return {
                "success": False,
                "content": None,
                "error": f"Client {client_name} not connected"
            }
        
        return await client.read_resource(uri)
    
    async def shutdown(self):
        """Shutdown all MCP clients"""
        for name in list(self.clients.keys()):
            await self.remove_client(name)
        print("All MCP clients disconnected")