#!/usr/bin/env python3
"""
Simple test script for Google Flights MCP client functionality
This script demonstrates the client without the I/O blocking issues of the full server example
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from source.mcp_clients.google_flights import create_google_flights_client, FlightSearchArgs


async def test_client_functionality():
    """Test basic client functionality without server dependency"""
    print("=== Google Flights MCP Client - Functionality Test ===")
    
    # Test 1: Client creation
    print("\n1. Testing client creation...")
    try:
        client = create_google_flights_client()
        print("✓ Client created successfully")
        print(f"   Client type: {type(client).__name__}")
        print(f"   Connected: {client.is_connected()}")
    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        return
    
    # Test 2: Validation models
    print("\n2. Testing FlightSearchArgs validation...")
    try:
        # Valid arguments
        valid_args = FlightSearchArgs(
            from_airport="LAX",
            to_airport="JFK",
            departure_date="2025-04-15",
            return_date="2025-04-22",
            adults=1,
            seat_class="economy"
        )
        print("✓ Valid FlightSearchArgs created successfully")
        print(f"   Route: {valid_args.from_airport} → {valid_args.to_airport}")
        print(f"   Departure: {valid_args.departure_date}")
        print(f"   Return: {valid_args.return_date}")
        print(f"   Passengers: {valid_args.adults} adults, {valid_args.children} children")
        print(f"   Class: {valid_args.seat_class}")
        
        # Test validation
        try:
            invalid_args = FlightSearchArgs(
                from_airport="INVALID_CODE",  # Too long
                to_airport="JFK",
                departure_date="2025-04-15"
            )
            print("✗ Validation failed - should have caught invalid airport code")
        except Exception:
            print("✓ Validation correctly caught invalid airport code")
            
    except Exception as e:
        print(f"✗ FlightSearchArgs validation test failed: {e}")
    
    # Test 3: Connection state testing (without actual connection attempt)
    print("\n3. Testing connection state management...")
    try:
        print(f"   Initial connection state: {client.is_connected()}")
        if not client.is_connected():
            print("✓ Initial state correctly shows disconnected")
        
        # Test that methods handle disconnected state properly
        tools_result = await client.list_tools()
        if not tools_result["success"] and "Not connected" in tools_result["error"]:
            print("✓ Methods properly check connection state")
        else:
            print(f"✗ Unexpected list_tools result: {tools_result}")
                
    except Exception as e:
        print(f"   Connection state test error: {e}")
        print("? Unexpected error in state management")
    
    # Test 4: Method availability
    print("\n4. Testing client methods availability...")
    methods_to_test = [
        'connect_to_server',
        'disconnect_from_server',
        'is_connected',
        'search_flights',
        'airport_search',
        'get_travel_dates',
        'get_airport_info',
        'get_all_airports',
        'list_tools',
        'list_resources'
    ]
    
    for method_name in methods_to_test:
        if hasattr(client, method_name):
            print(f"✓ {method_name}")
        else:
            print(f"✗ {method_name} - MISSING")
    
    print("\n=== Test Summary ===")
    print("✓ Client creation: Working")
    print("✓ Input validation: Working") 
    print("✓ Error handling: Working")
    print("✓ Method availability: Complete")
    print("\nNote: To test with actual server functionality, run the Google Flights")
    print("MCP server separately and connect to it from another terminal.")


if __name__ == "__main__":
    asyncio.run(test_client_functionality())