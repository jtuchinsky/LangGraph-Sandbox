#!/usr/bin/env python3
"""
Example usage of the Google Flights MCP client
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from source.mcp_clients.google_flights import create_google_flights_client, FlightSearchArgs


async def example_google_flights_usage():
    """Example of using the Google Flights MCP client"""
    print("=== Google Flights MCP Client Example ===")
    
    try:
        # Create client
        client = create_google_flights_client()
        
        # Connect to MCP server (adjust path as needed)
        server_command = ["python", "/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py"]
        print("\nConnecting to Google Flights MCP server...")
        connected = await client.connect_to_server(server_command)
        
        if not connected:
            print("✗ Failed to connect to Google Flights MCP server")
            print("Make sure the server is available at the specified path")
            return
        
        print("✓ Connected to Google Flights MCP server")
        
        # Example 1: Airport search
        print("\n1. Searching for airports with 'Los Angeles'...")
        airport_result = await client.airport_search("Los Angeles")
        if airport_result["success"]:
            print("Airport search results:")
            print(airport_result["result"])
        else:
            print(f"Airport search error: {airport_result.get('error')}")
        
        # Example 2: Get travel dates
        print("\n2. Getting suggested travel dates (30 days from now, 7-day trip)...")
        dates_result = await client.get_travel_dates(days_from_now=30, trip_length=7)
        if dates_result["success"]:
            print("Suggested travel dates:")
            print(dates_result["result"])
        else:
            print(f"Travel dates error: {dates_result.get('error')}")
        
        # Example 3: Search flights
        print("\n3. Searching for round-trip flights LAX -> JFK...")
        
        # Create flight search arguments
        search_args = FlightSearchArgs(
            from_airport="LAX",
            to_airport="JFK",
            departure_date="2025-04-15",
            return_date="2025-04-22",
            adults=1,
            seat_class="economy"
        )
        
        flight_result = await client.search_flights(search_args)
        if flight_result["success"]:
            print("Flight search results:")
            print(flight_result["result"])
        else:
            print(f"Flight search error: {flight_result.get('error')}")
        
        # Example 4: Get specific airport info
        print("\n4. Getting info for airport code 'JFK'...")
        airport_info = await client.get_airport_info("JFK")
        if airport_info["success"]:
            print("Airport info:")
            print(airport_info["result"])
        else:
            print(f"Airport info error: {airport_info.get('error')}")
        
        # Example 5: List available tools
        print("\n5. Listing available MCP tools...")
        tools_result = await client.list_tools()
        if tools_result["success"]:
            print("Available tools:")
            for tool in tools_result["tools"]:
                name = tool.get("name", "Unknown")
                description = tool.get("description", "No description")
                print(f"  - {name}: {description}")
        else:
            print(f"Tools listing error: {tools_result.get('error')}")
        
        # Example 6: Trip planning prompt
        print("\n6. Getting trip planning prompt for Tokyo...")
        trip_prompt = await client.plan_trip_prompt("Tokyo")
        if trip_prompt["success"]:
            print("Trip planning prompt:")
            print(trip_prompt["result"][:200] + "..." if len(trip_prompt["result"]) > 200 else trip_prompt["result"])
        else:
            print(f"Trip prompt error: {trip_prompt.get('error')}")
        
        # Disconnect from server
        await client.disconnect_from_server()
        print("\n✓ Disconnected from Google Flights MCP server")
        
    except Exception as e:
        print(f"Error in Google Flights usage example: {e}")


async def example_one_way_flight_search():
    """Example of searching for one-way flights"""
    print("\n=== One-Way Flight Search Example ===")
    
    try:
        client = create_google_flights_client()
        
        # Connect to server
        server_command = ["python", "/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py"]
        connected = await client.connect_to_server(server_command)
        
        if not connected:
            print("✗ Failed to connect to server")
            return
        
        print("✓ Connected to server")
        
        # Search one-way flights
        search_args = FlightSearchArgs(
            from_airport="SFO",
            to_airport="LAX", 
            departure_date="2025-05-01",
            # No return_date for one-way
            adults=2,
            children=1,
            seat_class="premium_economy"
        )
        
        print(f"\nSearching one-way flights: {search_args.from_airport} -> {search_args.to_airport}")
        print(f"Departure: {search_args.departure_date}")
        print(f"Passengers: {search_args.adults} adults, {search_args.children} children")
        print(f"Seat class: {search_args.seat_class}")
        
        result = await client.search_flights(search_args)
        if result["success"]:
            print("\nOne-way flight results:")
            print(result["result"])
        else:
            print(f"One-way flight search error: {result.get('error')}")
        
        await client.disconnect_from_server()
        
    except Exception as e:
        print(f"Error in one-way flight example: {e}")


async def example_airport_database_operations():
    """Example of airport database operations"""
    print("\n=== Airport Database Operations Example ===")
    
    try:
        client = create_google_flights_client()
        
        # Connect to server
        server_command = ["python", "/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py"]
        connected = await client.connect_to_server(server_command)
        
        if not connected:
            print("✗ Failed to connect to server")
            return
        
        print("✓ Connected to server")
        
        # Note: Airport database is automatically loaded by the server on startup (7,861 airports)
        # No need to call update_airports_database() unless you want to refresh the data
        
        # Get all airports (first 100)
        print("\n1. Getting all airports...")
        all_airports = await client.get_all_airports()
        if all_airports["success"]:
            print("All airports (partial list):")
            # Show first few lines only
            lines = all_airports["result"].split('\n')[:10]
            for line in lines:
                print(line)
            if len(all_airports["result"].split('\n')) > 10:
                print("... (truncated)")
        else:
            print(f"All airports error: {all_airports.get('error')}")
        
        # Search for specific airports  
        print("\n2. Searching for airports with 'New York'...")
        ny_airports = await client.airport_search("New York")
        if ny_airports["success"]:
            print("New York area airports:")
            print(ny_airports["result"])
        else:
            print(f"NY airports search error: {ny_airports.get('error')}")
        
        await client.disconnect_from_server()
        
    except Exception as e:
        print(f"Error in airport database example: {e}")


async def main():
    """Run all Google Flights examples"""
    print("Google Flights MCP Client Examples")
    print("=" * 50)
    
    # Run examples
    await example_google_flights_usage()
    
    print("\n" + "=" * 50)
    
    await example_one_way_flight_search()
    
    print("\n" + "=" * 50)
    
    await example_airport_database_operations()
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())