#stdio_client.py
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

class MCPClient:
    def __init__(self):
        self._session = None
        self._stack = None

    async def start_client(self,command,args):
        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        server_params = StdioServerParameters(
            command=command,
            args=args,
        )
        stdio = await self._stack.enter_async_context(stdio_client(server_params))
        read_stream, write_stream = stdio

        self._session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self._session.initialize()

        tools_result = await self._session.list_tools()
        resources_result = await self._session.list_resources()
        prompts_result = await self._session.list_prompts()

        return tools_result.tools, resources_result.resources, prompts_result.prompts

    async def call_tool(self, tool_name: str, arguments: dict):
        if self._session is None:
            raise Exception("Session wurde noch nicht gestartet! Bitte zuerst start_client() aufrufen.")
        
        result = await self._session.call_tool(tool_name, arguments)
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
            try:
                await asyncio.sleep(0.1)  # Zeit für sauberen Abbau
                await self._stack.aclose()
            except Exception as e:
                print(f"[WARN] Fehler beim Schließen einer Session: {e}")

async def main():
    client = MCPClient()
    result = await client.start_client()
    print(result)
    output_tool = await client.call_tool("add", {"a": 5, "b": 8})
    print(output_tool)
    output_resource = await client.read_resource("text://greeting")
    print(output_resource)
    output_prompt = await client.get_prompt("simple_greeting", {"name": "AceDragoon"})
    print(output_prompt)
    await client.close()

if __name__ == "__main__":
    asyncio.run(main())
