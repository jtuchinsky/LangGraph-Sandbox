import os
from langchain_openai import ChatOpenAI
from .base_agent import BaseLLMAgent, AgentConfig


class OpenAIAgent(BaseLLMAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    def _validate_credentials(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
    
    def get_llm(self):
        return ChatOpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            openai_api_key=self.api_key,
            timeout=self.config.timeout
        )
    
    def get_provider_name(self) -> str:
        return "openai"