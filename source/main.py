#!/usr/bin/env python3

import asyncio
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .config import get_settings, EnvironmentValidator, create_llm_agent, get_best_available_agent
from .graph import WorkflowGraph
from .mcp import MCPHost
from .memory import ContextMemory
from .tools import FileSystemTools, WebSearchTools
from .utils import ErrorHandler


class LangGraphMCPApplication:
    """Главное приложение MCP Host с LangGraph"""
    
    def __init__(self):
        self.settings = get_settings()
        self.setup_logging()
        
        # Core components
        self.error_handler = ErrorHandler()
        self.context_memory = ContextMemory(
            storage_path=self.settings.memory_storage_path,
            max_sessions=self.settings.max_memory_sessions
        )
        self.mcp_host = MCPHost()
        
        # Tools
        self.filesystem_tools = FileSystemTools()
        self.web_search_tools = WebSearchTools(
            search_api_key=self.settings.google_search_api_key,
            search_engine_id=self.settings.google_search_engine_id
        )
        
        # LLM and workflow
        self.llm_agent = None
        self.workflow_graph = None
        
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Настройка логирования"""
        level = getattr(logging, self.settings.log_level.upper(), logging.INFO)
        
        # Basic config
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File logging if specified
        if self.settings.log_file:
            log_path = Path(self.settings.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setLevel(level)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
    
    async def initialize(self):
        """Инициализация приложения"""
        self.logger.info("Initializing LangGraph MCP Application...")
        
        # Validate environment
        validation_report = EnvironmentValidator.get_validation_report()
        self.logger.info(f"Environment validation: {validation_report}")
        
        try:
            # Initialize LLM agent
            self.llm_agent = get_best_available_agent(task_type="classification")
            self.logger.info(f"Initialized LLM agent: {self.llm_agent.get_provider_name()}")
            
            # Initialize workflow graph
            self.workflow_graph = WorkflowGraph(self.llm_agent, self.mcp_host)
            self.logger.info("Initialized workflow graph")
            
            # Setup MCP clients (example configurations)
            await self.setup_mcp_clients()
            
            self.logger.info("Application initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            raise
    
    async def setup_mcp_clients(self):
        """Настройка MCP клиентов"""
        # Example MCP client configurations
        # These would be configured based on available MCP servers
        
        mcp_configs = [
            # Example: File system MCP server
            {
                "name": "filesystem",
                "command": ["python", "-m", "mcp_filesystem"],
                "args": []
            },
            # Example: Web search MCP server  
            {
                "name": "web_search",
                "command": ["python", "-m", "mcp_web_search"],
                "args": []
            }
        ]
        
        for config in mcp_configs:
            try:
                success = await self.mcp_host.add_client(
                    config["name"],
                    config["command"],
                    config["args"]
                )
                if success:
                    self.logger.info(f"Connected MCP client: {config['name']}")
                else:
                    self.logger.warning(f"Failed to connect MCP client: {config['name']}")
            except Exception as e:
                self.logger.error(f"Error setting up MCP client {config['name']}: {e}")
    
    async def process_task(self, description: str, session_id: str = "default") -> Dict[str, Any]:
        """Обработать задачу через workflow"""
        
        self.logger.info(f"Processing task for session {session_id}: {description[:100]}...")
        
        try:
            # Add user message to context
            self.context_memory.add_message(session_id, "user", description)
            
            # Run workflow
            result = await self.workflow_graph.run(description, session_id)
            
            # Add assistant response to context
            self.context_memory.add_message(
                session_id, 
                "assistant", 
                json.dumps(result, ensure_ascii=False)
            )
            
            self.logger.info(f"Task completed for session {session_id}")
            return result
            
        except Exception as e:
            error_result = await self.error_handler.handle_error(
                e, "main_application", "process_task", 
                {"session_id": session_id, "description": description}
            )
            
            self.logger.error(f"Task processing failed: {error_result}")
            return error_result
    
    async def get_conversation_context(self, session_id: str) -> str:
        """Получить контекст разговора"""
        return self.context_memory.get_conversation_context(session_id)
    
    async def search_web(self, query: str) -> Dict[str, Any]:
        """Поиск в интернете"""
        try:
            # Try MCP web search first
            if "web_search" in self.mcp_host.clients:
                result = await self.mcp_host.call_tool("web_search", "search", {"query": query})
                if result["success"]:
                    return result
            
            # Fallback to built-in web search
            return self.web_search_tools.search_with_fallback(query)
            
        except Exception as e:
            return await self.error_handler.handle_error(
                e, "web_search", "search", {"query": query}
            )
    
    async def file_operation(self, operation: str, **kwargs) -> Dict[str, Any]:
        """Операции с файлами"""
        try:
            # Try MCP filesystem first
            if "filesystem" in self.mcp_host.clients:
                result = await self.mcp_host.call_tool("filesystem", operation, kwargs)
                if result["success"]:
                    return result
            
            # Fallback to built-in filesystem tools
            if hasattr(self.filesystem_tools, operation):
                method = getattr(self.filesystem_tools, operation)
                return method(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown file operation: {operation}"
                }
                
        except Exception as e:
            return await self.error_handler.handle_error(
                e, "filesystem", operation, kwargs
            )
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Получить статус системы"""
        try:
            # MCP clients status
            mcp_status = {}
            for name, client in self.mcp_host.clients.items():
                mcp_status[name] = client.connected
            
            # Available tools from MCP clients
            mcp_tools = await self.mcp_host.list_all_tools()
            
            return {
                "status": "running",
                "llm_agent": {
                    "provider": self.llm_agent.get_provider_name() if self.llm_agent else None,
                    "model": self.llm_agent.config.model if self.llm_agent else None
                },
                "mcp_clients": mcp_status,
                "mcp_tools": {name: len(tools) for name, tools in mcp_tools.items()},
                "memory_sessions": len(self.context_memory.sessions),
                "error_stats": self.error_handler.get_error_statistics(),
                "settings": {
                    "memory_storage": self.settings.memory_storage_path,
                    "max_retries": self.settings.max_retries,
                    "log_level": self.settings.log_level
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def shutdown(self):
        """Завершение работы приложения"""
        self.logger.info("Shutting down application...")
        
        try:
            # Shutdown MCP clients
            await self.mcp_host.shutdown()
            
            # Cleanup old memory sessions
            self.context_memory.cleanup_old_sessions(self.settings.session_cleanup_days)
            
            self.logger.info("Application shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


async def main():
    """Главная функция"""
    app = LangGraphMCPApplication()
    
    try:
        await app.initialize()
        
        # Example usage
        print("🚀 LangGraph MCP Host started!")
        print("📊 System status:")
        status = await app.get_system_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        
        # Example task processing
        print("\n🔍 Processing example task...")
        task = "Найти информацию о последних новостях в области ИИ и сохранить в файл"
        result = await app.process_task(task)
        print("📝 Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Interactive mode (simple example)
        print("\n💬 Interactive mode (type 'quit' to exit):")
        while True:
            try:
                user_input = input("\nВаш запрос: ").strip()
                if user_input.lower() in ['quit', 'exit', 'выход']:
                    break
                
                if user_input:
                    result = await app.process_task(user_input)
                    print("\n📋 Результат классификации:")
                    print(json.dumps(result, indent=2, ensure_ascii=False))
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
        
    except Exception as e:
        print(f"❌ Application failed: {e}")
        
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())