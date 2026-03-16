"""
상품 마스터 + 가격/재고 + ESL ORM 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, Date, ForeignKey, Text, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    category_id = Column(Integer, primary_key=True, autoincrement=True)
    category_code = Column(String(50), unique=True, nullable=False)
    category_name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("product_categories.category_id"))
    depth = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    parent = relationship("ProductCategory", remote_side=[category_id])
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku = Column(String(50), unique=True, nullable=False)
    product_name = Column(String(200), nullable=False)
    manufacturer = Column(String(100))
    specification = Column(String(100))
    category_id = Column(Integer, ForeignKey("product_categories.category_id"))
    description = Column(Text)
    nutrition_info = Column(JSON)
    expiry_days = Column(Integer)
    image_thumb_url = Column(String(500))
    image_detail_url = Column(String(500))
    avg_rating = Column(Numeric(3, 2), default=0.00)
    review_count = Column(Integer, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("ProductCategory", back_populates="products")
    prices = relationship("ProductPrice", back_populates="product", cascade="all, delete-orphan")
    locations = relationship("ProductLocation", back_populates="product", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")


class ProductPrice(Base):
    __tablename__ = "product_prices"

    price_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    regular_price = Column(Integer, nullable=False)
    sale_price = Column(Integer)
    sale_end_date = Column(Date)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="prices")


class Inventory(Base):
    __tablename__ = "inventory"

    inventory_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    is_sold_out = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="inventory")


class ProductLocation(Base):
    __tablename__ = "product_locations"

    location_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    zone_id = Column(Integer, ForeignKey("category_zones.zone_id"))
    node_id = Column(Integer, ForeignKey("spatial_nodes.node_id"))
    shelf_info = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    product = relationship("Product", back_populates="locations")


class ProductReview(Base):
    __tablename__ = "product_reviews"

    review_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True))
    rating = Column(Integer, nullable=False)
    review_text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),
    )


class EslDevice(Base):
    __tablename__ = "esl_devices"

    esl_id = Column(Integer, primary_key=True, autoincrement=True)
    mac_address = Column(String(17), unique=True, nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"))
    battery_level = Column(Integer, default=100)
    last_sync_at = Column(DateTime(timezone=True))
    is_online = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("battery_level BETWEEN 0 AND 100", name="ck_battery_range"),
    )
