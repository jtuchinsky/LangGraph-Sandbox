import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel


class AgentConfig(BaseModel):
    model: str
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    timeout: int = 30


class BaseLLMAgent(ABC):
    def __init__(self, config: AgentConfig):
        self.config = config
        self._load_environment()
        self._validate_credentials()
    
    def _load_environment(self):
        load_dotenv()
    
    @abstractmethod
    def _validate_credentials(self):
        """Validate required API credentials"""
        pass
    
    @abstractmethod
    def get_llm(self):
        """Get the LLM instance"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name"""
        pass
    
    def invoke(self, message: str, **kwargs) -> str:
        """Invoke the LLM with a message"""
        llm = self.get_llm()
        response = llm.invoke(message, **kwargs)
        return response.content if hasattr(response, 'content') else str(response)