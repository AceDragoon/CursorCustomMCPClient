#manager.py
import json
import asyncio
from utils.paths import get_project_base
from servermanagers.AbstractManagers import AbstractManager
from clients.stdio_client import MCPClient
from fastmcp import FastMCP

class Manager(AbstractManager):

    def __init__(self) -> None:
        self.client = MCPClient()
        self.config_path = get_project_base() / "server_config.json"
        self.sessions = []
        self.server_session = {} 

    async def load_config(self):
        with open(self.config_path, "r") as file:
            config = json.load(file)
        return config
    
    async def add_session(self):
        self.config = await self.load_config()
        for name, server in self.config.get("mcpServers", {}).items():
                print(f"Server: {name}")
                print("  Command:", server.get("command"))
                print("  Args:", server.get("args"))
                session = await self.client.start_client(server.get("command"), server.get("args"), name)
                for tool in session[0]:
                    tool.server = name  
                self.sessions.extend(session[0]) 
                self.server_session[name] = session
        print(self.sessions)
        return self.sessions
    
    async def make_request(self):
        pass

    def get_session_by_tool_name(self, tool_name):
        for tool in self.sessions:
            if tool.name == tool_name:
                return self.server_session.get(tool.server)
        return None

    def get_session_by_resource_uri(self, uri):
        for resource in self.resources:
            if resource.uri == uri:
                return self.server_session.get(resource.server)
        return None

    def get_session_by_prompt_name(self, prompt_name):
        for prompt in self.prompts:
            if prompt.name == prompt_name:
                return self.server_session.get(prompt.server)
        return None

    async def call_tool(self, tool_name: str, arguments: dict):
        _session = self.get_session_by_tool_name(tool_name)
        if _session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")

        print(f"📤 Sende Tool-Call an Session für Tool '{tool_name}': {arguments}")
        result = await _session.call_tool(tool_name, arguments)
        print(f"📥 Ergebnis-Objekt: {result}")
        print(f"📦 result.content: {result.content}")
        return result.content

    async def read_resource(self, uri):
        _session = self.get_session_by_resource_uri(uri)
        if _session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        try:
            result = await _session.read_resource(uri)
        except:
            return "Error"
        return result.contents

    async def get_prompt(self, name, arguments):
        _session = self.get_session_by_prompt_name(name)
        if _session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        result = await _session.get_prompt(name, arguments)
        return result.messages

async def main():
    manager = Manager()
    try:
        await manager.add_session()

        # 🔽 Testaufruf für Tool "add"
        tool_name = "add"
        arguments = {"a": 3, "b": 4}

        print(f"\n🔧 Test: Tool '{tool_name}' mit Argumenten {arguments}")
        result = await manager.call_tool(tool_name, arguments)
        print(f"✅ Ergebnis: {result}")

    finally:
        print("\n🔻 Schließe Sessions ...")
        for session in manager.server_session.values():
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())