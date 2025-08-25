# Google Flights Usage Example - User Guide

## Getting Started

The Google Flights usage example (`examples/google_flights_usage.py`) shows you how to search for flights using Google's flight data through a Model Context Protocol (MCP) server. This guide will help you understand and use all the features available.

## What You Need

### 1. Google Flights MCP Server
The example connects to an external MCP server that scrapes Google Flights data. You need:

- The Google Flights MCP server running at: `/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py`
- Required Python packages: `fast-flights`, `fastmcp`, `aiohttp`

### 2. Install Dependencies
```bash
pip install pydantic asyncio
```

### 3. Server Setup
Make sure the Google Flights MCP server is available and can be run from the specified path.

## How to Run the Example

Navigate to your project directory and run:

```bash
python examples/google_flights_usage.py
```

The example will run three different demonstrations automatically.

## What the Example Shows

### 1. Complete Google Flights Demo

This is the main demonstration that shows all features:

**Features demonstrated:**
- **Airport Search**: Finding airports by typing "Los Angeles"
- **Travel Date Suggestions**: Getting optimal travel dates  
- **Flight Search**: Round-trip flights from LAX to JFK
- **Airport Information**: Details about specific airports
- **Available Tools**: What the MCP server can do
- **Trip Planning**: Getting travel planning prompts

**Example Output:**
```
=== Google Flights MCP Client Example ===

✓ Connected to Google Flights MCP server

1. Searching for airports with 'Los Angeles'...
Airport search results:
Found 3 airports matching 'Los Angeles':
Los Angeles International Airport, Los Angeles, CA, US (LAX)
Hollywood Burbank Airport, Burbank, CA, US (BUR)
Long Beach Airport, Long Beach, CA, US (LGB)

2. Getting suggested travel dates (30 days from now, 7-day trip)...
Suggested travel dates:
Departure date: 2025-05-25
Return date: 2025-06-01

3. Searching for round-trip flights LAX -> JFK...
Flight search results:
Found 12 flight options.

Option 1 [BEST OPTION]:
  Airline: United Airlines
  Departure: LAX at 08:00 AM
  Arrival: JFK at 04:30 PM
  Duration: 5h 30m
  Stops: Nonstop
  Price: $389
```

### 2. One-Way Flight Search Demo

Shows how to search for one-way flights with multiple passengers:

**Features:**
- One-way flights (no return date)
- Multiple passengers (2 adults, 1 child)
- Premium economy class
- Different route (SFO to LAX)

### 3. Airport Database Operations Demo

Demonstrates airport database management:

**Features:**
- Updating the airport database
- Getting all available airports
- Searching for specific airports (like "New York")

## Understanding Flight Search

### Search Parameters

You can customize your flight search with these parameters:

```python
search_args = FlightSearchArgs(
    from_airport="LAX",           # Departure airport (3-letter code)
    to_airport="JFK",            # Arrival airport (3-letter code)
    departure_date="2025-04-15", # Departure date (YYYY-MM-DD)
    return_date="2025-04-22",    # Return date (optional)
    adults=1,                    # Number of adults (1-9)
    children=0,                  # Number of children (0-9)
    infants_in_seat=0,           # Infants with seats (0-9)
    infants_on_lap=0,            # Infants on lap (0-9)
    seat_class="economy"         # Seat class
)
```

### Seat Classes Available
- `economy` - Standard economy class
- `premium_economy` - Premium economy with extra legroom
- `business` - Business class
- `first` - First class

### Airport Codes

If you don't know airport codes, use the airport search feature:

```python
# Find airports in a city
result = await client.airport_search("Tokyo")
```

**Popular Airport Codes:**
- **LAX** - Los Angeles International
- **JFK** - John F. Kennedy (New York)
- **SFO** - San Francisco International
- **ORD** - Chicago O'Hare
- **MIA** - Miami International
- **DEN** - Denver International

## Customizing Your Search

### Round-Trip vs One-Way

**Round-Trip Flight:**
```python
FlightSearchArgs(
    from_airport="BOS",
    to_airport="SEA", 
    departure_date="2025-07-15",
    return_date="2025-07-22",    # Include return date
    adults=1
)
```

**One-Way Flight:**
```python
FlightSearchArgs(
    from_airport="BOS",
    to_airport="SEA",
    departure_date="2025-07-15",
    # No return_date = one-way
    adults=1
)
```

### Family Travel

```python
FlightSearchArgs(
    from_airport="DFW",
    to_airport="LAX",
    departure_date="2025-08-01",
    return_date="2025-08-08",
    adults=2,           # Two parents
    children=2,         # Two children
    seat_class="economy"
)
```

### Business Travel

