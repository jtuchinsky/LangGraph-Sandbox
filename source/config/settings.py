import os
from typing import Dict, Any, Optional, List
from pydantic import BaseSettings, Field
from pathlib import Path


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # API Keys
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    mistral_api_key: Optional[str] = Field(None, env="MISTRAL_API_KEY")
    deepseek_api_key: Optional[str] = Field(None, env="DEEPSEEK_API_KEY")
    
    # Search APIs
    google_search_api_key: Optional[str] = Field(None, env="GOOGLE_SEARCH_API_KEY")
    google_search_engine_id: Optional[str] = Field(None, env="GOOGLE_SEARCH_ENGINE_ID")
    
    # Default LLM Settings
    default_llm_provider: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    default_model: str = Field("gpt-4o", env="DEFAULT_MODEL")
    default_temperature: float = Field(0.0, env="DEFAULT_TEMPERATURE")
    default_max_tokens: int = Field(2000, env="DEFAULT_MAX_TOKENS")
    
    # Ollama Settings
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    ollama_default_model: str = Field("llama3.2:3b", env="OLLAMA_DEFAULT_MODEL")
    
    # MCP Settings
    mcp_timeout: int = Field(30, env="MCP_TIMEOUT")
    mcp_max_retries: int = Field(3, env="MCP_MAX_RETRIES")
    
    # Memory Settings
    memory_storage_path: str = Field("memory_storage", env="MEMORY_STORAGE_PATH")
    max_memory_sessions: int = Field(100, env="MAX_MEMORY_SESSIONS")
    session_cleanup_days: int = Field(30, env="SESSION_CLEANUP_DAYS")
    
    # Error Handling
    max_retries: int = Field(3, env="MAX_RETRIES")
    base_retry_delay: float = Field(1.0, env="BASE_RETRY_DELAY")
    max_retry_delay: float = Field(60.0, env="MAX_RETRY_DELAY")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: Optional[str] = Field(None, env="LOG_FILE")
    
    # Development
    debug: bool = Field(False, env="DEBUG")
    development_mode: bool = Field(False, env="DEVELOPMENT_MODE")
    
    # Application
    app_name: str = Field("LangGraph MCP Host", env="APP_NAME")
    app_version: str = Field("0.1.0", env="APP_VERSION")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Получить настройки приложения (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings():
    """Перезагрузить настройки"""
    global _settings
    _settings = None
    return get_settings()


class EnvironmentValidator:
    """Валидатор окружения"""
    
    @staticmethod
    def validate_llm_credentials() -> Dict[str, bool]:
        """Проверить доступность учетных данных LLM"""
        settings = get_settings()
        
        return {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "groq": bool(settings.groq_api_key),
            "mistral": bool(settings.mistral_api_key),
            "deepseek": bool(settings.deepseek_api_key),
            "ollama": True  # Ollama doesn't require API key
        }
    
    @staticmethod
    def validate_search_credentials() -> Dict[str, bool]:
        """Проверить доступность учетных данных для поиска"""
        settings = get_settings()
        
        return {
            "google_search": bool(settings.google_search_api_key and settings.google_search_engine_id),
            "duckduckgo": True  # DuckDuckGo doesn't require API key
        }
    
    @staticmethod
    def validate_directories() -> Dict[str, bool]:
        """Проверить доступность директорий"""
        settings = get_settings()
        
        results = {}
        
        # Memory storage
        memory_path = Path(settings.memory_storage_path)
        try:
            memory_path.mkdir(exist_ok=True)
            results["memory_storage"] = True
        except Exception:
            results["memory_storage"] = False
        
        # Log directory
        if settings.log_file:
            log_path = Path(settings.log_file).parent
            try:
                log_path.mkdir(parents=True, exist_ok=True)
                results["log_directory"] = True
            except Exception:
                results["log_directory"] = False
        
        return results
    
    @staticmethod
    def get_validation_report() -> Dict[str, Any]:
        """Получить полный отчет о валидации окружения"""
        return {
            "llm_credentials": EnvironmentValidator.validate_llm_credentials(),
            "search_credentials": EnvironmentValidator.validate_search_credentials(),
            "directories": EnvironmentValidator.validate_directories(),
            "settings_loaded": True
        }