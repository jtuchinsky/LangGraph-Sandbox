"""
Google Flights MCP Client Package

This package provides an MCP client for connecting to Google Flights MCP server
that offers flight search, airport lookup, and travel planning functionality.
"""

from .client import (
    GoogleFlightsMCPClient,
    FlightSearchArgs,
    AirportSearchArgs,
    TravelDatesArgs,
    create_google_flights_client
)

# Main exports
__all__ = [
    "GoogleFlightsMCPClient",
    "FlightSearchArgs", 
    "AirportSearchArgs",
    "TravelDatesArgs",
    "create_google_flights_client"
]

# Backward compatibility and convenience aliases
GoogleFlightsClient = GoogleFlightsMCPClient
create_google_flights_mcp_client = create_google_flights_client