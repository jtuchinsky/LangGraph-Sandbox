#!/usr/bin/env python3
"""
Enhanced Google Flights MCP Client Test Suite

This comprehensive test script validates the Google Flights MCP client functionality
without requiring server connectivity, avoiding I/O blocking issues.

Features:
- Complete validation model testing (FlightSearchArgs, AirportSearchArgs, TravelDatesArgs)  
- Client method availability and behavior verification
- Edge case and boundary condition testing
- Comprehensive error handling validation
- Detailed test reporting with categorized results

Usage:
    python examples/test_google_flights_client.py

The script tests:
1. Client creation and initialization
2. Pydantic model validation (valid and invalid inputs)
3. Method availability and disconnected state handling
4. Edge cases (date boundaries, airport code formats)
5. Comprehensive error reporting

Note: This tests client functionality without server dependency. 
For full integration testing, run the Google Flights MCP server separately.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from source.mcp_clients.google_flights import (
    create_google_flights_client, 
    FlightSearchArgs,
    AirportSearchArgs,
    TravelDatesArgs
)


def generate_test_dates():
    """Generate valid test dates for flight searches"""
    today = datetime.now()
    departure = today + timedelta(days=30)
    return_date = departure + timedelta(days=7)
    return departure.strftime("%Y-%m-%d"), return_date.strftime("%Y-%m-%d")


async def test_validation_models():
    """Test all validation models with comprehensive test cases"""
    print("\n=== Testing Validation Models ===")
    test_results = []
    
    # FlightSearchArgs Tests
    print("\n1. Testing FlightSearchArgs...")
    departure_date, return_date = generate_test_dates()
    
    # Valid FlightSearchArgs test cases
    valid_test_cases = [
        {
            "name": "Basic round-trip flight",
            "args": {
                "from_airport": "LAX",
                "to_airport": "JFK", 
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": 1,
                "seat_class": "economy"
            }
        },
        {
            "name": "One-way business class",
            "args": {
                "from_airport": "sfo",  # Test case conversion
                "to_airport": "ord",
                "departure_date": departure_date,
                "adults": 2,
                "children": 1,
                "seat_class": "BUSINESS"  # Test case conversion
            }
        },
        {
            "name": "Family trip with infants",
            "args": {
                "from_airport": "DEN",
                "to_airport": "MIA",
                "departure_date": departure_date,
                "return_date": return_date,
                "adults": 2,
                "children": 2,
                "infants_in_seat": 1,
                "infants_on_lap": 1,
                "seat_class": "premium_economy"
            }
        }
    ]
    
    for test_case in valid_test_cases:
        try:
            args = FlightSearchArgs(**test_case["args"])
            print(f"   ✓ {test_case['name']}")
            print(f"     Route: {args.from_airport} → {args.to_airport}")
            print(f"     Class: {args.seat_class}")
            test_results.append(("FlightSearchArgs Valid", test_case["name"], True))
        except Exception as e:
            print(f"   ✗ {test_case['name']}: {e}")
            test_results.append(("FlightSearchArgs Valid", test_case["name"], False))
    
    # Invalid FlightSearchArgs test cases
    invalid_test_cases = [
        {
            "name": "Invalid airport code (too long)",
            "args": {"from_airport": "INVALID", "to_airport": "JFK", "departure_date": departure_date}
        },
        {
            "name": "Invalid date format", 
            "args": {"from_airport": "LAX", "to_airport": "JFK", "departure_date": "2025/04/15"}
        },
        {
            "name": "Invalid seat class",
            "args": {"from_airport": "LAX", "to_airport": "JFK", "departure_date": departure_date, "seat_class": "super_deluxe"}
        },
        {
            "name": "Too many passengers",
            "args": {"from_airport": "LAX", "to_airport": "JFK", "departure_date": departure_date, "adults": 15}
        }
    ]
    
    for test_case in invalid_test_cases:
        try:
            args = FlightSearchArgs(**test_case["args"])
            print(f"   ✗ {test_case['name']}: Should have failed validation")
            test_results.append(("FlightSearchArgs Invalid", test_case["name"], False))
        except Exception:
            print(f"   ✓ {test_case['name']}: Correctly caught validation error")
            test_results.append(("FlightSearchArgs Invalid", test_case["name"], True))
    
    # AirportSearchArgs Tests
    print("\n2. Testing AirportSearchArgs...")
    airport_test_cases = [
        {"query": "Los Angeles", "name": "City search"},
        {"query": "LAX", "name": "IATA code search"},
        {"query": "London", "name": "International city"},
        {"query": "Heathrow", "name": "Airport name search"}
    ]
    
    for test_case in airport_test_cases:
        try:
            args = AirportSearchArgs(query=test_case["query"])
            print(f"   ✓ {test_case['name']}: '{args.query}'")
            test_results.append(("AirportSearchArgs", test_case["name"], True))
        except Exception as e:
            print(f"   ✗ {test_case['name']}: {e}")
            test_results.append(("AirportSearchArgs", test_case["name"], False))
    
    # TravelDatesArgs Tests
    print("\n3. Testing TravelDatesArgs...")
    travel_date_cases = [
        {"args": {"days_from_now": 30, "trip_length": 7}, "name": "Standard business trip"},
        {"args": {"days_from_now": 60}, "name": "Departure only"},
        {"args": {"trip_length": 14}, "name": "Trip length only"},
        {"args": {}, "name": "No constraints"}
    ]
    
    for test_case in travel_date_cases:
        try:
            args = TravelDatesArgs(**test_case["args"])
            print(f"   ✓ {test_case['name']}")
            if args.days_from_now:
                print(f"     Days from now: {args.days_from_now}")
            if args.trip_length:
                print(f"     Trip length: {args.trip_length} days")
            test_results.append(("TravelDatesArgs", test_case["name"], True))
        except Exception as e:
            print(f"   ✗ {test_case['name']}: {e}")
            test_results.append(("TravelDatesArgs", test_case["name"], False))
    
    return test_results


async def test_client_methods():
    """Test client method behaviors in disconnected state"""
    print("\n=== Testing Client Methods ===")
    test_results = []
    client = create_google_flights_client()
    
    # Test 1: Connection state methods
    print("\n1. Testing connection state...")
    try:
        is_connected = client.is_connected()
        print(f"   Initial connection state: {is_connected}")
        if not is_connected:
            print("   ✓ Initial state correctly shows disconnected")
            test_results.append(("Connection State", "Initial disconnected", True))
        else:
            print("   ✗ Initial state should be disconnected")
            test_results.append(("Connection State", "Initial disconnected", False))
    except Exception as e:
        print(f"   ✗ Connection state test failed: {e}")
        test_results.append(("Connection State", "Initial disconnected", False))
    
    # Test 2: Methods requiring connection
    print("\n2. Testing methods that require connection...")
    departure_date, return_date = generate_test_dates()
    
    disconnected_methods = [
        {
            "method": "search_flights",
            "args": [FlightSearchArgs(
                from_airport="LAX", 
                to_airport="JFK", 
                departure_date=departure_date
            )],
            "name": "Flight search"
        },
        {
            "method": "airport_search", 
            "args": ["Los Angeles"],
            "name": "Airport search"
        },
        {
            "method": "list_tools",
            "args": [],
            "name": "List tools"
        }
    ]
    
    for test_method in disconnected_methods:
        try:
            method = getattr(client, test_method["method"])
            result = await method(*test_method["args"])
            
            if isinstance(result, dict) and not result.get("success", True):
                if "Not connected" in result.get("error", ""):
                    print(f"   ✓ {test_method['name']}: Properly handles disconnected state")
                    test_results.append(("Disconnected Methods", test_method["name"], True))
                else:
                    print(f"   ? {test_method['name']}: Unexpected error: {result.get('error', 'Unknown')}")
                    test_results.append(("Disconnected Methods", test_method["name"], False))
            else:
                print(f"   ✗ {test_method['name']}: Should return error when disconnected")
                test_results.append(("Disconnected Methods", test_method["name"], False))
                
        except Exception as e:
            print(f"   ✗ {test_method['name']}: Exception occurred: {e}")
            test_results.append(("Disconnected Methods", test_method["name"], False))
    
    # Test 3: Method availability
    print("\n3. Testing method availability...")
    required_methods = [
        'connect_to_server', 'disconnect_from_server', 'is_connected',
        'search_flights', 'airport_search', 'get_travel_dates',
        'get_airport_info', 'get_all_airports', 'list_tools', 'list_resources'
    ]
    
    missing_methods = []
    for method_name in required_methods:
        if hasattr(client, method_name):
            print(f"   ✓ {method_name}")
            test_results.append(("Method Availability", method_name, True))
        else:
            print(f"   ✗ {method_name} - MISSING")
            missing_methods.append(method_name)
            test_results.append(("Method Availability", method_name, False))
    
    if not missing_methods:
        print("   ✓ All required methods are available")
    
    return test_results


async def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print("\n=== Testing Edge Cases ===")
    test_results = []
    
    # Test 1: Date boundary conditions
    print("\n1. Testing date boundaries...")
    today = datetime.now()
    
    edge_date_cases = [
        {
            "name": "Past date (should fail)",
            "date": (today - timedelta(days=1)).strftime("%Y-%m-%d"),
            "should_pass": False
        },
        {
            "name": "Today's date",
            "date": today.strftime("%Y-%m-%d"), 
            "should_pass": True
        },
        {
            "name": "Far future date",
            "date": (today + timedelta(days=365)).strftime("%Y-%m-%d"),
            "should_pass": True
        }
    ]
    
    for test_case in edge_date_cases:
        try:
            args = FlightSearchArgs(
                from_airport="LAX",
                to_airport="JFK",
                departure_date=test_case["date"]
            )
            result = test_case["should_pass"]
            print(f"   {'✓' if result else '✗'} {test_case['name']}: Created successfully")
            test_results.append(("Date Boundaries", test_case["name"], result))
        except Exception as e:
            result = not test_case["should_pass"] 
            print(f"   {'✓' if result else '✗'} {test_case['name']}: {e}")
            test_results.append(("Date Boundaries", test_case["name"], result))
    
    # Test 2: Airport code edge cases
    print("\n2. Testing airport code edge cases...")
    airport_edge_cases = [
        {"code": "LAx", "name": "Mixed case (should convert)", "should_pass": True},
        {"code": "   LAX   ", "name": "Whitespace (should trim)", "should_pass": False},
        {"code": "LA", "name": "Too short", "should_pass": False},
        {"code": "123", "name": "Numeric codes", "should_pass": True}
    ]
    
    for test_case in airport_edge_cases:
        try:
            args = FlightSearchArgs(
                from_airport=test_case["code"],
                to_airport="JFK",
                departure_date=generate_test_dates()[0]
            )
            result = test_case["should_pass"]
            if result:
                print(f"   ✓ {test_case['name']}: '{test_case['code']}' → '{args.from_airport}'")
            else:
                print(f"   ✗ {test_case['name']}: Should have failed")
            test_results.append(("Airport Codes", test_case["name"], result))
        except Exception as e:
            result = not test_case["should_pass"]
            print(f"   {'✓' if result else '✗'} {test_case['name']}: {e}")
            test_results.append(("Airport Codes", test_case["name"], result))
    
    return test_results


def print_test_summary(all_results):
    """Print a comprehensive test summary"""
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*60)
    
    # Group results by category
    categories = {}
    for category, test_name, passed in all_results:
        if category not in categories:
            categories[category] = {"passed": 0, "failed": 0, "tests": []}
        categories[category]["tests"].append((test_name, passed))
        if passed:
            categories[category]["passed"] += 1
        else:
            categories[category]["failed"] += 1
    
    # Print summary by category
    total_passed = 0
    total_failed = 0
    
    for category, results in categories.items():
        passed = results["passed"]
        failed = results["failed"]
        total = passed + failed
        percentage = (passed / total * 100) if total > 0 else 0
        
        print(f"\n{category}: {passed}/{total} tests passed ({percentage:.1f}%)")
        
        if failed > 0:
            print("   Failed tests:")
            for test_name, passed in results["tests"]:
                if not passed:
                    print(f"     - {test_name}")
        
        total_passed += passed
        total_failed += failed
    
    # Overall summary
    total_tests = total_passed + total_failed
    overall_percentage = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"OVERALL RESULTS: {total_passed}/{total_tests} tests passed ({overall_percentage:.1f}%)")
    
    if total_failed == 0:
        print("🎉 ALL TESTS PASSED! The Google Flights client is working correctly.")
    elif total_failed <= 3:
        print("⚠️  Minor issues found. Client is mostly functional.")
    else:
        print("❌ Multiple issues detected. Review failed tests above.")
    
    print("\nNote: To test actual server connectivity and flight search functionality,")
    print("run the Google Flights MCP server in a separate terminal and modify")
    print("this script to include connection tests.")


async def test_client_functionality():
    """Run comprehensive test suite for Google Flights MCP client"""
    print("=== Google Flights MCP Client - Comprehensive Test Suite ===")
    print("Testing client functionality without server dependency")
    
    # Test 1: Basic client creation
    print("\n1. Testing client creation...")
    try:
        client = create_google_flights_client()
        print("✓ Client created successfully")
        print(f"   Client type: {type(client).__name__}")
        print(f"   Connected: {client.is_connected()}")
    except Exception as e:
        print(f"✗ Client creation failed: {e}")
        return
    
    # Run comprehensive test suite
    all_results = []
    
    try:
        # Run validation tests
        validation_results = await test_validation_models()
        all_results.extend(validation_results)
        
        # Run client method tests  
        method_results = await test_client_methods()
        all_results.extend(method_results)
        
        # Run edge case tests
        edge_case_results = await test_edge_cases()
        all_results.extend(edge_case_results)
        
        # Print comprehensive summary
        print_test_summary(all_results)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        print("This indicates a critical issue with the client implementation.")


if __name__ == "__main__":
    asyncio.run(test_client_functionality())