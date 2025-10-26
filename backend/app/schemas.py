from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    access_token: str
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
    created_at: datetime

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EntryPointBase(BaseModel):
    name: str
    ip: str
    ssh_port: int = Field(22, ge=1, le=65535)
    location: str
    status: str = "online"


class EntryPointCreate(EntryPointBase):
    pass


class EntryPointUpdate(BaseModel):
    name: Optional[str]
    ip: Optional[str]
    ssh_port: Optional[int]
    location: Optional[str]
    status: Optional[str]


class EntryPointOut(EntryPointBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class RouteBase(BaseModel):
    subdomain: str
    client_ip: str
    client_port: int = Field(..., ge=1, le=65535)
    protocol: str = Field("tcp", regex="^(tcp|udp|tcp\+udp)$", description="Allowed protocols")
    use_haproxy: bool = True


class RouteCreate(RouteBase):
    entry_points: List[int] = Field(default_factory=list)


class RouteOut(RouteBase):
    id: int
    created_at: datetime
    entry_points: List[int] = Field(default_factory=list)

    class Config:
        orm_mode = True
