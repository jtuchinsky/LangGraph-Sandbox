# Amadeus MCP Client Package - Refactored Sequence Diagrams

## 1. Direct API Usage Flow (Using AmadeusDirectClient)

```mermaid
sequenceDiagram
    participant User
    participant AmadeusDirectClient
    participant AmadeusAPI
    participant OAuthToken

    User->>AmadeusDirectClient: create_direct_client()
    AmadeusDirectClient->>AmadeusDirectClient: __init__(client_id, secret, host)
    
    User->>AmadeusDirectClient: autocomplete_locations("San Francisco")
    AmadeusDirectClient->>AmadeusDirectClient: _ensure_token()
    
    alt Token is expired or missing
        AmadeusDirectClient->>AmadeusAPI: POST /v1/security/oauth2/token
        AmadeusAPI-->>AmadeusDirectClient: access_token, expires_in
        AmadeusDirectClient->>OAuthToken: create token object
    end
    
    AmadeusDirectClient->>AmadeusDirectClient: _auth_headers()
    AmadeusDirectClient->>AmadeusAPI: GET /v1/reference-data/locations
    AmadeusAPI-->>AmadeusDirectClient: locations data
    AmadeusDirectClient-->>User: raw API response
    
    User->>AmadeusDirectClient: close()
```

## 1b. Direct API Usage via Wrapper Client

```mermaid
sequenceDiagram
    participant User
    participant AmadeusWrapperClient
    participant AmadeusDirectClient
    participant AmadeusAPI
    participant OAuthToken

    User->>AmadeusWrapperClient: create_amadeus_client()
    AmadeusWrapperClient->>AmadeusDirectClient: create_direct_client()
    
    User->>AmadeusWrapperClient: autocomplete_locations_direct("San Francisco")
    AmadeusWrapperClient->>AmadeusDirectClient: autocomplete_locations("San Francisco", 5, ["CITY", "AIRPORT"])
    AmadeusDirectClient->>AmadeusDirectClient: _ensure_token()
    
    alt Token is expired or missing
        AmadeusDirectClient->>AmadeusAPI: POST /v1/security/oauth2/token
        AmadeusAPI-->>AmadeusDirectClient: access_token, expires_in
        AmadeusDirectClient->>OAuthToken: create token object
    end
    
    AmadeusDirectClient->>AmadeusDirectClient: _auth_headers()
    AmadeusDirectClient->>AmadeusAPI: GET /v1/reference-data/locations
    AmadeusAPI-->>AmadeusDirectClient: locations data
    AmadeusDirectClient-->>AmadeusWrapperClient: raw API response
    AmadeusWrapperClient->>AmadeusWrapperClient: transform to slim format
    AmadeusWrapperClient-->>User: {success: true, items: [...]}
    
    User->>AmadeusWrapperClient: close()
    AmadeusWrapperClient->>AmadeusDirectClient: close()
```

## 2. MCP Server Usage Flow (Using AmadeusMCPOnlyClient)

```mermaid
sequenceDiagram
    participant User
    participant AmadeusMCPOnlyClient
    participant MCPClient
    participant MCPServer
    participant AmadeusDirectClient as ServerAPIClient
    participant AmadeusAPI

    User->>AmadeusMCPOnlyClient: create_mcp_client()
    User->>AmadeusMCPOnlyClient: connect_to_server(["python", "-m", "server"])
    AmadeusMCPOnlyClient->>MCPClient: __init__(server_command)
    AmadeusMCPOnlyClient->>MCPClient: connect()
    MCPClient->>MCPServer: start server process
    MCPClient->>MCPServer: initialize()
    MCPServer-->>MCPClient: connection established
    MCPClient-->>AmadeusMCPOnlyClient: connection success
    
    User->>AmadeusMCPOnlyClient: autocomplete_locations("Los Angeles")
    AmadeusMCPOnlyClient->>MCPClient: call_tool("autocomplete_locations", args)
    MCPClient->>MCPServer: tool call request
    MCPServer->>ServerAPIClient: autocomplete_locations("Los Angeles")
    
    ServerAPIClient->>AmadeusAPI: GET /v1/reference-data/locations
    AmadeusAPI-->>ServerAPIClient: locations data
    ServerAPIClient-->>MCPServer: processed results
    MCPServer-->>MCPClient: tool response
    MCPClient-->>AmadeusMCPOnlyClient: {success: true, result: [...]}
    AmadeusMCPOnlyClient-->>User: MCP response
    
    User->>AmadeusMCPOnlyClient: disconnect_from_server()
    AmadeusMCPOnlyClient->>MCPClient: disconnect()
    MCPClient->>MCPServer: close connection
```

