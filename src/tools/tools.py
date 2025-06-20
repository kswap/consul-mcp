import json
import traceback

from pydantic.json import pydantic_encoder
from mcp.server.fastmcp import FastMCP
from src.services.async_consul_client import AsyncConsulClient
from src.tools.models import GetServiceConnectionsInput, ServiceConnectionResponse, ServiceDetailResponse, \
    ServiceConnection


def register_tools(mcp: FastMCP):
    print("🔧 register_tools() called")

    @mcp.tool()
    async def list_services() -> dict[str, list[str]]:
        """
        Returns a dictionary of registered service names and their tags.
        """
        client = AsyncConsulClient()
        services = await client.get_services()
        if services is None:
            raise RuntimeError("Failed to fetch services from Consul")
        return services

    @mcp.tool()
    async def service_details() -> list[ServiceDetailResponse]:
        """
        Returns detailed information and health for all services except 'consul'.
        """
        client = AsyncConsulClient()
        services = await client.get_services_detailed()
        return [ServiceDetailResponse(**s.model_dump()) for s in services]

    @mcp.tool()
    async def get_service_connections(args: GetServiceConnectionsInput = GetServiceConnectionsInput()) -> dict:
        client = AsyncConsulClient()
        try:
            connections = (
                await client.get_failing_connections()
                if args.failing_only else
                await client.get_service_connections()
            )

            response = ServiceConnectionResponse(connections=connections)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(response.model_dump(), indent=2)
                    }
                ]
            }

        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": (
                        f"❌ Exception: {type(e).__name__}\n"
                        f"Message: {str(e)}\n"
                        f"Traceback:\n{traceback.format_exc()}"
                    )
                    }
                ]
            }
