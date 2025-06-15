#client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack

class MCPClient:
    def __init__(self):
        self._session = None
        self._stack = None

    async def stdio_session(self):
        self._stack = AsyncExitStack()

        server_params = StdioServerParameters(
            command="python",
            args=["server.py"],
        )
        stdio = await self._stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio

        _session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await _session.initialize()

        tools_result = await _session.list_tools()
        resources_result = await _session.list_resources()
        prompts_result = await _session.list_prompts()

        return _session, tools_result.tools, resources_result.resources, prompts_result.prompts
    
    async def sse_session(self, url):
        self._stack = AsyncExitStack()

        # Stelle Verbindung über SSE her
        sse = await self._stack.enter_async_context(sse_client(url))
        read_stream, write_stream = sse

        # Initialisiere die ClientSession
        _session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await _session.initialize()

        # Lade Tools, Ressourcen und Prompts
        tools_result = await _session.list_tools()
        resources_result = await _session.list_resources()
        prompts_result = await _session.list_prompts()

        return _session, tools_result.tools, resources_result.resources, prompts_result.prompts

    async def call_tool(self, _session, tool_name: str, arguments: dict):
        if _session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        
        result = await _session.call_tool(tool_name, arguments)
        return result.content
    
    async def read_resource(self, uri):
        if self._session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        try:
            result = await self._session.read_resource(uri)
        except:
            return "Error"
        return result.contents
    
    async def get_prompt(self, name, arguments):
        result = await self._session.get_prompt(name, arguments)
        return result.messages 

    async def close(self):
        if self._stack is not None:
            await self._stack.aclose()


async def main():
    client1 = MCPClient()
    session, a,b,c = await client1.sse_session("http://localhost:8050/sse")
    output_tool = await client1.call_tool(session,"add", {"a": 5, "b": 8})
    await client1.close()
    client2 = MCPClient()
    session2, a, b, c = await client2.sse_session("http://localhost:6050/sse")
    await client2.close()
    print(output_tool)
        #output_resource = await client.read_resource("text://greeting")
        #print(output_resource)
        #output_prompt = await client.get_prompt("simple_greeting", {"name": "AceDragoon"})
        #print(output_prompt)

if __name__ == "__main__":
    asyncio.run(main())
