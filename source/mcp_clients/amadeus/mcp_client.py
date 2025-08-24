from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator

from ..client import MCPClient


# ---- Pydantic Schemas for MCP Operations ----

class AutocompleteArgs(BaseModel):
    """Arguments for location autocomplete via MCP"""
    query: str = Field(..., description="Free text to match city/airport")
    limit: int = Field(5, ge=1, le=20)
    sub_types: Optional[List[Literal["CITY", "AIRPORT"]]] = Field(default=["CITY", "AIRPORT"])


class SearchArgs(BaseModel):
    """Arguments for flight search via MCP"""
    origin: str = Field(..., min_length=3, max_length=3, description="IATA code, e.g., JFK")
    destination: str = Field(..., min_length=3, max_length=3, description="IATA code, e.g., SFO")
    departure_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    return_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    adults: int = Field(1, ge=1, le=9)
    cabin: Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"] = "ECONOMY"
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    non_stop: Optional[bool] = None
    max_price: Optional[int] = Field(None, ge=1)
    max_results: int = Field(default=10, ge=1, le=250)

    @field_validator("origin", "destination")
    @classmethod
    def uppercase_iata(cls, v: str) -> str:
        return v.upper()


class PriceArgs(BaseModel):
    """Arguments for flight offer pricing via MCP"""
    flight_offer: Dict[str, Any]
    currency: Optional[str] = None


class AmadeusMCPClient:
    """MCP-specific client for connecting to Amadeus MCP server"""
    
    def __init__(self):
        self.mcp_client: Optional[MCPClient] = None
        self.connected = False
    
    async def connect_to_server(self, server_command: List[str]) -> bool:
        """Connect to the Amadeus MCP server"""
        try:
            self.mcp_client = MCPClient(server_command)
            result = await self.mcp_client.connect()
            self.connected = result
            return result
        except Exception as e:
            print(f"Failed to connect to MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect_from_server(self):
        """Disconnect from the MCP server"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
            self.connected = False
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server"""
        return self.connected and self.mcp_client is not None
    
    # ---- MCP Tool Call Methods ----
    
    async def autocomplete_locations(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None):
        """Use MCP server to autocomplete locations"""
        if not self.is_connected():
            return {"success": False, "error": "Not connected to MCP server"}
        
        args = AutocompleteArgs(query=query, limit=limit, sub_types=sub_types)
        return await self.mcp_client.call_tool("autocomplete_locations", args.model_dump())
    
    async def search_flights(self, search_args: Dict[str, Any]):
        """Use MCP server to search flights"""
        if not self.is_connected():
            return {"success": False, "error": "Not connected to MCP server"}
        
        return await self.mcp_client.call_tool("search_flights", search_args)
    
    async def price_offer(self, flight_offer: Dict[str, Any], currency: Optional[str] = None):
        """Use MCP server to price a flight offer"""
        if not self.is_connected():
            return {"success": False, "error": "Not connected to MCP server"}
        
        args = {"flight_offer": flight_offer, "currency": currency}
        return await self.mcp_client.call_tool("price_offer", args)
    
    async def list_tools(self):
        """List available tools from the MCP server"""
        if not self.is_connected():
            return {"success": False, "error": "Not connected to MCP server", "tools": []}
        
        try:
            tools = await self.mcp_client.list_tools()
            return {"success": True, "tools": tools}
        except Exception as e:
            return {"success": False, "error": str(e), "tools": []}
    
    async def list_resources(self):
        """List available resources from the MCP server"""
        if not self.is_connected():
            return {"success": False, "error": "Not connected to MCP server", "resources": []}
        
        try:
            resources = await self.mcp_client.list_resources()
            return {"success": True, "resources": resources}
        except Exception as e:
            return {"success": False, "error": str(e), "resources": []}


def create_mcp_client() -> AmadeusMCPClient:
    """Factory function to create an Amadeus MCP client"""
    return AmadeusMCPClient()