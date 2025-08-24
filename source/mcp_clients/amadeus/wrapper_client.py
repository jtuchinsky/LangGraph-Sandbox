import os
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv

from .direct_client import AmadeusDirectClient, create_direct_client
from .mcp_client import AmadeusMCPClient, create_mcp_client, SearchArgs, PriceArgs


class AmadeusWrapperClient:
    """High-level Amadeus client that combines direct API and MCP functionality with fallback support"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, host: str = "test"):
        load_dotenv()
        
        # Initialize direct API client
        self.direct_client = create_direct_client(client_id, client_secret, host)
        
        # Initialize MCP client
        self.mcp_client = create_mcp_client()
        
        # Default settings
        self.default_currency = os.getenv("DEFAULT_CURRENCY", "USD")
        self.default_max_results = int(os.getenv("DEFAULT_MAX_RESULTS", "10"))
    
    # ---- MCP Server Connection Management ----
    
    async def connect_to_mcp_server(self, server_command: List[str]) -> bool:
        """Connect to the Amadeus MCP server"""
        return await self.mcp_client.connect_to_server(server_command)
    
    async def disconnect_from_mcp_server(self):
        """Disconnect from the MCP server"""
        await self.mcp_client.disconnect_from_server()
    
    def is_mcp_connected(self) -> bool:
        """Check if MCP server is connected"""
        return self.mcp_client.is_connected()
    
    # ---- Direct API Methods ----
    
    def autocomplete_locations_direct(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None):
        """Direct API call to autocomplete locations"""
        try:
            data = self.direct_client.autocomplete_locations(query, limit, sub_types)
            # Return slimmed results for convenience
            items = []
            for item in data.get("data", []):
                items.append({
                    "name": item.get("name"),
                    "iata": item.get("iataCode"),
                    "type": item.get("subType"),
                    "timeZoneOffset": item.get("timeZoneOffset"),
                    "geo": item.get("geo"),
                    "address": item.get("address"),
                })
            return {"success": True, "count": len(items), "items": items}
        except httpx.HTTPStatusError as e:
            error_detail = f"HTTP {e.response.status_code}: {e.response.text if e.response.text else 'No response body'}"
            return {"success": False, "error": error_detail, "items": []}
        except Exception as e:
            return {"success": False, "error": str(e), "items": []}
    
    def search_flights_direct(self, args):
        """Direct API call to search flights"""
        try:
            # Convert dict to SearchArgs if needed
            if isinstance(args, dict):
                args = SearchArgs(**args)
            
            currency = args.currency or self.default_currency
            raw = self.direct_client.search_flights(
                origin=args.origin,
                destination=args.destination,
                departure_date=args.departure_date,
                return_date=args.return_date,
                adults=args.adults,
                cabin=args.cabin,
                currency=currency,
                non_stop=args.non_stop,
                max_price=args.max_price,
                max_results=args.max_results,
            )

            # Slim response: keep core fields used by agents regularly
            offers = []
            for offer in raw.get("data", []):
                price = offer.get("price", {})
                itineraries = []
                for itin in offer.get("itineraries", []):
                    segments = []
                    for seg in itin.get("segments", []):
                        dep = seg.get("departure", {})
                        arr = seg.get("arrival", {})
                        segments.append({
                            "carrierCode": seg.get("carrierCode"),
                            "number": seg.get("number"),
                            "from": dep.get("iataCode"),
                            "to": arr.get("iataCode"),
                            "depTime": dep.get("at"),
                            "arrTime": arr.get("at"),
                            "duration": seg.get("duration"),
                            "aircraft": seg.get("aircraft", {}).get("code"),
                            "operating": seg.get("operating", {}).get("carrierCode"),
                        })
                    itineraries.append({
                        "duration": itin.get("duration"),
                        "segments": segments
                    })
                offers.append({
                    "id": offer.get("id"),
                    "oneWay": offer.get("oneWay"),
                    "oneAdultTotal": price.get("grandTotal"),
                    "currency": price.get("currency"),
                    "itineraries": itineraries,
                    # Keep the full offer for pricing step
                    "_full": offer
                })

            meta = raw.get("meta", {})
            return {"success": True, "count": len(offers), "offers": offers, "meta": meta}
        except Exception as e:
            return {"success": False, "error": str(e), "offers": []}
    
    def price_offer_direct(self, args: PriceArgs):
        """Direct API call to price a flight offer"""
        try:
            result = self.direct_client.price_offer(args.flight_offer, args.currency)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e), "result": None}
    
    # ---- MCP Methods (via server) ----
    
    async def autocomplete_locations_mcp(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None):
        """Use MCP server to autocomplete locations"""
        return await self.mcp_client.autocomplete_locations(query, limit, sub_types)
    
    async def search_flights_mcp(self, search_args: Dict[str, Any]):
        """Use MCP server to search flights"""
        return await self.mcp_client.search_flights(search_args)
    
    async def price_offer_mcp(self, flight_offer: Dict[str, Any], currency: Optional[str] = None):
        """Use MCP server to price a flight offer"""
        return await self.mcp_client.price_offer(flight_offer, currency)
    
    # ---- Convenience Methods (with fallback) ----
    
    async def autocomplete_locations(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None, prefer_mcp: bool = True):
        """Autocomplete locations with MCP fallback to direct API"""
        if prefer_mcp and self.is_mcp_connected():
            result = await self.autocomplete_locations_mcp(query, limit, sub_types)
            if result.get("success"):
                return result
        
        # Fallback to direct API
        return self.autocomplete_locations_direct(query, limit, sub_types)
    
    async def search_flights(self, search_args: Dict[str, Any], prefer_mcp: bool = True):
        """Search flights with MCP fallback to direct API"""
        if prefer_mcp and self.is_mcp_connected():
            result = await self.search_flights_mcp(search_args)
            if result.get("success"):
                return result
        
        # Fallback to direct API
        args = SearchArgs(**search_args)
        return self.search_flights_direct(args)
    
    async def price_offer(self, flight_offer: Dict[str, Any], currency: Optional[str] = None, prefer_mcp: bool = True):
        """Price flight offer with MCP fallback to direct API"""
        if prefer_mcp and self.is_mcp_connected():
            result = await self.price_offer_mcp(flight_offer, currency)
            if result.get("success"):
                return result
        
        # Fallback to direct API
        args = PriceArgs(flight_offer=flight_offer, currency=currency)
        return self.price_offer_direct(args)
    
    # ---- Server Information Methods ----
    
    async def list_mcp_tools(self):
        """List available tools from the MCP server"""
        return await self.mcp_client.list_tools()
    
    async def list_mcp_resources(self):
        """List available resources from the MCP server"""
        return await self.mcp_client.list_resources()
    
    # ---- Resource Management ----
    
    def close(self):
        """Close all connections"""
        self.direct_client.close()


def create_amadeus_client(client_id: str = None, client_secret: str = None, host: str = "test") -> AmadeusWrapperClient:
    """Factory function to create a comprehensive Amadeus client with both direct API and MCP capabilities"""
    return AmadeusWrapperClient(client_id, client_secret, host)