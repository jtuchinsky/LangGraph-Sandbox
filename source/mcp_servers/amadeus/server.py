import os
from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP
from ...mcp_clients.amadeus.client import AmadeusAPIClient

# ---------- Server Configuration ----------

load_dotenv()

AMADEUS_HOST = os.getenv("AMADEUS_HOST", "test").lower()
BASE_URL = "https://test.api.amadeus.com" if AMADEUS_HOST != "prod" else "https://api.amadeus.com"

CLIENT_ID = os.getenv("AMADEUS_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("AMADEUS_CLIENT_SECRET", "")

DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "USD")
DEFAULT_MAX_RESULTS = int(os.getenv("DEFAULT_MAX_RESULTS", "10"))

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("Missing AMADEUS_CLIENT_ID or AMADEUS_CLIENT_SECRET in environment.")

# ---------- Pydantic Schemas for MCP Tools ----------

class AutocompleteArgs(BaseModel):
    """Arguments for location autocomplete MCP tool"""
    query: str = Field(..., description="Free text to match city/airport")
    limit: int = Field(5, ge=1, le=20)
    sub_types: Optional[List[Literal["CITY", "AIRPORT"]]] = Field(default=["CITY", "AIRPORT"])

class SearchArgs(BaseModel):
    """Arguments for flight search MCP tool"""
    origin: str = Field(..., min_length=3, max_length=3, description="IATA code, e.g., JFK")
    destination: str = Field(..., min_length=3, max_length=3, description="IATA code, e.g., SFO")
    departure_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    return_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    adults: int = Field(1, ge=1, le=9)
    cabin: Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"] = "ECONOMY"
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    non_stop: Optional[bool] = None
    max_price: Optional[int] = Field(None, ge=1)
    max_results: int = Field(default=DEFAULT_MAX_RESULTS, ge=1, le=250)

    @field_validator("origin", "destination")
    @classmethod
    def uppercase_iata(cls, v: str) -> str:
        return v.upper()

class PriceArgs(BaseModel):
    """Arguments for flight offer pricing MCP tool"""
    # Expect the exact flightOffer you received from search (JSON object)
    flight_offer: Dict[str, Any]
    currency: Optional[str] = None  # Typically pricing will use the offer currency

# ---------- MCP Server & Tools ----------

app = FastMCP("amadeus-mcp")
api_client = AmadeusAPIClient(CLIENT_ID, CLIENT_SECRET, BASE_URL)

@app.tool(description="Autocomplete locations (CITY, AIRPORT). Returns Amadeus locations JSON.")
def autocomplete_locations(args: AutocompleteArgs) -> Any:
    """
    Example:
    {"query":"San Fra", "limit":5, "sub_types":["CITY","AIRPORT"]}
    """
    data = api_client.autocomplete_locations(args.query, args.limit, args.sub_types)
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
    return {"count": len(items), "items": items}

@app.tool(description="Search flight offers (one-way or round-trip). Returns Amadeus flight offers JSON.")
def search_flights(args: SearchArgs) -> Any:
    """
    Example:
    {
      "origin":"JFK","destination":"SFO",
      "departure_date":"2025-09-10","adults":1,
      "non_stop":false,"cabin":"ECONOMY","max_results":20
    }
    """
    currency = args.currency or DEFAULT_CURRENCY
    raw = api_client.search_flights(
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
    return {"count": len(offers), "offers": offers, "meta": meta}

@app.tool(description="Re-price a flight offer (pass `_full` offer from search). Returns pricing JSON.")
def price_offer(args: PriceArgs) -> Any:
    """
    Example:
    { "flight_offer": <offers[i]["_full"] from search>, "currency": "USD" }
    """
    result = api_client.price_offer(args.flight_offer, args.currency)
    # keep result as-is; agent can read updated totals, fare rules, etc.
    return result

def main():
    app.run()

if __name__ == "__main__":
    main()
