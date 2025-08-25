# Google Flights Usage Example - Technical Documentation

## Overview

The `google_flights_usage.py` file demonstrates the integration of the Google Flights MCP client with the external Google Flights MCP server, showcasing comprehensive flight search, airport management, and travel planning functionality through the Model Context Protocol.

## Architecture

### Client Architecture

The example leverages the Google Flights MCP client architecture:

```python
from source.mcp_clients.google_flights import create_google_flights_client, FlightSearchArgs
```

**Key Components:**
- `GoogleFlightsMCPClient` - Main MCP protocol client
- `FlightSearchArgs` - Pydantic validation model for search parameters
- `MCPClient` - Underlying MCP protocol implementation

### External Server Integration

**Server Location**: `/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py`

**Server Dependencies**:
- `fast-flights` - Google Flights scraping API
- `fastmcp` - MCP server framework
- `aiohttp` - HTTP client for airport data fetching

## Technical Implementation

### Function: `example_google_flights_usage()`

**Purpose**: Comprehensive demonstration of all Google Flights MCP client capabilities.

**Technical Flow:**
```python
async def example_google_flights_usage():
    # 1. Client instantiation
    client = create_google_flights_client()
    
    # 2. MCP server connection
    server_command = ["python", "/path/to/flights-mcp-server.py"]
    connected = await client.connect_to_server(server_command)
    
    # 3. Multi-step operations
    # Airport search, travel dates, flight search, airport info, tools listing, trip planning
    
    # 4. Resource cleanup
    await client.disconnect_from_server()
```

**MCP Tool Integration:**

#### Airport Search
- **MCP Tool**: `airport_search`
- **Method**: `client.airport_search(query)`
- **Server Implementation**: CSV-based airport database search
- **Response Processing**: Text-based results with airport codes and names

#### Travel Date Suggestions
- **MCP Tool**: `get_travel_dates`
- **Method**: `client.get_travel_dates(days_from_now, trip_length)`
- **Server Logic**: Date calculation based on current date + offset
- **Default Values**: 30 days advance, 7-day trip length

#### Flight Search
- **MCP Tool**: `search_flights`
- **Method**: `client.search_flights(FlightSearchArgs)`
- **Server Integration**: `fast-flights` API wrapper
- **Search Parameters**:
  ```python
  FlightSearchArgs(
      from_airport="LAX",           # 3-letter IATA code
      to_airport="JFK",            # 3-letter IATA code
      departure_date="2025-04-15", # YYYY-MM-DD format
      return_date="2025-04-22",    # Optional for round-trip
      adults=1,                    # Passenger count validation
      seat_class="economy"         # Validated seat class
  )
  ```

#### Airport Information
- **MCP Resource**: `airports://{code}`
- **Method**: `client.get_airport_info(airport_code)`
- **Data Source**: Comprehensive CSV airport database
- **Response Format**: Structured airport information

### Function: `example_one_way_flight_search()`

**Purpose**: Specific demonstration of one-way flight search patterns.

**Key Technical Details:**

#### Parameter Validation
```python
search_args = FlightSearchArgs(
    from_airport="SFO",
    to_airport="LAX", 
    departure_date="2025-05-01",
    # return_date intentionally omitted for one-way
    adults=2,
    children=1,
    seat_class="premium_economy"
)
```

**Pydantic Validation Chain:**
1. **Airport Code Validation**: 3-character IATA code enforcement
2. **Date Format Validation**: Regex pattern matching for YYYY-MM-DD
3. **Passenger Count Validation**: Range validation (1-9 for adults)
4. **Seat Class Validation**: Enum validation against allowed values

### Function: `example_airport_database_operations()`

**Purpose**: Demonstrates airport database management and search capabilities.

**Technical Operations:**

#### Database Update
- **MCP Tool**: `update_airports_database`
- **Method**: `client.update_airports_database()`
- **Server Process**: 
  1. Fetches fresh airport data from CSV URL
  2. Validates IATA codes (3 uppercase letters)
  3. Updates internal airport dictionary
  4. Caches results to local JSON file

#### All Airports Resource
- **MCP Resource**: `airports://all`
- **Method**: `client.get_all_airports()`
- **Response Handling**: Large dataset truncation for display
- **Performance**: First 100 results to avoid overwhelming output

#### Targeted Airport Search
- **Search Algorithm**: String matching against airport names and codes
- **Case Insensitive**: Query normalization to uppercase
- **Result Limiting**: Top 20 matches with overflow indication

## Data Validation Architecture

### Pydantic Model Integration

**FlightSearchArgs Validation:**
```python
class FlightSearchArgs(BaseModel):
    from_airport: str = Field(..., min_length=3, max_length=3)
    to_airport: str = Field(..., min_length=3, max_length=3)
    departure_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    return_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    adults: int = Field(1, ge=1, le=9)
    children: int = Field(0, ge=0, le=9)
    infants_in_seat: int = Field(0, ge=0, le=9)
    infants_on_lap: int = Field(0, ge=0, le=9)
    seat_class: str = Field("economy")
    
    @field_validator("from_airport", "to_airport")
    @classmethod
    def uppercase_airport_codes(cls, v: str) -> str:
        return v.upper()
    
    @field_validator("seat_class")
    @classmethod
    def validate_seat_class(cls, v: str) -> str:
        valid_classes = ["economy", "premium_economy", "business", "first"]
        if v.lower() not in valid_classes:
            raise ValueError(f"Seat class must be one of: {', '.join(valid_classes)}")
        return v.lower()
```

