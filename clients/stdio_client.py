#stdio_client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from mcp_experimental.clients.AbstractClient import AbstractMCPClient

class MCPstdioClient(AbstractMCPClient):
    def __init__(self):
        self._stack = None

    async def start_session(self, command, args):
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        server_params = StdioServerParameters(
            command=command,
            args=args,
        )
        stdio = await self._stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio

        _session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await _session.initialize()

        tools_result = await _session.list_tools()
        resources_result = await _session.list_resources()
        prompts_result = await _session.list_prompts()
        

        return _session, tools_result.tools, resources_result.resources, prompts_result.prompts

    async def call_tool(self, command, args, tool_name: str, arguments: dict):
        server_params = StdioServerParameters(
            command=command,  # The command to run your server
            args=args,  # Arguments to the command
        )
        # Connect to the server
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
        return result.content
    
    
    async def read_resource(self, command, args, res_uri: str, arguments: dict ):
        server_params = StdioServerParameters(
            command=command,  # The command to run your server
            args=args,  # Arguments to the command
        )
        # Connect to the server
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.read_resource(res_uri)
        return result.contents
    
    async def get_prompt(self, command, args, name, arguments):
        server_params = StdioServerParameters(
            command=command,  # The command to run your server
            args=args,  # Arguments to the command
        )
        # Connect to the server
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.get_prompt(name, arguments)
        return result.messages

    async def close(self):
        if self._stack is not None:
            try:
                await asyncio.sleep(0.1)  # Zeit für sauberen Abbau
                await self._stack.aclose()
            except Exception as e:
                print(f"[WARN] Fehler beim Schließen einer Session: {e}")

async def main():
    client = MCPstdioClient()
    session, a, b, c = await client.start_session("python",["C://Users//User//Desktop//AI Code//MCP//CursorCustomMCPClient2//mcp_experimental//server.py"])
    output_tool = await client.call_tool(session, "add", {"a": 5, "b": 8})
    print(output_tool)
    output_resource = await client.read_resource(session, "text://greeting")
    print(output_resource)
    output_prompt = await client.get_prompt(session, "simple_greeting", {"name": "AceDragoon"})
    print(output_prompt)
    await client.close()
    session, a, b, c = await client.start_session("python",["C://Users//User//Desktop//AI Code//MCP//CursorCustomMCPClient2//mcp_experimental//example_server.py"])
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
