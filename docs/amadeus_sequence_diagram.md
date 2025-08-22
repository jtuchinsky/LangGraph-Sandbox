# Amadeus MCP Client Package - Sequence Diagrams

## 1. Direct API Usage Flow

```mermaid
sequenceDiagram
    participant User
    participant AmadeusMCPClient
    participant AmadeusAPIClient
    participant AmadeusAPI
    participant OAuthToken

    User->>AmadeusMCPClient: create_amadeus_client()
    AmadeusMCPClient->>AmadeusAPIClient: __init__(client_id, secret, base_url)
    
    User->>AmadeusMCPClient: autocomplete_locations_direct("San Francisco")
    AmadeusMCPClient->>AmadeusAPIClient: autocomplete_locations("San Francisco", 5, ["CITY", "AIRPORT"])
    AmadeusAPIClient->>AmadeusAPIClient: _ensure_token()
    
    alt Token is expired or missing
        AmadeusAPIClient->>AmadeusAPI: POST /v1/security/oauth2/token
        AmadeusAPI-->>AmadeusAPIClient: access_token, expires_in
        AmadeusAPIClient->>OAuthToken: create token object
    end
    
    AmadeusAPIClient->>AmadeusAPIClient: _auth_headers()
    AmadeusAPIClient->>AmadeusAPI: GET /v1/reference-data/locations
    AmadeusAPI-->>AmadeusAPIClient: locations data
    AmadeusAPIClient-->>AmadeusMCPClient: raw API response
    AmadeusMCPClient->>AmadeusMCPClient: transform to slim format
    AmadeusMCPClient-->>User: {success: true, items: [...]}
    
    User->>AmadeusMCPClient: close()
    AmadeusMCPClient->>AmadeusAPIClient: close()
```

## 2. MCP Server Usage Flow

```mermaid
sequenceDiagram
    participant User
    participant AmadeusMCPClient
    participant MCPClient
    participant MCPServer
    participant AmadeusAPIClient as ServerAPIClient
    participant AmadeusAPI

    User->>AmadeusMCPClient: create_amadeus_client()
    User->>AmadeusMCPClient: connect_to_mcp_server(["python", "-m", "server"])
    AmadeusMCPClient->>MCPClient: __init__(server_command)
    AmadeusMCPClient->>MCPClient: connect()
    MCPClient->>MCPServer: start server process
    MCPClient->>MCPServer: initialize()
    MCPServer-->>MCPClient: connection established
    MCPClient-->>AmadeusMCPClient: connection success
    
    User->>AmadeusMCPClient: autocomplete_locations_mcp("Los Angeles")
    AmadeusMCPClient->>MCPClient: call_tool("autocomplete_locations", args)
    MCPClient->>MCPServer: tool call request
    MCPServer->>ServerAPIClient: autocomplete_locations("Los Angeles")
    
    ServerAPIClient->>AmadeusAPI: GET /v1/reference-data/locations
    AmadeusAPI-->>ServerAPIClient: locations data
    ServerAPIClient-->>MCPServer: processed results
    MCPServer-->>MCPClient: tool response
    MCPClient-->>AmadeusMCPClient: {success: true, result: [...]}
    AmadeusMCPClient-->>User: MCP response
    
    User->>AmadeusMCPClient: disconnect_from_mcp_server()
    AmadeusMCPClient->>MCPClient: disconnect()
    MCPClient->>MCPServer: close connection
```

## 3. Hybrid Usage with Fallback

```mermaid
sequenceDiagram
    participant User
    participant AmadeusMCPClient
    participant MCPClient
    participant MCPServer
    participant AmadeusAPIClient
    participant AmadeusAPI

    User->>AmadeusMCPClient: create_amadeus_client()
    User->>AmadeusMCPClient: connect_to_mcp_server(server_command)
    
    alt MCP Server Available
        AmadeusMCPClient->>MCPClient: connect()
        MCPClient->>MCPServer: establish connection
        MCPServer-->>MCPClient: success
        MCPClient-->>AmadeusMCPClient: connected = true
    else MCP Server Unavailable
        MCPClient-->>AmadeusMCPClient: connected = false
    end
    
    User->>AmadeusMCPClient: search_flights(search_args, prefer_mcp=true)
    
    alt MCP Available and Prefer MCP
        AmadeusMCPClient->>AmadeusMCPClient: search_flights_mcp(search_args)
        AmadeusMCPClient->>MCPClient: call_tool("search_flights", args)
        MCPClient->>MCPServer: tool request
        
        alt MCP Call Succeeds
            MCPServer-->>MCPClient: flight results
            MCPClient-->>AmadeusMCPClient: {success: true, ...}
            AmadeusMCPClient-->>User: MCP results
        else MCP Call Fails
            MCPServer-->>MCPClient: error
            MCPClient-->>AmadeusMCPClient: {success: false, ...}
            Note over AmadeusMCPClient: Fallback to direct API
            AmadeusMCPClient->>AmadeusMCPClient: search_flights_direct(args)
            AmadeusMCPClient->>AmadeusAPIClient: search_flights(...)
            AmadeusAPIClient->>AmadeusAPI: GET /v2/shopping/flight-offers
            AmadeusAPI-->>AmadeusAPIClient: flight data
            AmadeusAPIClient-->>AmadeusMCPClient: API response
            AmadeusMCPClient-->>User: Direct API results
        end
    else Direct API Preferred or MCP Unavailable
        AmadeusMCPClient->>AmadeusMCPClient: search_flights_direct(args)
        AmadeusMCPClient->>AmadeusAPIClient: search_flights(...)
        AmadeusAPIClient->>AmadeusAPI: GET /v2/shopping/flight-offers
        AmadeusAPI-->>AmadeusAPIClient: flight data
        AmadeusAPIClient-->>AmadeusMCPClient: API response
        AmadeusMCPClient-->>User: Direct API results
    end
```

