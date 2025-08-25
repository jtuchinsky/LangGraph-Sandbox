# Google Flights MCP Client

A Python client for connecting to the Google Flights MCP server, which provides flight search, airport lookup, and travel planning functionality using the fast-flights API.

## Features

- **Flight Search**: Search for one-way and round-trip flights between airports
- **Airport Lookup**: Search airports by name, city, or IATA code
- **Travel Planning**: Get suggested travel dates and trip planning prompts
- **Airport Database**: Access comprehensive airport information and updates
- **Pydantic Validation**: Strong type checking and input validation
- **Async Support**: Full asynchronous operation support

## Installation

The client is part of the lang_graph_sandbox project. Ensure you have the required dependencies:

```bash
pip install pydantic
```

## Usage

### Basic Usage

```python
import asyncio
from source.mcp_clients.google_flights import create_google_flights_client, FlightSearchArgs

async def main():
    # Create client
    client = create_google_flights_client()
    
    # Connect to Google Flights MCP server
    server_command = ["python", "/path/to/google-flights-mcp/src/flights-mcp-server.py"]
    connected = await client.connect_to_server(server_command)
    
    if connected:
        # Search airports
        airports = await client.airport_search("Los Angeles")
        print(airports["result"])
        
        # Search flights
        search_args = FlightSearchArgs(
            from_airport="LAX",
            to_airport="JFK", 
            departure_date="2025-04-15",
            return_date="2025-04-22",
            adults=1,
            seat_class="economy"
        )
        
        flights = await client.search_flights(search_args)
        print(flights["result"])
        
        # Disconnect
        await client.disconnect_from_server()

asyncio.run(main())
```

### Flight Search Parameters

The `FlightSearchArgs` model supports:

- `from_airport`: 3-letter IATA departure code (e.g., "LAX")
- `to_airport`: 3-letter IATA arrival code (e.g., "JFK") 
- `departure_date`: Departure date in YYYY-MM-DD format
- `return_date`: Optional return date for round-trip flights
- `adults`: Number of adult passengers (1-9, default: 1)
- `children`: Number of children (0-9, default: 0)
- `infants_in_seat`: Number of infants in seat (0-9, default: 0)
- `infants_on_lap`: Number of infants on lap (0-9, default: 0)
- `seat_class`: economy, premium_economy, business, or first (default: economy)

### Available Methods

#### Flight Operations
- `search_flights(search_args)` - Search for flights
- `get_travel_dates(days_from_now, trip_length)` - Get suggested dates

#### Airport Operations
- `airport_search(query)` - Search airports by name/city/code
- `get_all_airports()` - Get list of all available airports
- `get_airport_info(airport_code)` - Get specific airport information
- `update_airports_database()` - Update airport database

#### Travel Planning
- `plan_trip_prompt(destination)` - Get trip planning prompt
- `compare_destinations_prompt(dest1, dest2)` - Compare destinations

#### Server Management
- `connect_to_server(server_command)` - Connect to MCP server
- `disconnect_from_server()` - Disconnect from server
- `is_connected()` - Check connection status
- `list_tools()` - List available MCP tools
- `list_resources()` - List available MCP resources

## Examples

See `examples/google_flights_usage.py` for comprehensive usage examples including:

- Basic flight search
- Airport operations
- One-way vs round-trip flights
- Database management
- Error handling

## Requirements

- Google Flights MCP Server running at specified path
- Python 3.8+
- Pydantic for data validation
- MCP client infrastructure

## Server Requirements

The Google Flights MCP server requires:
- `fast-flights` Python package
- `aiohttp` for HTTP requests
- `fastmcp` for MCP server functionality

Ensure the server is running before connecting the client.

## Error Handling

All methods return a dictionary with:
- `success`: Boolean indicating operation success
- `result`: The actual result data (on success)
- `error`: Error message (on failure)
- `raw_response`: Raw MCP response (optional)

```python
result = await client.search_flights(search_args)
if result["success"]:
    print("Flight search successful!")
    print(result["result"])
else:
    print(f"Error: {result['error']}")
```