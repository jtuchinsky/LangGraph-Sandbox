from .direct_client import AmadeusDirectClient, create_direct_client
from .mcp_client import AmadeusMCPClient as AmadeusMCPOnlyClient, create_mcp_client
from .wrapper_client import AmadeusWrapperClient, create_amadeus_client

# Maintain backward compatibility
AmadeusMCPClient = AmadeusWrapperClient
AmadeusAPIClient = AmadeusDirectClient  # Legacy alias

__all__ = [
    # Direct API client
    "AmadeusDirectClient", 
    "create_direct_client",
    
    # MCP-only client
    "AmadeusMCPOnlyClient", 
    "create_mcp_client",
    
    # Wrapper client (main interface)
    "AmadeusWrapperClient",
    "AmadeusMCPClient",  # Backward compatibility alias
    "create_amadeus_client",  # Main factory function
    
    # Legacy aliases
    "AmadeusAPIClient",  # Legacy alias for AmadeusDirectClient
]