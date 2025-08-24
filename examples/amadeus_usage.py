#!/usr/bin/env python3
"""
Example usage of the Amadeus MCP client and server integration
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from source.mcp_clients.amadeus import create_amadeus_client, AmadeusMCPClient


async def example_direct_api_usage():
    """Example of using the Amadeus client directly (without MCP server)"""
    print("=== Direct API Usage Example ===")
    
    try:
        # Create client (credentials from environment)
        client = create_amadeus_client()
        
        # Example 1: Autocomplete locations
        print("\n1. Autocompleting locations for 'San Francisco'...")
        result = client.autocomplete_locations_direct("San Francisco", limit=3,  sub_types = ["CITY", "AIRPORT"])
        if result["success"]:
            print(f"Found {result['count']} locations:")
            for item in result["items"]:
                print(f"  - {item['name']} ({item['iata']}) - {item['type']}")
        else:
            print(f"Error: {result.get('error')}")
        
        # Example 2: Search flights
        print("\n2. Searching round-trip flights EWR -> TLV...")
        search_args = {
            "origin": "EWR",
            "destination": "TLV",
            "departure_date": "2025-09-19",
            "return_date": "2025-10-05",
            "adults": 1,
            "cabin": "ECONOMY",
            "max_results": 15
        }
        
        flight_result = client.search_flights_direct(search_args)
        if flight_result["success"]:
            print(f"Found {flight_result['count']} flight offers:")
            # Show all requested results (up to max_results from search_args)
            display_count = min(len(flight_result["offers"]), search_args.get("max_results", 5))
            for i, offer in enumerate(flight_result["offers"][:display_count], 1):
                # Determine if round-trip or one-way
                trip_type = "Round-trip" if len(offer["itineraries"]) > 1 else "One-way"
                print(f"\n  === Offer {i}: {offer['oneAdultTotal']} {offer['currency']} ({trip_type}) ===")
                
                for j, itin in enumerate(offer["itineraries"], 1):
                    direction = "Outbound" if j == 1 else "Return"
                    print(f"    {direction} Journey - Total Duration: {itin['duration']}")
                    
                    for k, seg in enumerate(itin["segments"]):
                        # Flight info
                        airline = seg.get('carrierCode', 'N/A')
                        flight_num = seg.get('number', 'N/A')
                        operating = seg.get('operating')
                        operator_info = f" (operated by {operating})" if operating and operating != airline else ""
                        
                        print(f"      Flight {airline}{flight_num}{operator_info}")
                        print(f"      {seg['from']} -> {seg['to']}")
                        print(f"      Depart: {seg['depTime']} | Arrive: {seg['arrTime']}")
                        print(f"      Duration: {seg['duration']} | Aircraft: {seg.get('aircraft', 'N/A')}")
                        
                        # Connection time (if not the last segment)
                        if k < len(itin["segments"]) - 1:
                            print(f"      Connection at {seg['to']}")
                
                # Show pricing breakdown if available
                if len(offer["itineraries"]) > 1:
                    print(f"    💰 Total Price: {offer['oneAdultTotal']} {offer['currency']} (for complete round-trip)")
        else:
            print(f"Error: {flight_result.get('error')}")
        
        # Close the client
        client.close()
        
    except Exception as e:
        print(f"Error in direct API usage: {e}")


async def example_mcp_server_usage():
    """Example of using the Amadeus client with MCP server"""
    print("\n=== MCP Server Usage Example ===")
    
    try:
        # Create client
        client = create_amadeus_client()
        
        # Connect to MCP server (assuming server is running)
        server_command = ["python", "-m", "source.mcp_servers.amadeus.server"]
        connected = await client.connect_to_mcp_server(server_command)
        
        if connected:
            print("✓ Connected to Amadeus MCP server")
            
            # Example 1: MCP autocomplete
            print("\n1. Using MCP server to autocomplete 'Los Angeles'...")
            result = await client.autocomplete_locations_mcp("Los Angeles", limit=2)
            if result.get("success"):
                print("MCP autocomplete successful")
            else:
                print(f"MCP Error: {result.get('error')}")
            
            # Example 2: MCP flight search
            print("\n2. Using MCP server to search flights...")
            search_args = {
                "origin": "LAX",
                "destination": "JFK",
                "departure_date": "2025-04-01",
                "adults": 1,
                "cabin": "ECONOMY",
                "max_results": 1
            }
            
            flight_result = await client.search_flights_mcp(search_args)
            if flight_result.get("success"):
                print("MCP flight search successful")
            else:
                print(f"MCP Error: {flight_result.get('error')}")
            
            await client.disconnect_from_mcp_server()
            print("✓ Disconnected from MCP server")
            
        else:
            print("✗ Failed to connect to MCP server")
            print("Make sure the server is running with: python -m source.mcp_servers.amadeus.server")
        
        client.close()
        
    except Exception as e:
        print(f"Error in MCP server usage: {e}")


async def example_hybrid_usage():
    """Example showing fallback from MCP to direct API"""
    print("\n=== Hybrid Usage Example (MCP with Direct API Fallback) ===")
    
    try:
        client = create_amadeus_client()
        
        # Try to connect to MCP server (may fail)
        server_command = ["python", "-m", "source.mcp_servers.amadeus.server"]
        await client.connect_to_mcp_server(server_command)
        
        # Use convenience methods that automatically fallback
        print("\n1. Autocomplete with fallback...")
        result = await client.autocomplete_locations("Miami", limit=2, prefer_mcp=True)
        print(f"Result: {result.get('success')} - Found {result.get('count', 0)} items")
        
        print("\n2. Flight search with fallback...")
        search_args = {
            "origin": "MIA",
            "destination": "LAX",
            "departure_date": "2025-05-15",
            "adults": 1,
            "cabin": "ECONOMY",
            "max_results": 1
        }
        
        flight_result = await client.search_flights(search_args, prefer_mcp=True)
        print(f"Flight search: {flight_result.get('success')} - Found {flight_result.get('count', 0)} offers")
        
        await client.disconnect_from_mcp_server()
        client.close()
        
    except Exception as e:
        print(f"Error in hybrid usage: {e}")


async def main():
    """Run all examples"""
    print("Amadeus MCP Client Examples")
    print("=" * 40)
    
    # Run examples
    await example_direct_api_usage()
    
    print("\n" + "=" * 40)
    print("Examples completed!")


if __name__ == "__main__":
    asyncio.run(main())