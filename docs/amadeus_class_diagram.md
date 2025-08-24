# Amadeus MCP Client Package - Refactored Class Diagram

## Overview

The Amadeus MCP client package has been refactored into three separate components for better separation of concerns:

```mermaid
classDiagram
    %% Direct Client Module (direct_client.py)
    class OAuthToken {
        +access_token: str
        +token_type: str
        +expires_in: int
        +scope: Optional[str]
        +created_at: float
        +is_expired: bool
    }

    class AmadeusDirectClient {
        +client_id: str
        +client_secret: str
        +base_url: str
        -_token: Optional[OAuthToken]
        -_client: httpx.Client
        +__init__(client_id, client_secret, host)
        -_ensure_token()
        -_auth_headers(): Dict[str, str]
        +autocomplete_locations(query, limit, sub_types): dict
        +search_flights(origin, destination, departure_date, ...): dict
        +price_offer(flight_offer, currency): dict
        +close()
    }

    %% MCP Client Module (mcp_client.py)
    class AutocompleteArgs {
        +query: str
        +limit: int
        +sub_types: Optional[List[str]]
    }

    class SearchArgs {
        +origin: str
        +destination: str
        +departure_date: str
        +return_date: Optional[str]
        +adults: int
        +cabin: Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS", "FIRST"]
        +currency: Optional[str]
        +non_stop: Optional[bool]
        +max_price: Optional[int]
        +max_results: int
        +uppercase_iata(v): str
    }

    class PriceArgs {
        +flight_offer: Dict[str, Any]
        +currency: Optional[str]
    }

    class AmadeusMCPOnlyClient {
        +mcp_client: Optional[MCPClient]
        +connected: bool
        +__init__()
        +connect_to_server(server_command): bool
        +disconnect_from_server()
        +is_connected(): bool
        +autocomplete_locations(query, limit, sub_types): dict
        +search_flights(search_args): dict
        +price_offer(flight_offer, currency): dict
        +list_tools(): dict
        +list_resources(): dict
    }

    class MCPClient {
        +server_command: List[str]
        +server_args: List[str]
        +session: Optional[ClientSession]
        +connected: bool
        +__init__(server_command, server_args)
        +connect(): bool
        +disconnect()
        +list_tools(): List[Dict[str, Any]]
        +call_tool(tool_name, arguments): Dict[str, Any]
        +list_resources(): List[Dict[str, Any]]
        +read_resource(uri): Dict[str, Any]
    }

    %% Wrapper Client Module (wrapper_client.py)
    class AmadeusWrapperClient {
        +direct_client: AmadeusDirectClient
        +mcp_client: AmadeusMCPOnlyClient
        +default_currency: str
        +default_max_results: int
        +__init__(client_id, client_secret, host)
        +connect_to_mcp_server(server_command): bool
        +disconnect_from_mcp_server()
        +is_mcp_connected(): bool
        +autocomplete_locations_direct(query, limit, sub_types): dict
        +search_flights_direct(args): dict
        +price_offer_direct(args): dict
        +autocomplete_locations_mcp(query, limit, sub_types): dict
        +search_flights_mcp(search_args): dict
        +price_offer_mcp(flight_offer, currency): dict
        +autocomplete_locations(query, limit, sub_types, prefer_mcp): dict
        +search_flights(search_args, prefer_mcp): dict
        +price_offer(flight_offer, currency, prefer_mcp): dict
        +list_mcp_tools(): dict
        +list_mcp_resources(): dict
        +close()
    }

    %% Relationships
    AmadeusDirectClient --> OAuthToken : uses
    AmadeusMCPOnlyClient --> MCPClient : contains
    AmadeusMCPOnlyClient --> AutocompleteArgs : uses
    AmadeusMCPOnlyClient --> SearchArgs : uses
    AmadeusMCPOnlyClient --> PriceArgs : uses
    AmadeusWrapperClient --> AmadeusDirectClient : contains
    AmadeusWrapperClient --> AmadeusMCPOnlyClient : contains

    %% Inheritance
    AutocompleteArgs --|> BaseModel : extends
    SearchArgs --|> BaseModel : extends
    PriceArgs --|> BaseModel : extends
    OAuthToken --|> BaseModel : extends

    %% Factory functions
    class create_direct_client {
        <<function>>
        +create_direct_client(client_id, client_secret, host): AmadeusDirectClient
    }

    class create_mcp_client {
        <<function>>
        +create_mcp_client(): AmadeusMCPOnlyClient
    }

    class create_amadeus_client {
        <<function>>
        +create_amadeus_client(client_id, client_secret, host): AmadeusWrapperClient
    }

    create_direct_client --> AmadeusDirectClient : creates
    create_mcp_client --> AmadeusMCPOnlyClient : creates
    create_amadeus_client --> AmadeusWrapperClient : creates

    %% Notes
    note for AmadeusWrapperClient "High-level facade providing unified\ninterface with intelligent fallback\nfrom MCP to direct API"
    note for AmadeusDirectClient "Low-level HTTP client for\ndirect Amadeus API access\nwith OAuth 2.0 authentication"
    note for AmadeusMCPOnlyClient "Pure MCP protocol client for\ncommunicating with MCP servers"
    note for MCPClient "Generic MCP client for\nprotocol communication"
```

