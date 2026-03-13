from infrastructure.mcp import create_mcp

mcp = create_mcp()

if __name__ == "__main__":
    mcp.run(transport="stdio")
