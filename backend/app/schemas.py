from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: int
    exp: int


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        orm_mode = True


class EntryPointBase(BaseModel):
    name: str
    ip: str
    ssh_port: int = 22
    location: str
    wg_ip: Optional[str]
    provider: Optional[str]
    specs: Optional[dict[str, Any]]


class EntryPointCreate(EntryPointBase):
    ssh_method: str = "password"
    ssh_secret: Optional[str]
    wireguard_port: int = 51820
    bandwidth_limit: Optional[float]
    firewall_rules: Optional[str]
    backups: Optional[str]


class EntryPointOut(EntryPointBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class RouteBase(BaseModel):
    subdomain: str
    client_ip: str
    client_port: int
    protocol: str
    use_haproxy: bool = True
    settings: Optional[dict[str, Any]]


class RouteCreate(RouteBase):
    ddos_level: str = "high"
    rate_limit: Optional[int]
    entry_points: list[int] | None = None


class RouteOut(RouteBase):
    id: int
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class StatOut(BaseModel):
    entry_point_id: int
    cpu: int
    ram: int
    traffic_in: int
    traffic_out: int
    connections: int
    timestamp: datetime

    class Config:
        orm_mode = True


class AlertOut(BaseModel):
    id: int
    type: str
    message: str
    read: bool
    timestamp: datetime

    class Config:
        orm_mode = True


class SubscriptionOut(BaseModel):
    plan: str
    limits: dict[str, Any] | None
    expires_at: Optional[datetime]


class AuditLogOut(BaseModel):
    action: str
    details: dict[str, Any] | None
    ip_address: str | None
    timestamp: datetime

    class Config:
        orm_mode = True