```python
FlightSearchArgs(
    from_airport="JFK",
    to_airport="SFO",
    departure_date="2025-09-10",
    return_date="2025-09-12",
    adults=1,
    seat_class="business"    # Business class
)
```

## Using Airport Features

### Finding Airports

```python
# Search by city name
airports = await client.airport_search("San Francisco")

# Search by partial airport name  
airports = await client.airport_search("International")

# Search by state
airports = await client.airport_search("California")
```

### Getting Airport Details

```python
# Get info about a specific airport
info = await client.get_airport_info("LAX")
```

### Updating Airport Database

```python
# Refresh the airport database with latest data
update = await client.update_airports_database()
```

## Travel Planning Features

### Getting Optimal Dates

```python
# Get dates 45 days from now for a 10-day trip
dates = await client.get_travel_dates(days_from_now=45, trip_length=10)
```

### Trip Planning Prompts

```python
# Get comprehensive trip planning guidance
prompt = await client.plan_trip_prompt("Tokyo")
```

### Comparing Destinations

```python
# Compare two potential destinations
comparison = await client.compare_destinations_prompt("Paris", "London")
```

## Understanding the Results

### Flight Information

Each flight result includes:
- **Airline**: Which airline operates the flight
- **Times**: Departure and arrival times (local time zones)
- **Duration**: Total flight time
- **Stops**: Number of connections
- **Price**: Cost in USD
- **Best Option**: Marked when it's the recommended choice

### Reading Flight Times

- Times are in local airport time zones
- Format: `08:00 AM` for departure, `04:30 PM` for arrival
- Duration shown as: `5h 30m` (5 hours, 30 minutes)

### Connection Information

For flights with stops:
```
Stops: 1 stop in Denver (DEN)
Duration: 7h 45m total (includes connection time)
```

## Troubleshooting

### Common Issues

**1. Server Connection Failed**
```
✗ Failed to connect to Google Flights MCP server
```
**Solution**: 
- Make sure the Google Flights MCP server is available
- Check the server path is correct
- Ensure required dependencies are installed

**2. Invalid Airport Code**
```
Validation error: String should have at most 3 characters
```
**Solution**:
- Use 3-letter IATA codes only (like "LAX", not "Los Angeles")
- Use airport search to find correct codes

**3. Invalid Date Format**
```
Validation error: String should match pattern '^\\d{4}-\\d{2}-\\d{2}$'
```
**Solution**:
- Use YYYY-MM-DD format (like "2025-06-15")
- Not MM/DD/YYYY or other formats

**4. Invalid Seat Class**
```
Value error: Seat class must be one of: economy, premium_economy, business, first
```
**Solution**:
- Use exact values: "economy", "premium_economy", "business", "first"
- All lowercase

### Getting Help

**Check connection status:**
```python
if not connected:
    print("Check server availability and path")
```

**Validate your search parameters:**
```python
try:
    search_args = FlightSearchArgs(...)
except ValidationError as e:
    print(f"Parameter error: {e}")
```

**Search for airport codes:**
```python
# If unsure about airport codes
result = await client.airport_search("your city name")
```

## Advanced Usage

### Checking Available Features

```python
# See what the server can do
tools = await client.list_tools()
resources = await client.list_resources()
```

### Custom Search Patterns

```python
# Last-minute travel (next week)
search_args = FlightSearchArgs(
    from_airport="your_airport",
    to_airport="destination",
    departure_date="2025-04-28",  # Next Monday
    return_date="2025-05-02",     # Friday
    adults=1,
    seat_class="economy"
)
```

```python
# Extended vacation (2+ weeks)
search_args = FlightSearchArgs(
    from_airport="JFK",
    to_airport="LHR",
    departure_date="2025-06-01",
    return_date="2025-06-21",     # 3 weeks later
    adults=2,
    seat_class="premium_economy"
)
```

## Next Steps

### Integration Ideas

1. **Travel Planning App**: Use the flight search in a larger travel application
2. **Price Monitoring**: Regular searches to track price changes
3. **AI Assistant**: Integrate with chat systems for flight recommendations
4. **Itinerary Builder**: Combine with hotel and activity searches

### Production Considerations

- **Error Handling**: Implement robust error handling for network issues
- **Rate Limiting**: Be mindful of search frequency to avoid rate limits
- **Caching**: Consider caching results for frequently searched routes
- **User Input**: Validate user inputs before creating search arguments

## Limitations

- **Real-time Pricing**: Prices may change between search and booking
- **Availability**: Flight availability depends on current inventory
- **Booking**: This tool is for search only, not booking flights
- **Server Dependency**: Requires the external MCP server to be running

## Support

- **Server Issues**: Check the Google Flights MCP server documentation
- **Client Issues**: Review the error messages for specific guidance
- **Validation Errors**: Use the airport search to verify codes and parameters