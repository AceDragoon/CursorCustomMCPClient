from abc import ABC, abstractmethod

class AbstractLLM(ABC):
    @abstractmethod
    async def load_config(self) -> dict:
        pass

    @abstractmethod
    async def load_tools(self) -> dict:
        pass
    
    @abstractmethod
    async def user_message(self) -> dict:
        pass

    @abstractmethod
    async def system_message(self, messages, tools,temperature) -> dict:
        pass

    @abstractmethod
    async def tool_call(self, name, args) -> list:
        pass
    
    @abstractmethod
    async def workflow(self) -> None:
        pass
    @abstractmethod
    async def logic(self) -> None:
        pass

    @abstractmethod
    async def layout(self) -> None:
        pass

    @abstractmethod
    async def main(self) -> None:
        pass