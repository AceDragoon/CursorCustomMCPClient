#manager.py
import json
import asyncio
from mcp_experimental.utils.paths import get_project_base
from mcp_experimental.servermanagers.AbstractManagers import AbstractManager
from mcp_experimental.clients.stdio_client import MCPstdioClient
from mcp_experimental.clients.sse_client import MCPsseClient
from fastmcp import FastMCP

class Manager(AbstractManager):

    def __init__(self) -> None:
        self.config_path = get_project_base() / "server_config.json"
        self.sessions = {}
        self.clients = []

    async def load_config(self):
        with open(self.config_path, "r") as file:
            config = json.load(file)
        return config
    
    async def add_session(self):
        self.config = await self.load_config()
        for name, server in self.config.get("mcpServers", {}).items():
                
                if "url" in server:
                    client = MCPsseClient()
                    session = await client.start_session(server.get("url"))
                elif "command" in server:
                    client = MCPstdioClient()
                    print(server.get("command"), server.get("args"))
                    session = await client.start_session(server.get("command"), server.get("args"))
                self.sessions[name] = session
                self.clients.append(client)
        return self.sessions
    
    async def shutdown(self):
        for client in self.clients:
            await client.close()

async def main():
    manager = Manager()
    await manager.add_session()
    await manager.shutdown()



if __name__ == "__main__":
    asyncio.run(main())