from pydantic import BaseModel, Field
from typing import Literal, Optional, List, Dict

ConnectionStatus = Literal[
    "healthy", "warning", "degraded", "failing", "blocked", "allowed", "inferred"
]

class GetServiceConnectionsInput(BaseModel):
    failing_only: Optional[bool] = False

class ServiceConnection(BaseModel):
    source: str
    destination: str
    status: str
    protocol: Optional[str] = None
    latency: Optional[int] = None
    error_rate: Optional[float] = None
    error_message: Optional[str] = None
    intentionAction: Optional[str] = None
    usesServiceMesh: Optional[bool] = False

class ServiceConnectionResponse(BaseModel):
    connections: List[ServiceConnection]

class HealthCheck(BaseModel):
    id: str
    name: str
    status: Literal["passing", "warning", "critical", "unknown"]
    output: Optional[str] = None
    notes: Optional[str] = None
    serviceId: Optional[str] = None
    serviceName: Optional[str] = None

class HealthStatus(BaseModel):
    status: Literal["passing", "warning", "critical", "unknown"]
    checks: List[HealthCheck]

class ConsulService(BaseModel):
    id: str
    name: str
    address: Optional[str]
    port: str
    node: str
    tags: List[str]
    meta: dict
    health: HealthStatus

class ServiceDetailResponse(BaseModel):
    id: str
    name: str
    address: Optional[str]
    port: str
    node: str
    tags: List[str]
    meta: dict
    health: HealthStatus
