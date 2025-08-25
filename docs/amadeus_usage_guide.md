# Amadeus Usage Example - User Guide

## Getting Started

The Amadeus usage example (`examples/amadeus_usage.py`) demonstrates how to search for flights and get airport information using the Amadeus Travel API. This guide will help you understand and use the different features available.

## Prerequisites

### 1. Amadeus API Credentials
You need to register with Amadeus for Developers to get your API credentials:

1. Visit [Amadeus for Developers](https://developers.amadeus.com/)
2. Create an account and register your application
3. Get your `Client ID` and `Client Secret`

### 2. Environment Setup
Create a `.env` file in your project root:

```env
AMADEUS_CLIENT_ID=your_client_id_here
AMADEUS_CLIENT_SECRET=your_client_secret_here
AMADEUS_HOST=test  # Use "test" for testing, "prod" for production
```

### 3. Install Dependencies
```bash
pip install httpx pydantic python-dotenv
```

## How to Run the Example

Navigate to your project directory and run:

```bash
python examples/amadeus_usage.py
```

The example will demonstrate three different ways to use the Amadeus client.

## What the Example Does

### 1. Direct API Usage (Recommended for Most Users)

This approach connects directly to the Amadeus API without requiring a separate server.

**What it shows:**
- **Airport Search**: Finding airports by typing "San Francisco"
- **Round-trip Flight Search**: Looking for flights from Newark (EWR) to Tel Aviv (TLV)

**Example Output:**
```
=== Direct API Usage Example ===

1. Autocompleting locations for 'San Francisco'...
Found 3 locations:
  - San Francisco International Airport (SFO) - AIRPORT
  - San Francisco, CA, US (SFO) - CITY
  - San Francisco Bay Oakland International Airport (OAK) - AIRPORT

2. Searching round-trip flights EWR -> TLV...
Found 15 flight offers:

  === Offer 1: 1250.85 USD (Round-trip) ===
    Outbound Journey - Total Duration: PT11H25M
      Flight LH441
      EWR -> FRA
      Depart: 2025-09-19T22:20:00 | Arrive: 2025-09-20T11:45:00
      Duration: PT7H25M | Aircraft: 346
      
    Return Journey - Total Duration: PT13H10M
      Flight LH686
      TLV -> FRA
      Depart: 2025-10-05T14:50:00 | Arrive: 2025-10-05T18:40:00
      Duration: PT4H50M | Aircraft: 321
    💰 Total Price: 1250.85 USD (for complete round-trip)
```

### 2. MCP Server Usage (Advanced Users)

This approach uses a Model Context Protocol (MCP) server for integration with AI systems.

**When to use:**
- Building AI assistants that need flight data
- Integrating with chat systems
- When you need structured, AI-friendly responses

### 3. Hybrid Usage (Best of Both Worlds)

This automatically tries the MCP server first, then falls back to direct API if the server isn't available.

## Understanding the Flight Search

### Search Parameters

The example searches for flights with these parameters:

```python
search_args = {
    "origin": "EWR",                 # Newark Airport
    "destination": "TLV",            # Tel Aviv Airport
    "departure_date": "2025-09-19",  # September 19, 2025
    "return_date": "2025-10-05",     # October 5, 2025 (for round-trip)
    "adults": 1,                     # One adult passenger
    "cabin": "ECONOMY",              # Economy class
    "max_results": 15                # Show up to 15 flight options
}
```

### How to Modify the Search

You can easily modify the example to search for different flights:

1. **Change Airports**: Update `origin` and `destination` with different 3-letter airport codes
2. **Change Dates**: Update the departure and return dates (format: YYYY-MM-DD)
3. **Passengers**: Change the number of adults
4. **Cabin Class**: Choose from "ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"
5. **Results**: Adjust `max_results` to see more or fewer options

### Airport Codes

If you don't know the 3-letter code for an airport, the example shows how to search:

```python
# This will help you find airport codes
result = client.autocomplete_locations_direct("Los Angeles", limit=5)
```

Common airport codes:
- **JFK** - John F. Kennedy International (New York)
- **LAX** - Los Angeles International
- **LHR** - London Heathrow
- **CDG** - Charles de Gaulle (Paris)
- **NRT** - Narita International (Tokyo)

## Understanding the Results

### Flight Information Displayed

For each flight offer, you'll see:

- **Price**: Total cost in USD (or specified currency)
- **Trip Type**: Round-trip or One-way
- **Journey Details**: For each leg of the trip:
  - Flight number and airline code
  - Departure and arrival airports
  - Departure and arrival times
  - Flight duration
  - Aircraft type
  - Operating airline (if different from marketing airline)

### Reading Flight Times

Times are shown in ISO format:
- `2025-09-19T22:20:00` = September 19, 2025 at 10:20 PM
- Times are typically in local airport time

### Understanding Connections

If a flight has connections, you'll see multiple segments:
```
Flight LH441
EWR -> FRA  (Newark to Frankfurt)
Connection at FRA

Flight LH686  
FRA -> TLV  (Frankfurt to Tel Aviv)
```

## Customizing the Example

### Search for Different Routes

```python
# Example: Search Los Angeles to New York
search_args = {
    "origin": "LAX",
    "destination": "JFK", 
    "departure_date": "2025-06-15",
    "adults": 2,                    # Two passengers
    "cabin": "BUSINESS",            # Business class
    "max_results": 10
}
```

### One-Way Flights

```python
# Remove return_date for one-way flights
search_args = {
    "origin": "SFO",
    "destination": "SEA",
    "departure_date": "2025-07-04",
    # No return_date = one-way flight
    "adults": 1,
    "cabin": "ECONOMY",
    "max_results": 5
}
```

### Different Passenger Configurations

```python
# Family with children
search_args = {
    "origin": "DFW",
    "destination": "ORD",
    "departure_date": "2025-08-20",
    "adults": 2,        # Two adults
    "children": 2,      # Two children (if supported by your client version)
    "cabin": "ECONOMY",
    "max_results": 8
}
```

## Troubleshooting

### Common Issues

**1. Authentication Error (401)**
- Check your `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET`
- Make sure they're correctly set in your `.env` file
- Verify your Amadeus developer account is active

**2. No Results Found**
- Check that airport codes are valid (3 letters, like "LAX" not "Los Angeles")
- Ensure dates are in the future
- Try different date ranges or routes

**3. Invalid Date Format**
- Dates must be in YYYY-MM-DD format
- Example: "2025-12-25" not "12/25/2025"

**4. Server Connection Issues**
- For MCP server examples, ensure the server is running
- Direct API usage doesn't require a server

### Getting Help

**Check the logs** for detailed error messages:
```python
try:
    # Your flight search code
except Exception as e:
    print(f"Error details: {e}")
```

**Verify airport codes** using the autocomplete feature:
```python
result = client.autocomplete_locations_direct("city name here")
```

## Next Steps

### Integrating into Your Application

The example shows three patterns you can use in your own applications:

1. **Simple Integration**: Use `example_direct_api_usage()` as a template
2. **AI Integration**: Use MCP server pattern for AI assistants
3. **Robust Integration**: Use hybrid pattern for maximum reliability

### Advanced Features

Once you're comfortable with basic searches, you can explore:
- Flight pricing and booking
- Multi-city trips
- Hotel and car rental searches
- Airport and airline information

### Production Considerations

When moving to production:
1. Set `AMADEUS_HOST=prod` in your environment
2. Use production API credentials
3. Implement proper error handling and logging
4. Consider rate limiting and caching strategies

## Support

- **Amadeus API Documentation**: [https://developers.amadeus.com/](https://developers.amadeus.com/)
- **Project Issues**: Check the project's GitHub issues
- **API Status**: Monitor Amadeus API status for service updates