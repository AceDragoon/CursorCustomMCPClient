from abc import ABC, abstractmethod

class AbstractManager(ABC):

    @abstractmethod
    async def load_config(path):
        pass

    @abstractmethod
    async def add_session(self):
        pass

    @abstractmethod
    async def make_request(self):
        pass