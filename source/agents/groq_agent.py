import os
from groq import Groq
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from .base_agent import BaseLLMAgent, AgentConfig


class GroqChatModel(BaseChatModel):
    client: Groq
    model_name: str
    temperature: float
    max_tokens: int
    
    def __init__(self, client: Groq, model_name: str, temperature: float = 0.0, max_tokens: int = None):
        super().__init__()
        self.client = client
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    def _generate(self, messages, stop=None, **kwargs):
        groq_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                groq_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                groq_messages.append({"role": "assistant", "content": msg.content})
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=groq_messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return AIMessage(content=response.choices[0].message.content)
    
    def invoke(self, input_text, **kwargs):
        if isinstance(input_text, str):
            messages = [HumanMessage(content=input_text)]
        else:
            messages = input_text
        return self._generate(messages, **kwargs)
    
    @property
    def _llm_type(self) -> str:
        return "groq"


class GroqAgent(BaseLLMAgent):
    def __init__(self, config: AgentConfig):
        super().__init__(config)
    
    def _validate_credentials(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
    
    def get_llm(self):
        client = Groq(api_key=self.api_key)
        return GroqChatModel(
            client=client,
            model_name=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
    
    def get_provider_name(self) -> str:
        return "groq"