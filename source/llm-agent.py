import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


class LLMAgent(ABC):
    def __init__(self):
        self._load_environment()
    
    def _load_environment(self):
        load_dotenv()
    
    @abstractmethod
    def get_lm(self, model: str):
        pass


class OpenAIAgent(LLMAgent):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
    
    def get_lm(self, model: str):
        return ChatOpenAI(
            model_name=model,
            temperature=0,
            openai_api_key=self.api_key
        )

if __name__ == "__main__":
    agent = OpenAIAgent()
    llm = agent.get_lm(model="gpt-4o"
                       )
    response = llm.invoke("Кто ты?")
    print(response.content)