## 4. Flight Search and Pricing Flow

```mermaid
sequenceDiagram
    participant User
    participant AmadeusMCPClient
    participant AmadeusAPIClient
    participant AmadeusAPI

    User->>AmadeusMCPClient: search_flights_direct(search_args)
    AmadeusMCPClient->>AmadeusMCPClient: validate and convert SearchArgs
    AmadeusMCPClient->>AmadeusAPIClient: search_flights(origin, destination, ...)
    
    AmadeusAPIClient->>AmadeusAPIClient: _ensure_token()
    AmadeusAPIClient->>AmadeusAPI: GET /v2/shopping/flight-offers
    AmadeusAPI-->>AmadeusAPIClient: flight offers JSON
    AmadeusAPIClient-->>AmadeusMCPClient: raw flight data
    
    AmadeusMCPClient->>AmadeusMCPClient: transform to slim format
    Note over AmadeusMCPClient: Keep _full offer for pricing
    AmadeusMCPClient-->>User: {success: true, offers: [...]}
    
    User->>User: Select offer from results
    User->>AmadeusMCPClient: price_offer_direct({flight_offer: offer._full})
    AmadeusMCPClient->>AmadeusAPIClient: price_offer(offer._full, currency)
    AmadeusAPIClient->>AmadeusAPI: POST /v1/shopping/flight-offers/pricing
    AmadeusAPI-->>AmadeusAPIClient: updated pricing data
    AmadeusAPIClient-->>AmadeusMCPClient: pricing response
    AmadeusMCPClient-->>User: {success: true, result: {...}}
```

## 5. Error Handling Flow

```mermaid
sequenceDiagram
    participant User
    participant AmadeusMCPClient
    participant AmadeusAPIClient
    participant AmadeusAPI

    User->>AmadeusMCPClient: autocomplete_locations_direct("query")
    AmadeusMCPClient->>AmadeusAPIClient: autocomplete_locations("query")
    AmadeusAPIClient->>AmadeusAPIClient: _ensure_token()
    AmadeusAPIClient->>AmadeusAPI: GET /v1/reference-data/locations
    
    alt HTTP Error (4xx/5xx)
        AmadeusAPI-->>AmadeusAPIClient: HTTP 400 Bad Request
        AmadeusAPIClient->>AmadeusAPIClient: raise HTTPStatusError
        AmadeusAPIClient-->>AmadeusMCPClient: HTTPStatusError exception
        AmadeusMCPClient->>AmadeusMCPClient: catch and format error
        AmadeusMCPClient-->>User: {success: false, error: "HTTP 400: details"}
    else Network/Other Error
        AmadeusAPI-->>AmadeusAPIClient: Connection error
        AmadeusAPIClient-->>AmadeusMCPClient: Exception
        AmadeusMCPClient->>AmadeusMCPClient: catch generic exception
        AmadeusMCPClient-->>User: {success: false, error: "error message"}
    else Success
        AmadeusAPI-->>AmadeusAPIClient: Valid response
        AmadeusAPIClient-->>AmadeusMCPClient: Success data
        AmadeusMCPClient-->>User: {success: true, items: [...]}
    end
```

## Key Interaction Patterns

### 1. **Authentication Flow**
- OAuth token managed automatically by `AmadeusAPIClient`
- Token refresh handled transparently before API calls
- Credentials loaded from environment variables

### 2. **Dual Access Pattern**
- Direct API methods (`*_direct()`) for immediate access
- MCP methods (`*_mcp()`) for server-mediated access  
- Convenience methods with automatic fallback

### 3. **Error Handling Strategy**
- HTTP errors captured with detailed status information
- MCP failures trigger automatic fallback to direct API
- Consistent error response format across all methods

### 4. **Data Transformation**
- Raw API responses transformed to "slim" format
- Full offer data preserved for pricing operations
- Consistent response structure for client applications

### 5. **Resource Management**
- HTTP client and MCP connections properly closed
- Connection state tracked and validated
- Graceful degradation when services unavailable