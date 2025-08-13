from typing import Dict, Any, Optional
from ..agents import (
    BaseLLMAgent, AgentConfig, OpenAIAgent, AnthropicAgent, 
    OllamaAgent, GroqAgent, MistralAgent, DeepSeekAgent
)
from .settings import get_settings


class LLMConfig:
    """Конфигурация LLM агентов"""
    
    # Доступные модели для каждого провайдера
    PROVIDER_MODELS = {
        "openai": [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-3.5-turbo"
        ],
        "anthropic": [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ],
        "groq": [
            "llama-3.1-405b-reasoning",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ],
        "mistral": [
            "mistral-large-latest",
            "mistral-medium-latest", 
            "mistral-small-latest",
            "open-mistral-7b",
            "open-mixtral-8x7b"
        ],
        "deepseek": [
            "deepseek-chat",
            "deepseek-coder"
        ],
        "ollama": [
            "llama3.2:1b",
            "llama3.2:3b", 
            "llama3.1:8b",
            "llama3.1:70b",
            "mistral:7b",
            "codellama:7b",
            "codellama:34b"
        ]
    }
    
    # Рекомендуемые настройки для разных задач
    TASK_CONFIGS = {
        "classification": {
            "temperature": 0.0,
            "max_tokens": 500
        },
        "generation": {
            "temperature": 0.7,
            "max_tokens": 2000
        },
        "code": {
            "temperature": 0.1,
            "max_tokens": 4000
        },
        "analysis": {
            "temperature": 0.2,
            "max_tokens": 1500
        }
    }
    
    @staticmethod
    def get_available_providers() -> Dict[str, bool]:
        """Получить список доступных провайдеров"""
        settings = get_settings()
        
        return {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "groq": bool(settings.groq_api_key),
            "mistral": bool(settings.mistral_api_key),
            "deepseek": bool(settings.deepseek_api_key),
            "ollama": True  # Always available if running
        }
    
    @staticmethod
    def get_provider_models(provider: str) -> list:
        """Получить доступные модели для провайдера"""
        return LLMConfig.PROVIDER_MODELS.get(provider, [])
    
    @staticmethod
    def get_recommended_model(provider: str, task_type: str = "general") -> Optional[str]:
        """Получить рекомендуемую модель для задачи"""
        models = LLMConfig.get_provider_models(provider)
        if not models:
            return None
        
        # Рекомендации по моделям для разных задач
        recommendations = {
            "openai": {
                "classification": "gpt-4o-mini",
                "generation": "gpt-4o", 
                "code": "gpt-4o",
                "analysis": "gpt-4o",
                "general": "gpt-4o"
            },
            "anthropic": {
                "classification": "claude-3-5-haiku-20241022",
                "generation": "claude-3-5-sonnet-20241022",
                "code": "claude-3-5-sonnet-20241022", 
                "analysis": "claude-3-5-sonnet-20241022",
                "general": "claude-3-5-sonnet-20241022"
            },
            "groq": {
                "classification": "llama-3.1-8b-instant",
                "generation": "llama-3.1-70b-versatile",
                "code": "llama-3.1-70b-versatile",
                "analysis": "llama-3.1-70b-versatile", 
                "general": "llama-3.1-70b-versatile"
            },
            "mistral": {
                "classification": "mistral-small-latest",
                "generation": "mistral-large-latest",
                "code": "mistral-large-latest",
                "analysis": "mistral-large-latest",
                "general": "mistral-large-latest"
            },
            "deepseek": {
                "classification": "deepseek-chat",
                "generation": "deepseek-chat",
                "code": "deepseek-coder",
                "analysis": "deepseek-chat",
                "general": "deepseek-chat"
            },
            "ollama": {
                "classification": "llama3.2:3b",
                "generation": "llama3.1:8b",
                "code": "codellama:7b",
                "analysis": "llama3.1:8b",
                "general": "llama3.2:3b"
            }
        }
        
        provider_recommendations = recommendations.get(provider, {})
        recommended_model = provider_recommendations.get(task_type, provider_recommendations.get("general"))
        
        # Verify the model is available
        if recommended_model in models:
            return recommended_model
        
        # Fallback to first available model
        return models[0] if models else None


def create_llm_agent(provider: str, 
                    model: Optional[str] = None,
                    task_type: str = "general",
                    custom_config: Optional[Dict[str, Any]] = None) -> BaseLLMAgent:
    """Создать LLM агента"""
    
    settings = get_settings()
    
    # Determine model
    if not model:
        model = LLMConfig.get_recommended_model(provider, task_type)
        if not model:
            raise ValueError(f"No model available for provider: {provider}")
    
    # Get task-specific config
    task_config = LLMConfig.TASK_CONFIGS.get(task_type, LLMConfig.TASK_CONFIGS["generation"])
    
    # Create agent config
    config_data = {
        "model": model,
        "temperature": task_config["temperature"],
        "max_tokens": task_config["max_tokens"],
        "timeout": 30
    }
    
    # Apply custom config overrides
    if custom_config:
        config_data.update(custom_config)
    
    config = AgentConfig(**config_data)
    
    # Create appropriate agent
    if provider == "openai":
        return OpenAIAgent(config)
    elif provider == "anthropic":
        return AnthropicAgent(config)
    elif provider == "groq":
        return GroqAgent(config)
    elif provider == "mistral":
        return MistralAgent(config)
    elif provider == "deepseek":
        return DeepSeekAgent(config)
    elif provider == "ollama":
        return OllamaAgent(config, base_url=settings.ollama_base_url)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_best_available_agent(task_type: str = "general",
                           custom_config: Optional[Dict[str, Any]] = None) -> BaseLLMAgent:
    """Получить лучший доступный агент для задачи"""
    
    settings = get_settings()
    available_providers = LLMConfig.get_available_providers()
    
    # Priority order for providers
    provider_priority = ["openai", "anthropic", "groq", "mistral", "deepseek", "ollama"]
    
    for provider in provider_priority:
        if available_providers.get(provider, False):
            try:
                return create_llm_agent(provider, task_type=task_type, custom_config=custom_config)
            except Exception as e:
                print(f"Failed to create {provider} agent: {e}")
                continue
    
    raise RuntimeError("No LLM providers available")


def create_multi_agent_setup() -> Dict[str, BaseLLMAgent]:
    """Создать мульти-агентную настройку с разными провайдерами"""
    
    agents = {}
    available_providers = LLMConfig.get_available_providers()
    
    for provider, available in available_providers.items():
        if available:
            try:
                agents[provider] = create_llm_agent(provider)
                print(f"Created {provider} agent")
            except Exception as e:
                print(f"Failed to create {provider} agent: {e}")
    
    return agents