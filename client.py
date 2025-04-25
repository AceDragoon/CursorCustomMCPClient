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
            await session.initialize()
            print("listing_tools:")
            tools_result = await session.list_tools()
            print(tools_result)
            print("Available tools: ")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # Ressourcen auflisten
            resources_result = await session.list_resources()
            print("📚 Verfügbare Ressourcen:")
            print(resources_result)
            for resource in resources_result.resources:
                print(f"  - {resource.uri}: {resource.name} ({resource.mimeType})")


            # Beispiel: Erste Ressource lesen
            if not resources_result.resources:
                print("Keine Ressourcen verfügbar.")

            #result = await session.call_tool("Username", arguments={})
            #print(result)


if __name__ == "__main__":
    asyncio.run(start_client())
