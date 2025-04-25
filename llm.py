import asyncio
from contextlib import AsyncExitStack
from typing import Tuple, Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPToolClient:
    def __init__(self, script_path="server.py"):
        self.script_path = script_path
        self.session: ClientSession = None
        self.stack: AsyncExitStack = None
        self.tools = []

    async def start(self):
        self.stack = AsyncExitStack()
        await self.stack.__aenter__()

        params = StdioServerParameters(command="python", args=[self.script_path])
        read_stream, write_stream = await self.stack.enter_async_context(stdio_client(params))
        self.session = await self.stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()

        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools

    def get_openai_function_definitions(self):
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema
            }
            for tool in self.tools
        ]

    async def call_tool(self, name: str, args: Dict[str, Any]) -> str:
        result = await self.session.call_tool(name, args)
        return str(result.content)

    async def shutdown(self):
        if self.stack:
            await self.stack.aclose()
