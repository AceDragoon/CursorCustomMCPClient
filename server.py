from fastmcp import FastMCP

mcp = FastMCP("Demo")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Addiert zwei Zahlen."""
    return a + b

if __name__ == "__main__":
    mcp.run(transport="stdio")