import asyncio
import os
from mcp.server.fastmcp import FastMCP
from src.tools.tools import register_tools
from src.services.async_consul_client import AsyncConsulClient

def setup_mcp(mcp_server: FastMCP):
    register_tools(mcp_server)

async def check_consul_health(consul_client: AsyncConsulClient) -> bool:
    return await consul_client.is_healthy()

mcp = FastMCP("consul_mcp_server")
setup_mcp(mcp)

def main():
    consul_client = AsyncConsulClient()

    print("Validating if consul is reachable")
    is_healthy = asyncio.run(consul_client.is_healthy())

    if not is_healthy:
        print("Consul is unhealthy. MCP server will not start.")
        return

    transport = os.getenv("MCP_TRANSPORT", "streamable-http")

    print(f"✅ Consul is healthy. Running server with {transport} transport")
    if transport in ("stdio", "sse", "streamable-http"):
        mcp.run(transport=transport)
    else:
        raise ValueError(f"Unknown transport: {transport}")

if __name__ == "__main__":
    main()
