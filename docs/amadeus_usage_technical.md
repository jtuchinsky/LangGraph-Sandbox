# Amadeus Usage Example - Technical Documentation

## Overview

The `amadeus_usage.py` file demonstrates the complete integration of the refactored Amadeus MCP client package, showcasing three distinct usage patterns: direct API access, MCP server integration, and hybrid fallback functionality.

## Architecture

### Client Architecture Integration

The example leverages the modular Amadeus client architecture:

```python
from source.mcp_clients.amadeus import create_amadeus_client, AmadeusMCPClient
```

**Key Components Used:**
- `AmadeusWrapperClient` (via `create_amadeus_client()`)
- `AmadeusDirectClient` (internally composed)
- `AmadeusMCPOnlyClient` (internally composed)

### Design Patterns Demonstrated

1. **Factory Pattern**: Uses `create_amadeus_client()` for clean object creation
2. **Facade Pattern**: Unified interface hiding complexity of multiple clients
3. **Strategy Pattern**: Intelligent fallback from MCP to direct API
4. **Resource Management**: Proper connection lifecycle management

## Technical Implementation

### Function: `example_direct_api_usage()`

**Purpose**: Demonstrates direct Amadeus API access without MCP server dependency.

**Technical Flow:**
```python
async def example_direct_api_usage():
    # 1. Client instantiation via factory
    client = create_amadeus_client()
    
    # 2. Direct API method calls
    result = client.autocomplete_locations_direct(query, limit, sub_types)
    flight_result = client.search_flights_direct(search_args)
    
    # 3. Resource cleanup
    client.close()
```

**Key Technical Details:**

#### Location Autocomplete
- **Method**: `autocomplete_locations_direct()`
- **Parameters**: 
  - `query`: Free text search term
  - `limit`: Result count (default: 3)
  - `sub_types`: Location types filter `["CITY", "AIRPORT"]`
- **API Endpoint**: `/v1/reference-data/locations`
- **Response Format**: Normalized slim format with success wrapper

#### Flight Search
- **Method**: `search_flights_direct()`
- **Parameters**: Dictionary with search criteria
- **API Endpoint**: `/v2/shopping/flight-offers`
- **Authentication**: OAuth 2.0 with automatic token management
- **Response Processing**: 
  - Dynamic display count based on `max_results` parameter
  - Trip type detection (Round-trip vs One-way)
  - Detailed airline and connection information parsing

**Search Arguments Structure:**
```python
search_args = {
    "origin": "EWR",           # 3-letter IATA code
    "destination": "TLV",      # 3-letter IATA code  
    "departure_date": "2025-09-19",  # YYYY-MM-DD format
    "return_date": "2025-10-05",     # Optional for round-trip
    "adults": 1,               # Passenger count
    "cabin": "ECONOMY",        # Seat class
    "max_results": 15          # Display limit
}
```

**Response Processing Logic:**
```python
display_count = min(len(flight_result["offers"]), search_args.get("max_results", 5))
for i, offer in enumerate(flight_result["offers"][:display_count], 1):
    trip_type = "Round-trip" if len(offer["itineraries"]) > 1 else "One-way"
    # Process itineraries and segments...
```

### Function: `example_mcp_server_usage()`

**Purpose**: Demonstrates MCP server integration with protocol-specific operations.

**Technical Flow:**
```python
async def example_mcp_server_usage():
    # 1. Client creation
    client = create_amadeus_client()
    
    # 2. MCP server connection
    server_command = ["python", "-m", "source.mcp_servers.amadeus.server"]
    connected = await client.connect_to_mcp_server(server_command)
    
    # 3. MCP tool calls
    result = await client.autocomplete_locations_mcp(query, limit)
    flight_result = await client.search_flights_mcp(search_args)
    
    # 4. Cleanup
    await client.disconnect_from_mcp_server()
    client.close()
```

**MCP Integration Details:**

#### Server Command Structure
- **Module Path**: `source.mcp_servers.amadeus.server`
- **Execution**: Python subprocess with MCP protocol
- **Connection**: Async bidirectional communication

#### MCP Method Mapping
- `autocomplete_locations_mcp()` → MCP tool: `autocomplete_locations`
- `search_flights_mcp()` → MCP tool: `search_flights`
- `price_offer_mcp()` → MCP tool: `price_offer`

