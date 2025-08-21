# Amadeus MCP Client Package - Class Diagram

```mermaid
classDiagram
    class OAuthToken {
        +access_token: str
        +token_type: str
        +expires_in: int
        +scope: Optional[str]
        +created_at: float
        +is_expired: bool
    }

    class AmadeusAPIClient {
        -client_id: str
        -client_secret: str
        -base_url: str
        -_token: Optional[OAuthToken]
        -_client: httpx.Client
        +__init__(client_id, client_secret, base_url)
        -_ensure_token()
        -_auth_headers(): Dict[str, str]
        +autocomplete_locations(query, limit, sub_types): dict
        +search_flights(origin, destination, departure_date, ...): dict
        +price_offer(flight_offer, currency): dict
        +close()
    }

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

    class AmadeusMCPClient {
        +client_id: str
        +client_secret: str
        +base_url: str
        +api_client: AmadeusAPIClient
        +default_currency: str
        +default_max_results: int
        +mcp_client: Optional[MCPClient]
        +__init__(client_id, client_secret, host)
        +connect_to_mcp_server(server_command): bool
        +disconnect_from_mcp_server()
        +autocomplete_locations_direct(query, limit, sub_types): dict
        +search_flights_direct(args): dict
        +price_offer_direct(args): dict
        +autocomplete_locations_mcp(query, limit, sub_types): dict
        +search_flights_mcp(search_args): dict
        +price_offer_mcp(flight_offer, currency): dict
        +autocomplete_locations(query, limit, sub_types, prefer_mcp): dict
        +search_flights(search_args, prefer_mcp): dict
        +price_offer(flight_offer, currency, prefer_mcp): dict
        +close()
    }

    %% Relationships
    AmadeusAPIClient --> OAuthToken : uses
    AmadeusMCPClient --> AmadeusAPIClient : contains
    AmadeusMCPClient --> MCPClient : contains
    AmadeusMCPClient --> AutocompleteArgs : uses
    AmadeusMCPClient --> SearchArgs : uses
    AmadeusMCPClient --> PriceArgs : uses

    %% Inheritance
    AutocompleteArgs --|> BaseModel : extends
    SearchArgs --|> BaseModel : extends
    PriceArgs --|> BaseModel : extends
    OAuthToken --|> BaseModel : extends

    %% Factory function
    class create_amadeus_client {
        <<function>>
        +create_amadeus_client(client_id, client_secret, host): AmadeusMCPClient
    }
    create_amadeus_client --> AmadeusMCPClient : creates

    %% Notes
    note for AmadeusMCPClient "Main facade class providing both\ndirect API access and MCP server\nintegration with automatic fallback"
    note for AmadeusAPIClient "Low-level HTTP client for\ndirect Amadeus API access\nwith OAuth 2.0 authentication"
    note for MCPClient "Generic MCP client for\ncommunicating with MCP servers"
```

## Package Structure

```
mcp_clients/amadeus/
├── __init__.py
└── client.py
    ├── OAuthToken (Pydantic model)
    ├── AmadeusAPIClient (Low-level API client)
    ├── AutocompleteArgs (Pydantic model)
    ├── SearchArgs (Pydantic model)
    ├── PriceArgs (Pydantic model)
    ├── AmadeusMCPClient (High-level facade)
    └── create_amadeus_client() (Factory function)
```

## Key Design Patterns

1. **Facade Pattern**: `AmadeusMCPClient` provides a unified interface for both direct API and MCP server access
2. **Strategy Pattern**: Automatic fallback from MCP to direct API based on availability
3. **Factory Pattern**: `create_amadeus_client()` function for easy instantiation
4. **Composition**: `AmadeusMCPClient` contains both `AmadeusAPIClient` and `MCPClient`

## Usage Flow

1. Create client using factory function
2. Optionally connect to MCP server
3. Use convenience methods with automatic fallback
4. Direct API methods always available as backup
5. Close connections when done

## Dependencies

- **External**: `httpx`, `pydantic`, `dotenv`
- **Internal**: `mcp_clients.client.MCPClient`
- **MCP**: `mcp.ClientSession`, `mcp.client.stdio`