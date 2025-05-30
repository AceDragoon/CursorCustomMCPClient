from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.resource(uri="text://greeting", description="Ein freundlicher Gruß")
def greeting() -> str:
    return "Willkommen beim MCP-Server!"

@mcp.resource(uri="time://now", description="Aktuelle Serverzeit")
def current_time() -> str:
    from datetime import datetime
    return datetime.now().isoformat()

@mcp.prompt()
def simple_greeting(name: str) -> list:
    """Generiere eine nette Begrüßung für eine Person."""
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": f"Bitte begrüße höflich {name}."
            }
        }
    ]



if __name__ == "__main__":
    mcp.run(transport="stdio")
