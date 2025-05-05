import asyncio
from abc import ABC, abstractmethod

class AbstractMCPClient(ABC):

    @abstractmethod
    async def start_client(self):
        pass

    @abstractmethod
    async def call_tool(self):
        pass

    @abstractmethod
    async def read_resource(self):
        pass
     
    @abstractmethod
    async def read_resource(self):
        pass

    @abstractmethod
    async def get_prompt(self):
        pass
    
    @abstractmethod
    async def close(self):
        pass