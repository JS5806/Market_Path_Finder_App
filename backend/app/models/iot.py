"""
IoT 장치 (Beacon, NFC, 경로 결과) ORM 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Beacon(Base):
    __tablename__ = "beacons"

    beacon_id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    uuid = Column(String(36), nullable=False)
    major = Column(Integer, nullable=False)
    minor = Column(Integer, nullable=False)
    x = Column(Numeric(8, 2), nullable=False)
    y = Column(Numeric(8, 2), nullable=False)
    floor = Column(Integer, nullable=False, default=1)
    tx_power = Column(Integer, default=-59)
    label = Column(String(100))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    from sqlalchemy.orm import relationship
    store = relationship("Store", back_populates="beacons")


class NfcTag(Base):
    __tablename__ = "nfc_tags"

    nfc_tag_id = Column(Integer, primary_key=True, autoincrement=True)
    tag_uid = Column(String(30), unique=True, nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"))
    location_desc = Column(String(200))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RouteResult(Base):
    __tablename__ = "route_results"

    route_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("cart_sessions.session_id"))
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id"), nullable=False)
    visit_order = Column(JSON, nullable=False)
    total_distance = Column(Numeric(10, 2))
    algorithm = Column(String(30), nullable=False, default="dijkstra")
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)
