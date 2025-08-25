"""
Google Flights MCP Client

A client for connecting to the Google Flights MCP server that provides flight search,
airport lookup, and travel planning functionality using fast-flights API.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, field_validator
from ..client import MCPClient


# Pydantic models for request/response validation
class FlightSearchArgs(BaseModel):
    """Arguments for flight search"""
    from_airport: str = Field(..., min_length=3, max_length=3, description="3-letter IATA departure code")
    to_airport: str = Field(..., min_length=3, max_length=3, description="3-letter IATA arrival code")
    departure_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Departure date YYYY-MM-DD")
    return_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="Return date YYYY-MM-DD")
    adults: int = Field(1, ge=1, le=9, description="Number of adults")
    children: int = Field(0, ge=0, le=9, description="Number of children")
    infants_in_seat: int = Field(0, ge=0, le=9, description="Number of infants in seat")
    infants_on_lap: int = Field(0, ge=0, le=9, description="Number of infants on lap")
    seat_class: str = Field("economy", description="Seat class: economy, premium_economy, business, first")
    
    @field_validator("from_airport", "to_airport")
    @classmethod
    def uppercase_airport_codes(cls, v: str) -> str:
        return v.upper()
    
    @field_validator("seat_class")
    @classmethod
    def validate_seat_class(cls, v: str) -> str:
        valid_classes = ["economy", "premium_economy", "business", "first"]
        if v.lower() not in valid_classes:
            raise ValueError(f"Seat class must be one of: {', '.join(valid_classes)}")
        return v.lower()


class AirportSearchArgs(BaseModel):
    """Arguments for airport search"""
    query: str = Field(..., min_length=2, description="Search term for airport name, city, or code")


class TravelDatesArgs(BaseModel):
    """Arguments for travel date suggestions"""
    days_from_now: Optional[int] = Field(None, ge=1, description="Days from today for departure")
    trip_length: Optional[int] = Field(None, ge=1, description="Trip length in days")


class GoogleFlightsMCPClient:
    """MCP client for Google Flights server"""
    
    def __init__(self):
        self.mcp_client: Optional[MCPClient] = None
        self.connected = False
        self.logger = logging.getLogger(__name__)
    
    async def connect_to_server(self, server_command: List[str]) -> bool:
        """Connect to the Google Flights MCP server"""
        try:
            self.mcp_client = MCPClient(server_command)
            result = await self.mcp_client.connect()
            self.connected = result
            
            if self.connected:
                self.logger.info("Connected to Google Flights MCP server")
            else:
                self.logger.error("Failed to connect to Google Flights MCP server")
            
            return self.connected
            
        except Exception as e:
            self.logger.error(f"Error connecting to Google Flights MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect_from_server(self):
        """Disconnect from the MCP server"""
        if self.mcp_client:
            try:
                await self.mcp_client.disconnect()
                self.connected = False
                self.logger.info("Disconnected from Google Flights MCP server")
            except Exception as e:
                self.logger.error(f"Error disconnecting: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to MCP server"""
        return self.connected
    
    async def search_flights(self, search_args: FlightSearchArgs) -> Dict[str, Any]:
        """Search for flights using MCP server"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            # Convert Pydantic model to dict for MCP call
            args_dict = search_args.model_dump(exclude_none=True)
            
            result = await self.mcp_client.call_tool("search_flights", args_dict)
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error searching flights: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def airport_search(self, query: str) -> Dict[str, Any]:
        """Search for airports by name, city, or code"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            search_args = AirportSearchArgs(query=query)
            args_dict = search_args.model_dump()
            
            result = await self.mcp_client.call_tool("airport_search", args_dict)
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error searching airports: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_travel_dates(self, days_from_now: Optional[int] = None, 
                              trip_length: Optional[int] = None) -> Dict[str, Any]:
        """Get suggested travel dates"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            travel_args = TravelDatesArgs(days_from_now=days_from_now, trip_length=trip_length)
            args_dict = travel_args.model_dump(exclude_none=True)
            
            result = await self.mcp_client.call_tool("get_travel_dates", args_dict)
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error getting travel dates: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_airports_database(self) -> Dict[str, Any]:
        """Update the airports database"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            result = await self.mcp_client.call_tool("update_airports_database", {})
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error updating airports database: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_all_airports(self) -> Dict[str, Any]:
        """Get all available airports using MCP resource"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            result = await self.mcp_client.read_resource("airports://all")
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error getting airports: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
        """Get information about a specific airport"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            airport_code = airport_code.upper()
            result = await self.mcp_client.read_resource(f"airports://{airport_code}")
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error getting airport info: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def plan_trip_prompt(self, destination: str) -> Dict[str, Any]:
        """Get trip planning prompt for a destination"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            # MCP prompts are typically called differently - this might need adjustment
            # based on the actual MCP client implementation
            result = await self.mcp_client.call_tool("plan_trip", {"destination": destination})
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error getting trip plan prompt: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def compare_destinations_prompt(self, destination1: str, destination2: str) -> Dict[str, Any]:
        """Get prompt for comparing two destinations"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            args = {"destination1": destination1, "destination2": destination2}
            result = await self.mcp_client.call_tool("compare_destinations", args)
            
            if result.get("is_error", False):
                return {
                    "success": False,
                    "error": result.get("content", "Unknown error occurred")
                }
            
            return {
                "success": True,
                "result": result.get("content", ""),
                "raw_response": result
            }
            
        except Exception as e:
            self.logger.error(f"Error getting destination comparison prompt: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List all available MCP tools"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            tools = await self.mcp_client.list_tools()
            return {
                "success": True,
                "tools": tools
            }
        except Exception as e:
            self.logger.error(f"Error listing tools: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_resources(self) -> Dict[str, Any]:
        """List all available MCP resources"""
        if not self.connected or not self.mcp_client:
            return {
                "success": False,
                "error": "Not connected to Google Flights MCP server"
            }
        
        try:
            resources = await self.mcp_client.list_resources()
            return {
                "success": True,
                "resources": resources
            }
        except Exception as e:
            self.logger.error(f"Error listing resources: {e}")
            return {
                "success": False,
                "error": str(e)
            }


def create_google_flights_client() -> GoogleFlightsMCPClient:
    """Factory function to create a Google Flights MCP client"""
    return GoogleFlightsMCPClient()