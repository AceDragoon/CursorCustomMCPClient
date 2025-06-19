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
                    session = await client.start_session(server.get("command"), server.get("args"))
                self.sessions[name] = session
                self.clients.append(client)
                await client.close()
                print(f"Server {name} initialisiert")
        functions = await self.get_functions()
        return functions
    
    async def get_functions(self):
        all_tools, all_resources, all_prompts = [], [], []

        for session in self.sessions.values():
            tools, resources, prompts = session[1:]  # überspringe ClientSession
            all_tools += tools
            all_resources += resources
            all_prompts += prompts

        return (all_tools, all_resources, all_prompts)
    
    def find_server_by_function_name(self, function_name: str) -> str | None:
        for server_name, session_data in self.sessions.items():
            for index, function_list in enumerate(session_data[1:]):  # [1]=Tools, [2]=Resources, [3]=Prompts
                for obj in function_list:
                    if obj.name == function_name:
                        return server_name, index  # index: 0 = Tool, 1 = Resource, 2 = Prompt
        return None, None
    
    async def make_request(self, function_name, arguments):
        print(arguments)
        config = await self.load_config()
        server_name, type = self.find_server_by_function_name(function_name)
        server = config.get("mcpServers", {}).get(server_name)
        if "url" in server:
            client = MCPsseClient()
            if type == 0:
                function_result = await client.call_tool(server.get("url"), function_name, arguments)
            elif type == 1:
                result = await client.read_resource(server.get("url"), function_name, arguments)
                function_result = result[0].text
            elif type == 2:
                function_result = await client.get_prompt(server.get("url"), function_name, arguments)
        elif "command" in server:
            client = MCPstdioClient()
            if type == 0:
                function_result = await client.call_tool(server.get("command"), server.get("args"), function_name, arguments)
            if type == 1:
                result = await client.read_resource(server.get("command"), server.get("args"), function_name, arguments)
                function_result = result[0].text
            if type == 2:
                function_result = await client.get_prompt(server.get("command"), server.get("args"), function_name, arguments)
        print(f"Request result : {function_result}")
        return function_result
        
    
    async def shutdown(self):
        pass

async def main():
    manager = Manager()
    await manager.add_session()
    await manager.get_functions()
    function_result = await manager.make_request("save_graphviz_diagram", {'code': 'digraph G {\n  A -> B;\n  B -> C;\n  C -> A;\n}', 'filename': 'mini_diagram'})
    print(function_result)


if __name__ == "__main__":
    asyncio.run(main())