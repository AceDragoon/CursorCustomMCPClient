#manager.py
import json
import asyncio
from utils.paths import get_project_base
from servermanagers.AbstractManagers import AbstractManager
from clients.stdio_client import MCPClient

class Manager(AbstractManager):

    def __init__(self) -> None:
        self.config_path = get_project_base() / "server_config.json"
        self.session_tools = {}
        self.session_resources = {}
        self.session_prompts = {}

    async def load_config(self):
        with open(self.config_path, "r") as file:
            config = json.load(file)
        return config
    
    async def add_session(self):
        client = MCPClient()
        config = await self.load_config()
        for name, server in config.get("mcpServers", {}).items():
                print(f"Server: {name}")
                print("  Command:", server.get("command"))
                print("  Args:", server.get("args"))
                tools, resources, prompts = await client.start_client(server.get("command"), server.get("args"))
                self.session_tools[name] = tools
                self.session_resources[name] = resources
                self.session_prompts[name] = prompts
        print(self.session_tools)
        print(self.session_resources)
        print(self.session_prompts)
        return self.session_tools, self.session_resources, self.session_prompts
    
    async def make_request(self):
        pass

async def main():
    manager = Manager()
    try:
        await manager.add_session()
    finally:
        print()
        for session in manager.sessions.values():
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())