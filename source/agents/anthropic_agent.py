import os
from langchain_anthropic import ChatAnthropic
from .base_agent import BaseLLMAgent, AgentConfig


class AnthropicAgent(BaseLLMAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    def _validate_credentials(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    def get_llm(self):
        return ChatAnthropic(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            anthropic_api_key=self.api_key,
            timeout=self.config.timeout
        )
    
    def get_provider_name(self) -> str:
        return "anthropic"