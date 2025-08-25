# Google Flights MCP Client - Testing Guide

## Testing Issue: Server I/O Blocking

When running `google_flights_usage.py`, the MCP server takes over terminal I/O using STDIO transport, which prevents us from seeing the client output in the same terminal.

## Solution: Multi-Terminal Testing

### Method 1: Simple Client Test (No Server Required)

Test basic client functionality without server dependency:

```bash
python examples/test_google_flights_client.py
```

This will test:
- ✅ Client creation
- ✅ Input validation  
- ✅ Error handling
- ✅ Method availability

### Method 2: Full Server Testing (Two Terminals)

For complete functionality testing with the actual MCP server:

#### Terminal 1: Start the Server
```bash
python /Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py
```

Wait for the server to show:
```
Starting MCP server 'Flight Planner' with transport 'stdio'
```

#### Terminal 2: Test Client Connection
```bash
python -c "
import asyncio
from source.mcp_clients.google_flights import create_google_flights_client

async def quick_test():
    client = create_google_flights_client()
    server_command = ['python', '/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py']
    
    print('Testing connection...')
    connected = await client.connect_to_server(server_command)
    print(f'Connected: {connected}')
    
    if connected:
        print('Testing airport search...')
        result = await client.airport_search('Los Angeles')
        print(f'Airport search success: {result[\"success\"]}')
        if result['success']:
            print('✓ Airport search working!')
        
        await client.disconnect_from_server()
        print('✓ Disconnected')
    else:
        print('✗ Connection failed')

asyncio.run(quick_test())
"
```

### Method 3: Individual Tool Testing

Test specific functionality without full example:

```bash
# Test airport search only
python -c "
import asyncio
from source.mcp_clients.google_flights import create_google_flights_client

async def test_airport_search():
    client = create_google_flights_client()
    server_command = ['python', '/Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py']
    
    if await client.connect_to_server(server_command):
        result = await client.airport_search('New York')
        print('Airport search result:')
        print(result['result'] if result['success'] else result['error'])
        await client.disconnect_from_server()

asyncio.run(test_airport_search())
"
```

## Expected Behavior

### Successful Connection
When working correctly, you should see:
1. **Terminal 1**: Server starts and waits for connections
2. **Terminal 2**: Client connects, runs tests, shows results
3. **Terminal 1**: May show server-side activity logs

### Connection Issues
If connection fails, check:
- ✅ Server is running in Terminal 1
- ✅ Server path is correct
- ✅ FastMCP and dependencies installed
- ✅ No firewall blocking local connections

## Alternative Testing Approaches

### 1. Background Server Test
```bash
# Start server in background
python /Users/jacobtuchinsky/PycharmProjects/google-flights-mcp/src/flights-mcp-server.py &
SERVER_PID=$!

# Wait for startup
sleep 3

# Run client test
python examples/test_google_flights_client.py

# Clean up
kill $SERVER_PID
```

### 2. Debug Mode Testing
Add debug output to see what's happening:

```python
# In client code, add:
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed MCP protocol messages
```

### 3. Mock Server Testing
For development, consider creating a mock server that returns dummy data without the I/O blocking issues.

## Troubleshooting

### Server Won't Start
- Check FastMCP installation: `pip list | grep fastmcp`
- Check server path exists
- Check Python version compatibility

### Client Won't Connect  
- Verify server is actually listening
- Check MCP protocol version compatibility
- Try with different server commands

### I/O Issues
- Use separate terminals/processes
- Consider logging to files instead of stdout
- Use background processes with output redirection

## Production Usage

For production use, consider:
- Running MCP server as a service
- Using TCP transport instead of STDIO
- Implementing proper logging and monitoring
- Adding health checks and reconnection logic