import os
import time
import json
from typing import Any, Dict, List, Optional, Literal

import httpx
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from ..client import MCPClient


class OAuthToken(BaseModel):
    """OAuth token for Amadeus API authentication"""
    access_token: str
    token_type: str
    expires_in: int
    scope: Optional[str] = None
    created_at: float = Field(default_factory=lambda: time.time())

    @property
    def is_expired(self) -> bool:
        # refresh a bit early (15s)
        return (time.time() - self.created_at) >= (self.expires_in - 15)


class AmadeusAPIClient:
    """Low-level Amadeus API client for direct API access"""
    
    def __init__(self, client_id: str, client_secret: str, base_url: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip("/")
        self._token: Optional[OAuthToken] = None
        self._client = httpx.Client(timeout=30.0)

    def _ensure_token(self):
        """Ensure we have a valid OAuth token"""
        if self._token and not self._token.is_expired:
            return
            
        token_url = f"{self.base_url}/v1/security/oauth2/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = self._client.post(token_url, data=data, headers=headers)
        r.raise_for_status()
        self._token = OAuthToken(**r.json())

    def _auth_headers(self) -> Dict[str, str]:
        """Get authorization headers with current token"""
        self._ensure_token()
        assert self._token is not None
        return {"Authorization": f"Bearer {self._token.access_token}"}

    # ---- Locations (autocomplete) ----
    def autocomplete_locations(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None):
        """Autocomplete locations using Amadeus API"""
        params = {
            "keyword": query,
            "page[limit]": str(limit),
        }
        if sub_types:
            params["subType"] = ",".join(sub_types)
        url = f"{self.base_url}/v1/reference-data/locations"
        r = self._client.get(url, headers=self._auth_headers(), params=params)
        r.raise_for_status()
        return r.json()

    # ---- Flight Offers Search ----
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        adults: int,
        cabin: str,
        currency: str,
        non_stop: Optional[bool],
        max_price: Optional[int],
        max_results: int,
    ):
        """Search flight offers using Amadeus API"""
        url = f"{self.base_url}/v2/shopping/flight-offers"
        payload: Dict[str, Any] = {
            "currencyCode": currency,
            "adults": adults,
            "sources": ["GDS"],
            "travelClass": cabin,  # ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST
            "max": max_results,
            "originLocationCode": origin.upper(),
            "destinationLocationCode": destination.upper(),
            "departureDate": departure_date,
        }
        if return_date:
            payload["returnDate"] = return_date
        if non_stop is not None:
            payload["nonStop"] = non_stop
        if max_price is not None:
            payload["maxPrice"] = max_price

        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json",
        }
        r = self._client.get(url, headers=headers, params=payload)
        r.raise_for_status()
        return r.json()

    # ---- Flight Offers Price ----
    def price_offer(self, flight_offer: Dict[str, Any], currency: Optional[str]):
        """Price a flight offer using Amadeus API"""
        url = f"{self.base_url}/v1/shopping/flight-offers/pricing"
        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json",
        }

        body = {
            "data": {
                "type": "flight-offers-pricing",
                "flightOffers": [flight_offer],
            }
        }

        r = self._client.post(url, headers=headers, json=body)
        r.raise_for_status()
        return r.json()

    def close(self):
        """Close the HTTP client"""
        self._client.close()


# ---- Pydantic Schemas for Client Operations ----

class AutocompleteArgs(BaseModel):
    """Arguments for location autocomplete"""
    query: str = Field(..., description="Free text to match city/airport")
    limit: int = Field(5, ge=1, le=20)
    sub_types: Optional[List[Literal["CITY", "AIRPORT"]]] = Field(default=["CITY", "AIRPORT"])


class SearchArgs(BaseModel):
    """Arguments for flight search"""
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
    """Arguments for flight offer pricing"""
    # Expect the exact flightOffer you received from search (JSON object)
    flight_offer: Dict[str, Any]
    currency: Optional[str] = None  # Typically pricing will use the offer currency