## Refactored Package Structure

```
mcp_clients/amadeus/
├── __init__.py                # Main exports and backward compatibility
├── direct_client.py          # Direct Amadeus API client
│   ├── OAuthToken (Pydantic model)
│   ├── AmadeusDirectClient
│   └── create_direct_client() (Factory function)
├── mcp_client.py             # MCP-specific functionality
│   ├── AutocompleteArgs (Pydantic model)
│   ├── SearchArgs (Pydantic model)
│   ├── PriceArgs (Pydantic model)
│   ├── AmadeusMCPOnlyClient
│   └── create_mcp_client() (Factory function)
├── wrapper_client.py         # High-level wrapper with fallback
│   ├── AmadeusWrapperClient
│   └── create_amadeus_client() (Factory function)
└── client.py.backup          # Original monolithic implementation
```

## Key Design Patterns

1. **Facade Pattern**: `AmadeusWrapperClient` provides unified interface for both access methods
2. **Strategy Pattern**: Intelligent fallback from MCP to direct API based on availability
3. **Factory Pattern**: Multiple factory functions for different client types
4. **Composition**: `AmadeusWrapperClient` composes `AmadeusDirectClient` and `AmadeusMCPOnlyClient`
5. **Single Responsibility**: Each class has one clear purpose
6. **Separation of Concerns**: Direct API, MCP protocol, and wrapper logic are separated

## Component Responsibilities

### AmadeusDirectClient
- OAuth 2.0 token management
- Direct HTTP calls to Amadeus API
- Raw API response handling
- Connection management

### AmadeusMCPOnlyClient  
- MCP server connection management
- MCP tool calls and responses
- Protocol-specific operations
- Server status monitoring

### AmadeusWrapperClient
- Unified interface for both access methods
- Intelligent fallback logic
- Response normalization
- Configuration management

## Usage Patterns

### Direct API Only
```python
from source.mcp_clients.amadeus import create_direct_client
client = create_direct_client()
result = client.autocomplete_locations("Paris")
client.close()
```

### MCP Protocol Only
```python
from source.mcp_clients.amadeus import create_mcp_client
client = create_mcp_client()
await client.connect_to_server(server_command)
result = await client.autocomplete_locations("Paris")
await client.disconnect_from_server()
```

### Comprehensive (Recommended)
```python
from source.mcp_clients.amadeus import create_amadeus_client
client = create_amadeus_client()
# Use direct API methods
result = client.autocomplete_locations_direct("Paris")
# Or use fallback methods (tries MCP first, falls back to direct)
result = await client.autocomplete_locations("Paris", prefer_mcp=True)
client.close()
```

## Dependencies

### Direct Client
- **External**: `httpx`, `pydantic`, `dotenv`
- **Internal**: None (standalone)

### MCP Client
- **External**: `pydantic`
- **Internal**: `mcp_clients.client.MCPClient`
- **MCP**: `mcp.ClientSession`, `mcp.client.stdio`

### Wrapper Client
- **External**: `dotenv`
- **Internal**: `AmadeusDirectClient`, `AmadeusMCPOnlyClient`

## Backward Compatibility

The refactoring maintains full backward compatibility through aliases:
- `AmadeusMCPClient` → `AmadeusWrapperClient`
- `AmadeusAPIClient` → `AmadeusDirectClient` 
- `create_amadeus_client()` continues to work as expected