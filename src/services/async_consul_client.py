import os
from typing import Optional

import httpx

from src.services.consul_client_util import enhance_connection_with_metrics
from src.tools.models import ServiceConnection, ConsulService, HealthStatus, HealthCheck


class AsyncConsulClient:
    def __init__(self):
        self.host = os.getenv("CONSUL_HOST", "localhost")
        self.port = int(os.getenv("CONSUL_PORT", 8500))
        self.scheme = os.getenv("CONSUL_SCHEME", "http")
        self.token = os.getenv("CONSUL_HTTP_TOKEN")
        self.base_url = f"{self.scheme}://{self.host}:{self.port}"
        self.headers = {"X-Consul-Token": self.token} if self.token else {}
        self.timeout = float(os.getenv("CONSUL_HTTP_TIMEOUT", 5.0))

    def get_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=self.timeout,
        )

    async def is_healthy(self) -> bool:
        try:
            async with self.get_client() as client:
                res = await client.get("/v1/status/leader")
                return res.status_code == 200 and res.text.strip() != '""'
        except Exception as e:
            print(f"Consul health check failed: {e}")
            return False

    async def get_services(self) -> Optional[dict[str, list[str]]]:
        try:
            async with self.get_client() as client:
                res = await client.get("/v1/catalog/services")
                return res.json() if res.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching services: {e}")
            return None

    async def get_service_health(self, service_name: str) -> Optional[list[dict]]:
        try:
            async with self.get_client() as client:
                res = await client.get(f"/v1/health/service/{service_name}")
                return res.json() if res.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching health for service {service_name}: {e}")
            return None

    async def get_service_health_by_id(self, service_id: str) -> HealthStatus:
        try:
            async with self.get_client() as client:
                res = await client.get("/v1/agent/checks")
                if res.status_code != 200:
                    return HealthStatus(status="unknown", checks=[])

                checks = res.json()
                service_checks = []
                overall_status = "passing"

                for check in checks.values():
                    if check.get("ServiceID") == service_id:
                        status = check.get("Status", "unknown")
                        service_checks.append(
                            HealthCheck(
                                id=check.get("CheckID"),
                                name=check.get("Name"),
                                status=status,
                                output=check.get("Output"),
                                notes=check.get("Notes"),
                                serviceId=check.get("ServiceID"),
                                serviceName=check.get("ServiceName")
                            )
                        )
                        if status == "critical":
                            overall_status = "critical"
                        elif status == "warning" and overall_status != "critical":
                            overall_status = "warning"

                return HealthStatus(status=overall_status, checks=service_checks)
        except Exception as e:
            print(f"Error fetching service health for {service_id}: {e}")
            return HealthStatus(status="unknown", checks=[])

    async def get_services_detailed(self) -> list[ConsulService]:
        try:
            async with self.get_client() as client:
                res = await client.get("/v1/catalog/services")
                if res.status_code != 200:
                    return []

                services = []
                names = res.json()
                for name in names:
                    if name == "consul":
                        continue
                    detail_res = await client.get(f"/v1/catalog/service/{name}")
                    if detail_res.status_code == 200:
                        for service in detail_res.json():
                            health = await self.get_service_health_by_id(service.get("ServiceID"))
                            services.append(
                                ConsulService(
                                    id=service.get("ServiceID"),
                                    name=service.get("ServiceName"),
                                    address=service.get("ServiceAddress") or service.get("Address"),
                                    port=str(service.get("ServicePort")),
                                    node=service.get("Node"),
                                    tags=service.get("ServiceTags") or [],
                                    meta=service.get("ServiceMeta") or {},
                                    health=health
                                )
                            )
                return services
        except Exception as e:
            print(f"Error fetching detailed services: {e}")
            return []

    async def get_service_connections(self) -> list[ServiceConnection]:
        try:
            async with self.get_client() as client:
                connections = []

                # 1. Try Connect intentions
                try:
                    res = await client.get("/v1/connect/intentions")
                    if res.status_code == 200 and isinstance(res.json(), list):
                        for intention in res.json():
                            connections.append(
                                ServiceConnection(
                                    source=intention.get("SourceName"),
                                    destination=intention.get("DestinationName"),
                                    status="allowed" if intention.get("Action") == "allow" else "blocked",
                                    intentionAction=intention.get("Action"),
                                    protocol="tcp",
                                    usesServiceMesh=True
                                )
                            )
                except Exception as e:
                    print(f"Connect intentions failed, fallback: {e}")

                # 2. Fallback to inference
                if not connections:
                    services = await self.get_services_detailed()
                    for source in services:
                        meta = source.meta or {}
                        upstreams = meta.get("upstream_services", "")
                        upstream_list = [s.strip() for s in upstreams.split(",") if s.strip()]

                        for upstream_name in upstream_list:
                            targets = [s for s in services if s.name == upstream_name]
                            for target in targets:
                                connections.append(
                                    ServiceConnection(
                                        source=source.name,
                                        destination=target.name,
                                        status="inferred",
                                        protocol=meta.get("protocol", "http"),
                                        usesServiceMesh=False
                                    )
                                )

                        for target in services:
                            if source.id == target.id:
                                continue
                            if (
                                ("api" in source.name and "service" in target.name) or
                                ("web" in source.name and "api" in target.name) or
                                ("service" in source.name and "db" in target.name) or
                                ("frontend" in source.name and "api" in target.name) or
                                ("api" in source.name and "auth" in target.name) or
                                ("api" in source.name and "payment" in target.name)
                            ):
                                connection = ServiceConnection(
                                    source=source.name,
                                    destination=target.name,
                                    status="inferred",
                                    protocol="http",
                                    usesServiceMesh=False
                                )
                                enhanced = enhance_connection_with_metrics(connection.model_dump())
                                connections.append(ServiceConnection(**enhanced))

                return connections

        except Exception as e:
            print(f"Error in get_service_connections: {e}")
            return []

    async def get_failing_connections(self) -> list[ServiceConnection]:
        try:
            connections = await self.get_service_connections()
            return [conn for conn in connections if conn.status in {"blocked", "failing", "degraded"}]
        except Exception as e:
            print(f"Error in get_failing_connections: {e}")
            return []