class AmadeusMCPClient:
    """High-level Amadeus MCP client that wraps the API client and MCP functionality"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, host: str = "test"):
        load_dotenv()
        
        # Use provided credentials or environment variables
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET", "")
        
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Missing AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET")
        
        # Setup API client
        host = host.lower()
        self.base_url = "https://test.api.amadeus.com" if host != "prod" else "https://api.amadeus.com"
        self.api_client = AmadeusAPIClient(self.client_id, self.client_secret, self.base_url)
        
        # Default settings
        self.default_currency = os.getenv("DEFAULT_CURRENCY", "USD")
        self.default_max_results = int(os.getenv("DEFAULT_MAX_RESULTS", "10"))
        
        # MCP client for connecting to Amadeus MCP server
        self.mcp_client: Optional[MCPClient] = None
    
    async def connect_to_mcp_server(self, server_command: List[str]):
        """Connect to the Amadeus MCP server"""
        self.mcp_client = MCPClient(server_command)
        return await self.mcp_client.connect()
    
    async def disconnect_from_mcp_server(self):
        """Disconnect from the MCP server"""
        if self.mcp_client:
            await self.mcp_client.disconnect()
    
    # ---- Direct API Methods ----
    
    def autocomplete_locations_direct(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None):
        """Direct API call to autocomplete locations"""
        try:
            data = self.api_client.autocomplete_locations(query, limit, sub_types)
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
            raw = self.api_client.search_flights(
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
            result = self.api_client.price_offer(args.flight_offer, args.currency)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e), "result": None}
    
    # ---- MCP Methods (via server) ----
    
    async def autocomplete_locations_mcp(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None):
        """Use MCP server to autocomplete locations"""
        if not self.mcp_client:
            return {"success": False, "error": "Not connected to MCP server"}
        
        args = AutocompleteArgs(query=query, limit=limit, sub_types=sub_types)
        return await self.mcp_client.call_tool("autocomplete_locations", args.model_dump())
    
    async def search_flights_mcp(self, search_args: Dict[str, Any]):
        """Use MCP server to search flights"""
        if not self.mcp_client:
            return {"success": False, "error": "Not connected to MCP server"}
        
        return await self.mcp_client.call_tool("search_flights", search_args)
    
    async def price_offer_mcp(self, flight_offer: Dict[str, Any], currency: Optional[str] = None):
        """Use MCP server to price a flight offer"""
        if not self.mcp_client:
            return {"success": False, "error": "Not connected to MCP server"}
        
        args = {"flight_offer": flight_offer, "currency": currency}
        return await self.mcp_client.call_tool("price_offer", args)
    
    # ---- Convenience Methods (with fallback) ----
    
    async def autocomplete_locations(self, query: str, limit: int = 5, sub_types: Optional[List[str]] = None, prefer_mcp: bool = True):
        """Autocomplete locations with MCP fallback to direct API"""
        if prefer_mcp and self.mcp_client:
            result = await self.autocomplete_locations_mcp(query, limit, sub_types)
            if result.get("success"):
                return result
        
        # Fallback to direct API
        return self.autocomplete_locations_direct(query, limit, sub_types)
    
    async def search_flights(self, search_args: Dict[str, Any], prefer_mcp: bool = True):
        """Search flights with MCP fallback to direct API"""
        if prefer_mcp and self.mcp_client:
            result = await self.search_flights_mcp(search_args)
            if result.get("success"):
                return result
        
        # Fallback to direct API
        args = SearchArgs(**search_args)
        return self.search_flights_direct(args)
    
    async def price_offer(self, flight_offer: Dict[str, Any], currency: Optional[str] = None, prefer_mcp: bool = True):
        """Price flight offer with MCP fallback to direct API"""
        if prefer_mcp and self.mcp_client:
            result = await self.price_offer_mcp(flight_offer, currency)
            if result.get("success"):
                return result
        
        # Fallback to direct API
        args = PriceArgs(flight_offer=flight_offer, currency=currency)
        return self.price_offer_direct(args)
    
    def close(self):
        """Close all connections"""
        self.api_client.close()


def create_amadeus_client(client_id: str = None, client_secret: str = None, host: str = "test") -> AmadeusMCPClient:
    """Factory function to create an Amadeus MCP client"""
    return AmadeusMCPClient(client_id, client_secret, host)