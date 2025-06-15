from abc import ABC, abstractmethod

class AbstractLLM(ABC):
    @abstractmethod
    async def message_from_user(self) -> str:
        pass

    @abstractmethod
    async def retrieve_tools(self) -> list:
        pass
    
    @abstractmethod
    async def retrieve_config(self) -> dict:
        pass

    @abstractmethod
    async def create_functions(self) -> str:
        pass

    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str, tools: list, repetition: int, temperature: float) -> str:
        pass

    @abstractmethod
    async def function_call(self, function_call: str) -> str:
        pass
    
    @abstractmethod
    async def main_loop(self) -> None:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass