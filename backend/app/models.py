from datetime import datetime, timedelta

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), default="owner")
    created_at = Column(DateTime, default=datetime.utcnow)
    api_key = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    timezone = Column(String(64), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    notification_settings = Column(JSON, nullable=True, default=dict)

    entry_points = relationship("EntryPoint", back_populates="owner")
    routes = relationship("Route", back_populates="owner")
    alerts = relationship("Alert", back_populates="user")


class EntryPoint(Base):
    __tablename__ = "entry_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    name = Column(String(120), nullable=False)
    ip = Column(String(64), nullable=False)
    ssh_port = Column(Integer, default=22)
    location = Column(String(120), nullable=False)
    wg_ip = Column(String(64), nullable=True)
    wg_pubkey = Column(String(255), nullable=True)
    status = Column(String(32), default="provisioning")
    provider = Column(String(64), nullable=True)
    specs = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="entry_points")
    stats = relationship("Stat", back_populates="entry_point", cascade="all, delete-orphan")
    ddos_logs = relationship("DDoSLog", back_populates="entry_point", cascade="all, delete-orphan")
    routes = relationship("RouteAssignment", back_populates="entry_point", cascade="all, delete-orphan")
    install_events = relationship(
        "EntryPointInstallEvent",
        back_populates="entry_point",
        order_by="EntryPointInstallEvent.created_at",
        cascade="all, delete-orphan",
    )


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    subdomain = Column(String(255), nullable=False)
    client_ip = Column(String(64), nullable=False)
    client_port = Column(Integer, nullable=False)
    protocol = Column(String(32), nullable=False, default="tcp")
    use_haproxy = Column(Boolean, default=True)
    status = Column(String(32), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    settings = Column(JSON, nullable=True)

    owner = relationship("User", back_populates="routes")
    assignments = relationship(
        "RouteAssignment",
        back_populates="route",
        cascade="all, delete-orphan",
    )


class Stat(Base):
    __tablename__ = "stats"

    id = Column(Integer, primary_key=True)
    entry_point_id = Column(Integer, ForeignKey("entry_points.id", ondelete="CASCADE"))
    cpu = Column(Integer)
    ram = Column(Integer)
    traffic_in = Column(Integer)
    traffic_out = Column(Integer)
    connections = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    entry_point = relationship("EntryPoint", back_populates="stats")


class DDoSLog(Base):
    __tablename__ = "ddos_logs"

    id = Column(Integer, primary_key=True)
    entry_point_id = Column(Integer, ForeignKey("entry_points.id", ondelete="CASCADE"))
    attack_type = Column(String(64))
    source_ip = Column(String(64))
    packets_blocked = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)

    entry_point = relationship("EntryPoint", back_populates="ddos_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(255))
    details = Column(JSON)
    ip_address = Column(String(64))
    timestamp = Column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    type = Column(String(32))
    message = Column(Text)
    read = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="alerts")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    plan = Column(String(64), default="free")
    limits = Column(JSON)
    expires_at = Column(DateTime, nullable=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=1))


class EntryPointInstallEvent(Base):
    __tablename__ = "entry_point_install_events"

    id = Column(Integer, primary_key=True)
    entry_point_id = Column(Integer, ForeignKey("entry_points.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    entry_point = relationship("EntryPoint", back_populates="install_events")


class RouteAssignment(Base):
    __tablename__ = "route_assignments"
    __table_args__ = (
        UniqueConstraint("route_id", "entry_point_id", name="uix_route_entry_point"),
    )

    id = Column(Integer, primary_key=True)
    route_id = Column(Integer, ForeignKey("routes.id", ondelete="CASCADE"), nullable=False)
    entry_point_id = Column(Integer, ForeignKey("entry_points.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Integer, default=1)

    route = relationship("Route", back_populates="assignments")
    entry_point = relationship("EntryPoint", back_populates="routes")