## 2b. MCP Server Usage via Wrapper Client

```mermaid
sequenceDiagram
    participant User
    participant AmadeusWrapperClient
    participant AmadeusMCPOnlyClient
    participant MCPClient
    participant MCPServer
    participant AmadeusDirectClient as ServerAPIClient
    participant AmadeusAPI

    User->>AmadeusWrapperClient: create_amadeus_client()
    AmadeusWrapperClient->>AmadeusMCPOnlyClient: create_mcp_client()
    User->>AmadeusWrapperClient: connect_to_mcp_server(["python", "-m", "server"])
    AmadeusWrapperClient->>AmadeusMCPOnlyClient: connect_to_server(server_command)
    AmadeusMCPOnlyClient->>MCPClient: connect()
    MCPClient->>MCPServer: start server process
    MCPServer-->>MCPClient: connection established
    MCPClient-->>AmadeusMCPOnlyClient: success
    AmadeusMCPOnlyClient-->>AmadeusWrapperClient: connected = true
    
    User->>AmadeusWrapperClient: autocomplete_locations_mcp("Los Angeles")
    AmadeusWrapperClient->>AmadeusMCPOnlyClient: autocomplete_locations("Los Angeles")
    AmadeusMCPOnlyClient->>MCPClient: call_tool("autocomplete_locations", args)
    MCPClient->>MCPServer: tool call request
    MCPServer->>ServerAPIClient: autocomplete_locations("Los Angeles")
    
    ServerAPIClient->>AmadeusAPI: GET /v1/reference-data/locations
    AmadeusAPI-->>ServerAPIClient: locations data
    ServerAPIClient-->>MCPServer: processed results
    MCPServer-->>MCPClient: tool response
    MCPClient-->>AmadeusMCPOnlyClient: {success: true, result: [...]}
    AmadeusMCPOnlyClient-->>AmadeusWrapperClient: MCP response
    AmadeusWrapperClient-->>User: MCP response
    
    User->>AmadeusWrapperClient: disconnect_from_mcp_server()
    AmadeusWrapperClient->>AmadeusMCPOnlyClient: disconnect_from_server()
    AmadeusMCPOnlyClient->>MCPClient: disconnect()
    MCPClient->>MCPServer: close connection
```

## 3. Hybrid Usage with Intelligent Fallback (Wrapper Client)