### Validation Chain Execution
1. **Field Type Validation**: Automatic type checking
2. **Field Constraints**: Length, range, and pattern validation
3. **Custom Validators**: Airport code normalization and seat class validation
4. **Error Aggregation**: Comprehensive validation error reporting

## MCP Protocol Integration

### Connection Management
```python
async def connect_to_server(self, server_command: List[str]) -> bool:
    try:
        self.mcp_client = MCPClient(server_command)
        result = await self.mcp_client.connect()
        self.connected = result
        return self.connected
    except Exception as e:
        self.logger.error(f"Error connecting: {e}")
        return False
```

### Tool Call Architecture
```python
async def search_flights(self, search_args: FlightSearchArgs) -> Dict[str, Any]:
    # 1. Connection validation
    if not self.connected or not self.mcp_client:
        return {"success": False, "error": "Not connected"}
    
    # 2. Parameter serialization
    args_dict = search_args.model_dump(exclude_none=True)
    
    # 3. MCP tool invocation
    result = await self.mcp_client.call_tool("search_flights", args_dict)
    
    # 4. Response processing
    if result.get("is_error", False):
        return {"success": False, "error": result.get("content")}
    
    return {"success": True, "result": result.get("content"), "raw_response": result}
```

### Resource Access Pattern
```python
async def get_airport_info(self, airport_code: str) -> Dict[str, Any]:
    airport_code = airport_code.upper()
    result = await self.mcp_client.read_resource(f"airports://{airport_code}")
    # Response processing...
```

## Error Handling Strategies

### Response Format Standardization
```python
{
    "success": boolean,        # Operation success indicator
    "result": string,          # Primary result content
    "error": string,           # Error message (on failure)
    "raw_response": dict       # Full MCP response (optional)
}
```

### Exception Hierarchy
1. **Connection Errors**: Server unavailability, network issues
2. **Validation Errors**: Pydantic model validation failures
3. **MCP Protocol Errors**: Protocol-level communication issues
4. **Tool Execution Errors**: Server-side tool execution failures

### Graceful Degradation
```python
if not connected:
    print("✗ Failed to connect to Google Flights MCP server")
    print("Make sure the server is available at the specified path")
    return
```

## Performance Considerations

### Async Operation Patterns
- **Non-blocking I/O**: All MCP operations use async/await
- **Connection Pooling**: Single persistent connection per client instance
- **Resource Management**: Explicit connection lifecycle management

### Data Transfer Optimization
- **Selective Serialization**: `exclude_none=True` for parameter passing
- **Response Truncation**: Large datasets limited for display performance
- **Caching Strategy**: Server-side airport database caching

## Server Dependencies and Requirements

### External Server Architecture
**fast-flights Integration:**
```python
from fast_flights import FlightData, Passengers, Result, get_flights

# Server-side flight search execution
result: Result = get_flights(
    flight_data=flight_data,
    trip=trip_type,
    seat=seat_class,
    passengers=passengers,
    fetch_mode="fallback"
)
```

**Airport Database Management:**
- **Data Source**: Public CSV from airportsdata repository
- **Update Mechanism**: HTTP fetch with aiohttp
- **Storage**: Local JSON cache with fallback to remote fetch
- **Validation**: IATA code format validation (3 uppercase letters)

### Server Configuration
```python
DEFAULT_CONFIG = {
    "max_results": 10,
    "default_trip_days": 7,
    "default_advance_days": 30,
    "seat_classes": ["economy", "premium_economy", "business", "first"]
}
```

## Testing and Validation

### Unit Testing Hooks
```python
# Validation testing
try:
    args = FlightSearchArgs(from_airport='INVALID', ...)
except ValidationError as e:
    # Validation error handling
```

### Integration Testing Patterns
1. **Server Connectivity**: Connection establishment validation
2. **Tool Availability**: MCP tool discovery and listing
3. **Response Format**: Standardized response validation
4. **Error Scenarios**: Connection failure simulation

## Security and Privacy

### Data Handling
- **No Persistent Storage**: Client doesn't store flight data
- **Connection Security**: MCP protocol security
- **Input Sanitization**: Pydantic validation prevents injection

### Server Communication
- **Process Isolation**: Server runs in separate process
- **Command Injection Protection**: Parameterized server commands
- **Resource Access Control**: Controlled airport data access

## Extension Points

### Custom Tool Integration
```python
# Add new MCP tools to server
@mcp.tool()
def custom_flight_analysis(args: CustomArgs) -> str:
    # Custom analysis logic
    pass

# Corresponding client method
async def custom_analysis(self, args: CustomArgs) -> Dict[str, Any]:
    return await self.mcp_client.call_tool("custom_flight_analysis", args.model_dump())
```

### Response Processing Customization
```python
# Override response formatting
def format_flight_results(self, raw_result: str) -> Dict[str, Any]:
    # Custom parsing and formatting
    pass
```

## Monitoring and Observability

### Logging Integration
```python
self.logger = logging.getLogger(__name__)
self.logger.info("Connected to Google Flights MCP server")
self.logger.error(f"Error searching flights: {e}")
```

### Performance Metrics
- **Connection Latency**: MCP connection establishment time
- **Tool Execution Time**: Individual tool call duration
- **Success Rates**: Tool execution success/failure ratios
- **Data Transfer**: Request/response payload sizes

## Deployment Architecture

### Client Deployment
- **Dependencies**: Pydantic, MCP client libraries
- **Configuration**: Server path configuration
- **Resource Requirements**: Minimal client-side resources

### Server Deployment
- **External Process**: Separate server process management
- **Dependencies**: fast-flights, fastmcp, aiohttp
- **Data Management**: Airport database initialization and updates
- **Resource Requirements**: Higher server-side compute and memory