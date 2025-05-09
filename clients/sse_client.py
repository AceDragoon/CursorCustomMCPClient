#sse_client.py
import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client
from contextlib import AsyncExitStack
from mcp_experimental.clients.AbstractClient import AbstractMCPClient

class MCPsseClient(AbstractMCPClient):
    def __init__(self):
        self._session = None
        self._stack = None

    async def start_session(self, url):
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

    async def call_tool(self, url, tool_name: str, arguments: dict):
        async with sse_client(url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                # Initialize the connection
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
        
        return result.content
    
    async def read_resource(self, _session, uri):
        if _session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        try:
            result = await _session.read_resource(uri)
        except:
            return "Error"
        return result.contents
    
    async def get_prompt(self, _session, name, arguments):
        result = await _session.get_prompt(name, arguments)
        return result.messages 

    async def close(self):
        if self._stack is not None:
            try:
                await asyncio.sleep(0.1)  # Zeit für sauberen Abbau
                await self._stack.aclose()
            except Exception as e:
                print(f"[WARN] Fehler beim Schließen einer Session: {e}")

async def main():
    client = MCPsseClient()
    session, a, b , c = await client.start_session("http://127.0.0.1:8050/sse")
    print(session)
    output_tool = await client.call_tool(session,"add", {"a": 5, "b": 8})
    print(output_tool)
    output_resource = await client.read_resource(session,"text://greeting")
    print(output_resource)
    output_prompt = await client.get_prompt(session,"simple_greeting", {"name": "AceDragoon"})
    print(output_prompt)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
