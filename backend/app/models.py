from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    entry_points = relationship("EntryPoint", back_populates="owner", cascade="all, delete-orphan")
    routes = relationship("Route", back_populates="owner", cascade="all, delete-orphan")


class EntryPoint(Base):
    __tablename__ = "entry_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(120), nullable=False)
    ip = Column(String(64), nullable=False)
    ssh_port = Column(Integer, nullable=False, default=22)
    location = Column(String(120), nullable=False)
    status = Column(String(32), nullable=False, default="online")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="entry_points")
    routes = relationship("RouteAssignment", back_populates="entry_point", cascade="all, delete-orphan")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subdomain = Column(String(255), nullable=False)
    client_ip = Column(String(64), nullable=False)
    client_port = Column(Integer, nullable=False)
    protocol = Column(String(16), nullable=False, default="tcp")
    use_haproxy = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="routes")
    assignments = relationship("RouteAssignment", back_populates="route", cascade="all, delete-orphan")


class RouteAssignment(Base):
    __tablename__ = "route_assignments"
    __table_args__ = (
        UniqueConstraint("route_id", "entry_point_id", name="uix_route_entry_point"),
    )

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    entry_point_id = Column(Integer, ForeignKey("entry_points.id", ondelete="CASCADE"), nullable=False)

    route = relationship("Route", back_populates="assignments")
    entry_point = relationship("EntryPoint", back_populates="routes")