```mermaid
sequenceDiagram
    participant User
    participant AmadeusWrapperClient
    participant AmadeusMCPOnlyClient
    participant MCPClient
    participant MCPServer
    participant AmadeusDirectClient
    participant AmadeusAPI

    User->>AmadeusWrapperClient: create_amadeus_client()
    AmadeusWrapperClient->>AmadeusDirectClient: create_direct_client()
    AmadeusWrapperClient->>AmadeusMCPOnlyClient: create_mcp_client()
    User->>AmadeusWrapperClient: connect_to_mcp_server(server_command)
    
    alt MCP Server Available
        AmadeusWrapperClient->>AmadeusMCPOnlyClient: connect_to_server()
        AmadeusMCPOnlyClient->>MCPClient: connect()
        MCPClient->>MCPServer: establish connection
        MCPServer-->>MCPClient: success
        MCPClient-->>AmadeusMCPOnlyClient: connected = true
        AmadeusMCPOnlyClient-->>AmadeusWrapperClient: success
    else MCP Server Unavailable
        AmadeusMCPOnlyClient-->>AmadeusWrapperClient: connected = false
    end
    
    User->>AmadeusWrapperClient: search_flights(search_args, prefer_mcp=true)
    
    alt MCP Available and Prefer MCP
        AmadeusWrapperClient->>AmadeusWrapperClient: search_flights_mcp(search_args)
        AmadeusWrapperClient->>AmadeusMCPOnlyClient: search_flights(args)
        AmadeusMCPOnlyClient->>MCPClient: call_tool("search_flights", args)
        MCPClient->>MCPServer: tool request
        
        alt MCP Call Succeeds
            MCPServer-->>MCPClient: flight results
            MCPClient-->>AmadeusMCPOnlyClient: {success: true, ...}
            AmadeusMCPOnlyClient-->>AmadeusWrapperClient: MCP results
            AmadeusWrapperClient-->>User: MCP results
        else MCP Call Fails
            MCPServer-->>MCPClient: error
            MCPClient-->>AmadeusMCPOnlyClient: {success: false, ...}
            AmadeusMCPOnlyClient-->>AmadeusWrapperClient: error
            Note over AmadeusWrapperClient: Intelligent fallback to direct API
            AmadeusWrapperClient->>AmadeusWrapperClient: search_flights_direct(args)
            AmadeusWrapperClient->>AmadeusDirectClient: search_flights(...)
            AmadeusDirectClient->>AmadeusAPI: POST /v2/shopping/flight-offers
            AmadeusAPI-->>AmadeusDirectClient: flight data
            AmadeusDirectClient-->>AmadeusWrapperClient: API response
            AmadeusWrapperClient-->>User: Direct API results
        end
    else Direct API Preferred or MCP Unavailable
        AmadeusWrapperClient->>AmadeusWrapperClient: search_flights_direct(args)
        AmadeusWrapperClient->>AmadeusDirectClient: search_flights(...)
        AmadeusDirectClient->>AmadeusAPI: POST /v2/shopping/flight-offers
        AmadeusAPI-->>AmadeusDirectClient: flight data
        AmadeusDirectClient-->>AmadeusWrapperClient: API response
        AmadeusWrapperClient-->>User: Direct API results
    end
```

## 4. Flight Search and Pricing Flow (Updated)

```mermaid
sequenceDiagram
    participant User
    participant AmadeusWrapperClient
    participant AmadeusDirectClient
    participant AmadeusAPI

    User->>AmadeusWrapperClient: search_flights_direct(search_args)
    AmadeusWrapperClient->>AmadeusWrapperClient: validate and convert SearchArgs
    AmadeusWrapperClient->>AmadeusDirectClient: search_flights(origin, destination, ...)
    
    AmadeusDirectClient->>AmadeusDirectClient: _ensure_token()
    AmadeusDirectClient->>AmadeusAPI: POST /v2/shopping/flight-offers
    AmadeusAPI-->>AmadeusDirectClient: flight offers JSON
    AmadeusDirectClient-->>AmadeusWrapperClient: raw flight data
    
    AmadeusWrapperClient->>AmadeusWrapperClient: transform to slim format
    Note over AmadeusWrapperClient: Keep _full offer for pricing
    AmadeusWrapperClient-->>User: {success: true, offers: [...]}
    
    User->>User: Select offer from results
    User->>AmadeusWrapperClient: price_offer_direct({flight_offer: offer._full})
    AmadeusWrapperClient->>AmadeusDirectClient: price_offer(offer._full, currency)
    AmadeusDirectClient->>AmadeusAPI: POST /v1/shopping/flight-offers/pricing
    AmadeusAPI-->>AmadeusDirectClient: updated pricing data
    AmadeusDirectClient-->>AmadeusWrapperClient: pricing response
    AmadeusWrapperClient-->>User: {success: true, result: {...}}
```

