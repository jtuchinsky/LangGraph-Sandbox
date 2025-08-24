import os
import time
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field
from dotenv import load_dotenv


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


class AmadeusDirectClient:
    """Direct Amadeus API client for low-level API access"""
    
    def __init__(self, client_id: str = None, client_secret: str = None, host: str = "test"):
        load_dotenv()
        
        # Use provided credentials or environment variables
        self.client_id = client_id or os.getenv("AMADEUS_CLIENT_ID", "")
        self.client_secret = client_secret or os.getenv("AMADEUS_CLIENT_SECRET", "")
        
        if not self.client_id or not self.client_secret:
            raise RuntimeError("Missing AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET")
        
        # Setup API configuration
        host = host.lower()
        self.base_url = "https://test.api.amadeus.com" if host != "prod" else "https://api.amadeus.com"
        
        # HTTP client and token management
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
        
        # Build the request payload for POST method (v2 structure)
        origin_destinations = [
            {
                "id": "1",
                "originLocationCode": origin.upper(),
                "destinationLocationCode": destination.upper(),
                "departureDateTimeRange": {"date": departure_date},
            }
        ]
        
        # Add return journey as separate origin-destination for round-trip
        if return_date:
            origin_destinations.append({
                "id": "2", 
                "originLocationCode": destination.upper(),
                "destinationLocationCode": origin.upper(),
                "departureDateTimeRange": {"date": return_date},
            })
            
        travelers = [{"id": str(i + 1), "travelerType": "ADULT"} for i in range(adults)]
        
        # Build cabin restrictions for all origin-destinations
        origin_destination_ids = [str(i + 1) for i in range(len(origin_destinations))]
        
        payload: Dict[str, Any] = {
            "currencyCode": currency,
            "originDestinations": origin_destinations,
            "travelers": travelers,
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": max_results,
                "flightFilters": {
                    "cabinRestrictions": [{"cabin": cabin, "coverage": "MOST_SEGMENTS", "originDestinationIds": origin_destination_ids}]
                }
            }
        }
        
        if non_stop is not None:
            payload["searchCriteria"]["flightFilters"]["connectionRestriction"] = {
                "maxNumberOfConnections": 0 if non_stop else 2
            }
            
        if max_price is not None:
            payload["searchCriteria"]["pricingOptions"] = {"includedCheckedBagsOnly": False}
            payload["searchCriteria"]["maxPrice"] = max_price

        headers = {
            **self._auth_headers(),
            "Content-Type": "application/json",
        }
        
        # Use POST method with JSON payload instead of GET with query params
        r = self._client.post(url, headers=headers, json=payload)
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


def create_direct_client(client_id: str = None, client_secret: str = None, host: str = "test") -> AmadeusDirectClient:
    """Factory function to create a direct Amadeus API client"""
    return AmadeusDirectClient(client_id, client_secret, host)