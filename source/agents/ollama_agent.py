import os
from langchain_ollama import ChatOllama
from .base_agent import BaseLLMAgent, AgentConfig


class OllamaAgent(BaseLLMAgent):
    def __init__(self, config: AgentConfig, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        super().__init__(config)
    
    def _validate_credentials(self):
        # Ollama doesn't require API keys for local deployment
        pass
    
    def get_llm(self):
        return ChatOllama(
            model=self.config.model,
            temperature=self.config.temperature,
            base_url=self.base_url,
            timeout=self.config.timeout
        )
    
    def get_provider_name(self) -> str:
        return "ollama"