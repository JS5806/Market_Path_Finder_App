"""
마트 및 공간 데이터 ORM 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, JSON, Time, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Store(Base):
    __tablename__ = "stores"

    store_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    store_name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    open_time = Column(Time, nullable=False, server_default="09:00")
    close_time = Column(Time, nullable=False, server_default="22:00")
    floor_count = Column(Integer, nullable=False, default=1)
    floor_info = Column(JSON)
    width_meters = Column(Numeric(8, 2))
    height_meters = Column(Numeric(8, 2))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    nodes = relationship("SpatialNode", back_populates="store", cascade="all, delete-orphan")
    edges = relationship("SpatialEdge", back_populates="store", cascade="all, delete-orphan")
    zones = relationship("CategoryZone", back_populates="store", cascade="all, delete-orphan")
    beacons = relationship("Beacon", back_populates="store", cascade="all, delete-orphan")


class SpatialNode(Base):
    __tablename__ = "spatial_nodes"

    node_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    x = Column(Numeric(8, 2), nullable=False)
    y = Column(Numeric(8, 2), nullable=False)
    floor = Column(Integer, nullable=False, default=1)
    node_type = Column(String(30), nullable=False, default="waypoint")
    label = Column(String(100))
    is_obstacle = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    store = relationship("Store", back_populates="nodes")


class SpatialEdge(Base):
    __tablename__ = "spatial_edges"

    edge_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    from_node_id = Column(Integer, ForeignKey("spatial_nodes.node_id", ondelete="CASCADE"), nullable=False)
    to_node_id = Column(Integer, ForeignKey("spatial_nodes.node_id", ondelete="CASCADE"), nullable=False)
    distance = Column(Numeric(8, 2), nullable=False)
    weight = Column(Numeric(8, 2))
    is_bidirectional = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    store = relationship("Store", back_populates="edges")
    from_node = relationship("SpatialNode", foreign_keys=[from_node_id])
    to_node = relationship("SpatialNode", foreign_keys=[to_node_id])


class CategoryZone(Base):
    __tablename__ = "category_zones"

    zone_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    zone_name = Column(String(100), nullable=False)
    category_code = Column(String(50), nullable=False)
    x_start = Column(Numeric(8, 2), nullable=False)
    y_start = Column(Numeric(8, 2), nullable=False)
    x_end = Column(Numeric(8, 2), nullable=False)
    y_end = Column(Numeric(8, 2), nullable=False)
    floor = Column(Integer, nullable=False, default=1)
    node_id = Column(Integer, ForeignKey("spatial_nodes.node_id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    store = relationship("Store", back_populates="zones")


class CongestionData(Base):
    __tablename__ = "congestion_data"

    congestion_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(Integer, ForeignKey("category_zones.zone_id"))
    density_level = Column(Integer, nullable=False, default=1)
    measured_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("density_level BETWEEN 1 AND 5", name="ck_density_range"),
    )
