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
            
            #initialisiert die Session
            await session.initialize()

            #listet alle tools auf
            tools_result = await session.list_tools()

            #listet alle Ressourcen auf
            resources_result = await session.list_resources()

            result = (tools_result,resources_result)
            
    return (result) 


if __name__ == "__main__":
    output = asyncio.run(start_client())
    print(output)

