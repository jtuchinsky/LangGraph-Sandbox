# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive LangGraph MCP Host application that serves as a multi-LLM AI agent with Model Context Protocol (MCP) client integration. The project has evolved significantly from a simple sandbox to a full-featured AI application.

## Project Structure

```
├── source/
│   ├── agents/              # Multi-LLM agent implementations
│   ├── mcp_clients/         # MCP client implementations
│   │   └── amadeus/         # Amadeus travel API client (refactored)
│   │       ├── direct_client.py      # Direct API client
│   │       ├── mcp_client.py         # MCP-only client
│   │       ├── wrapper_client.py     # Unified wrapper with fallback
│   │       └── __init__.py           # Factory functions and exports
│   ├── mcp_servers/         # MCP server implementations
│   │   └── amadeus/         # Amadeus MCP server
│   ├── graph/               # LangGraph state machine
│   ├── tools/               # Filesystem and web search tools
│   ├── memory/              # Dialogue context memory
│   ├── utils/               # Error handling and retry logic
│   ├── config/              # Settings and LLM configuration
│   └── main.py              # Main application entry point
├── examples/                # Usage examples
├── docs/                    # Architecture documentation
└── README.md                # Comprehensive project documentation
```

## Development Setup

The project uses:
- Python 3.11+
- UV package manager (preferred)
- Docker (for Ollama support)
- Multiple LLM APIs (OpenAI, Anthropic, DeepSeek, Groq, Mistral)

## Environment Variables Required

```env
# LLM API Keys
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GROQ_API_KEY=your_groq_key
MISTRAL_API_KEY=your_mistral_key
DEEPSEEK_API_KEY=your_deepseek_key

# Amadeus Travel API
AMADEUS_CLIENT_ID=your_amadeus_client_id
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret
AMADEUS_HOST=test  # or "prod" for production

# Search APIs
GOOGLE_SEARCH_API_KEY=your_google_key
GOOGLE_SEARCH_ENGINE_ID=your_engine_id

# Configuration
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
OLLAMA_BASE_URL=http://localhost:11434
```

## Commands

### Installing dependencies
```bash
uv pip install -r requirements.txt
```

### Running the main application
```bash
python -m source.main
```

### Running Amadeus examples
```bash
python examples/amadeus_usage.py
```

### Running Amadeus MCP server
```bash
python -m source.mcp_servers.amadeus.server
```

### Docker setup for Ollama
```bash
chmod +x scripts/setup_ollama.sh
./scripts/setup_ollama.sh
docker-compose up -d ollama
```

### Testing specific components
```bash
# Test Amadeus client import
python -c "from source.mcp_clients.amadeus import create_amadeus_client; print('Import successful')"

# Test server import
python -c "from source.mcp_servers.amadeus.server import main; print('Server import successful')"
```

## Code Architecture

### Multi-LLM Support
- **OpenAI**: GPT-4, GPT-3.5 models
- **Anthropic**: Claude 3.5 Sonnet, Haiku, Opus
- **DeepSeek**: Chat and Coder models
- **Groq**: Llama, Mixtral, Gemma models
- **Mistral**: Large, Medium, Small models
- **Local LLMs**: via Ollama + Docker

### Amadeus Travel API Integration (Recently Refactored)
The Amadeus client has been refactored into three separate components:

1. **AmadeusDirectClient** (`direct_client.py`): Low-level direct API access with OAuth 2.0
2. **AmadeusMCPOnlyClient** (`mcp_client.py`): Pure MCP protocol client
3. **AmadeusWrapperClient** (`wrapper_client.py`): High-level facade with intelligent fallback

### Key Features
- **Filesystem Operations**: Read, create, modify, delete files
- **Internet Search**: Google Search API, DuckDuckGo fallback
- **Dialogue Memory**: Persistent context and session management
- **Error Recovery**: Automatic retry mechanisms and fallback strategies
- **Task Classification**: Intelligent routing based on task type
- **MCP Integration**: Model Context Protocol for external tool integration

### Recent Major Changes
1. **Amadeus Client Refactoring**: Split monolithic client into modular architecture
2. **Round-trip Flight Search**: Fixed API payload structure for v2 endpoints
3. **Documentation Updates**: Comprehensive architecture diagrams and guides
4. **Import Fixes**: Resolved server import issues after refactoring
5. **Example Improvements**: Fixed display limits and pricing clarification

## Testing

### Flight Search Testing
The project includes comprehensive examples for testing Amadeus functionality:
- Direct API usage
- MCP server integration
- Hybrid fallback patterns
- Round-trip flight search with detailed airline information

### Common Issues
- **Authentication**: Ensure AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET are set
- **Round-trip Search**: API requires separate origin-destination objects for outbound/return
- **Import Paths**: Use the new modular client imports after refactoring

## Development Notes

- The project maintains backward compatibility through factory functions and aliases
- All clients can be used independently or together
- Error handling includes automatic fallback from MCP to direct API
- Comprehensive logging and monitoring capabilities built-in
- Docker support for both development and deployment

This is a mature, production-ready application with extensive documentation and example usage patterns.