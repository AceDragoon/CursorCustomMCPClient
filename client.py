import asyncio
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

async def start_client():
    server_params = StdioServerParameters(
        command="python",  # The command to run your server
        args=["server.py"],  # Arguments to the command
    )


    async with stdio_client(server_params) as (read_stream,write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            print("Initializing session:")

            try:
                await asyncio.wait_for(session.initialize(), timeout=5)
            except asyncio.TimeoutError:
                print("Initialisierung des MCP-Servers hat zu lange gedauert.")

            print("listing_tools:")
            tools_result = await session.list_tools()
            print("Available tools: ")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")
            

            result = await session.call_tool("Username", arguments={})
            print(result)


if __name__ == "__main__":
    asyncio.run(start_client())
