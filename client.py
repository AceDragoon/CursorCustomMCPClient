import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

class MCPClient:
    def __init__(self):
        self._session = None
        self._stack = None

    async def start_client(self):
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
        )
        stdio = await self._stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio

        self._session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self._session.initialize()

        tools_result = await self._session.list_tools()
        return tools_result.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        if self._session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        
        result = await self._session.call_tool(tool_name, arguments)
        return result.content

    async def close(self):
        if self._stack is not None:
            await self._stack.aclose()


async def main():
    client = MCPClient()
    await client.start_client()
    output = await client.call_tool("add", {"a": 5, "b": 8})
    print(output)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