### Function: `example_hybrid_usage()`

**Purpose**: Demonstrates intelligent fallback mechanism from MCP to direct API.

**Technical Implementation:**
```python
# Automatic fallback logic in AmadeusWrapperClient
result = await client.autocomplete_locations(query, prefer_mcp=True)
```

**Fallback Strategy:**
1. **Primary**: Attempt MCP server connection
2. **MCP Call**: Execute via MCP protocol if connected
3. **Fallback Detection**: Monitor for MCP failures/unavailability
4. **Automatic Switch**: Seamlessly switch to direct API
5. **Error Recovery**: Handle network/protocol errors gracefully

## Error Handling Architecture

### Response Format Standardization
All methods return consistent response structure:
```python
{
    "success": boolean,      # Operation success indicator
    "count": integer,        # Result count (for collections)
    "items": array,          # Result data (for autocomplete)
    "offers": array,         # Flight offers (for search)
    "error": string          # Error message (on failure)
}
```

### Exception Management
```python
try:
    # Client operations
    pass
except Exception as e:
    print(f"Error in direct API usage: {e}")
    # Graceful degradation
```

## Authentication Flow

### OAuth 2.0 Implementation
- **Token Management**: Automatic via `AmadeusDirectClient`
- **Refresh Logic**: Transparent token renewal
- **Credential Sources**: Environment variables
- **Security**: Secure token storage and rotation

### Environment Variables
```bash
AMADEUS_CLIENT_ID=your_client_id
AMADEUS_CLIENT_SECRET=your_client_secret  
AMADEUS_HOST=test  # or "prod"
```

## Performance Considerations

### Connection Management
- **Resource Pooling**: HTTP client reuse in direct client
- **Connection Lifecycle**: Proper open/close patterns
- **Memory Management**: Explicit resource cleanup

### API Rate Limiting
- **Built-in Handling**: Automatic retry mechanisms
- **Error Recovery**: Exponential backoff strategies
- **Quota Management**: Efficient request batching

## Data Flow Architecture

```
User Input → AmadeusWrapperClient → Strategy Selection
    ↓
Direct Path: AmadeusDirectClient → OAuth → Amadeus API
    ↓
MCP Path: AmadeusMCPOnlyClient → MCP Protocol → Amadeus Server
    ↓
Response Processing → Normalization → User Output
```

## Testing Integration Points

### Unit Testing Hooks
- **Client Mocking**: Factory pattern enables easy mocking
- **Response Validation**: Consistent response format
- **Error Simulation**: Exception handling verification

### Integration Testing
- **Server Connectivity**: MCP server availability tests
- **API Validation**: Direct API endpoint testing
- **Fallback Verification**: MCP→Direct API switching tests

## Security Considerations

### API Key Management
- **Environment Variables**: Secure credential storage
- **Token Rotation**: Automatic OAuth token refresh
- **Access Control**: Scoped API permissions

### Data Privacy
- **Request Logging**: Sensitive data filtering
- **Response Sanitization**: PII data handling
- **Secure Transport**: HTTPS/TLS enforcement

## Monitoring and Observability

### Logging Integration
```python
# Built-in logging points
client.logger.info("Connected to Amadeus MCP server")
client.logger.error(f"Error connecting: {e}")
```

### Performance Metrics
- **Response Times**: API call duration tracking
- **Success Rates**: Error/success ratio monitoring
- **Resource Usage**: Memory and connection tracking

## Extension Points

### Custom Response Processing
```python
# Override response transformation
def custom_flight_formatter(offers):
    # Custom display logic
    pass
```

### Additional MCP Tools
- **Server Extensions**: Add new MCP tools to server
- **Client Methods**: Corresponding client method implementations
- **Protocol Handlers**: Custom MCP message handling

## Deployment Considerations

### Environment Setup
- **Dependencies**: Pydantic, httpx, MCP libraries
- **Configuration**: Environment variable management
- **Server Deployment**: MCP server process management

### Scalability
- **Connection Pooling**: Multiple client instances
- **Load Balancing**: Distributed MCP servers
- **Caching**: Response caching strategies