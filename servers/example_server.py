from mcp.server.fastmcp import FastMCP

mcp = FastMCP( 
    name="Userdata",
    host="0.0.0.0",
    port=6050,
)

#@mcp.tool()
#def Username() -> str:
#    """get the current Username"""
#    return "AceDragoon"

if __name__ == "__main__":
    mcp.run(transport="sse")