## 5. Error Handling Flow (Updated)

```mermaid
sequenceDiagram
    participant User
    participant AmadeusWrapperClient
    participant AmadeusDirectClient
    participant AmadeusAPI

    User->>AmadeusWrapperClient: autocomplete_locations_direct("query")
    AmadeusWrapperClient->>AmadeusDirectClient: autocomplete_locations("query")
    AmadeusDirectClient->>AmadeusDirectClient: _ensure_token()
    AmadeusDirectClient->>AmadeusAPI: GET /v1/reference-data/locations
    
    alt HTTP Error (4xx/5xx)
        AmadeusAPI-->>AmadeusDirectClient: HTTP 400 Bad Request
        AmadeusDirectClient->>AmadeusDirectClient: raise HTTPStatusError
        AmadeusDirectClient-->>AmadeusWrapperClient: HTTPStatusError exception
        AmadeusWrapperClient->>AmadeusWrapperClient: catch and format error
        AmadeusWrapperClient-->>User: {success: false, error: "HTTP 400: details"}
    else Network/Other Error
        AmadeusAPI-->>AmadeusDirectClient: Connection error
        AmadeusDirectClient-->>AmadeusWrapperClient: Exception
        AmadeusWrapperClient->>AmadeusWrapperClient: catch generic exception
        AmadeusWrapperClient-->>User: {success: false, error: "error message"}
    else Success
        AmadeusAPI-->>AmadeusDirectClient: Valid response
        AmadeusDirectClient-->>AmadeusWrapperClient: Success data
        AmadeusWrapperClient-->>User: {success: true, items: [...]}
    end
```

## Key Interaction Patterns in Refactored Architecture

### 1. **Authentication Flow**
- OAuth token managed automatically by `AmadeusDirectClient`
- Token refresh handled transparently before API calls
- Credentials loaded from environment variables
- Isolated in direct client for clear separation of concerns

### 2. **Modular Access Pattern**
- **Direct API**: `AmadeusDirectClient` for immediate low-level access
- **MCP Protocol**: `AmadeusMCPOnlyClient` for server-mediated access  
- **Unified Interface**: `AmadeusWrapperClient` with intelligent fallback logic
- Each component can be used independently

### 3. **Intelligent Fallback Strategy**
- `AmadeusWrapperClient` tries MCP first, automatically falls back to direct API
- HTTP errors captured with detailed status information in both paths
- MCP failures trigger seamless fallback with no user intervention required
- Consistent error response format across all access methods

### 4. **Data Transformation & Response Normalization**
- Raw API responses transformed to "slim" format in wrapper client
- Full offer data preserved for pricing operations
- Direct client returns raw API responses for maximum flexibility
- Wrapper client provides normalized, consistent response structure

### 5. **Resource Management & Connection Handling**
- Each client manages its own resources independently
- HTTP client properly closed in `AmadeusDirectClient`
- MCP connections tracked and validated in `AmadeusMCPOnlyClient`  
- `AmadeusWrapperClient` coordinates cleanup across both clients
- Graceful degradation when services unavailable

### 6. **Separation of Concerns**
- **Authentication**: Isolated in direct client
- **Protocol handling**: Isolated in MCP client  
- **Business logic**: Coordinated in wrapper client
- **Error handling**: Implemented at appropriate layers
- **Resource management**: Handled by respective components

### 7. **Flexible Usage Patterns**
- **Minimalist**: Use `AmadeusDirectClient` for simple API access
- **Protocol-specific**: Use `AmadeusMCPOnlyClient` for MCP operations
- **Comprehensive**: Use `AmadeusWrapperClient` for full functionality with fallback
- **Legacy compatible**: Existing code continues to work unchanged