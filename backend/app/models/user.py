"""
사용자, 장바구니, 쇼핑 히스토리 ORM 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, ForeignKey, JSON, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    user_name = Column(String(50), nullable=False)
    role = Column(String(20), nullable=False, default="customer")  # admin, manager, customer
    age_group = Column(String(10))
    preferred_categories = Column(JSON)
    preferred_store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id"))
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    cart_sessions = relationship("CartSession", back_populates="user", cascade="all, delete-orphan")
    shopping_history = relationship("ShoppingHistory", back_populates="user", cascade="all, delete-orphan")


class CartSession(Base):
    __tablename__ = "cart_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id"))
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cart_sessions")
    items = relationship("CartItem", back_populates="session", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("cart_sessions.session_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    added_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    source = Column(String(20), nullable=False, default="manual")
    is_collected = Column(Boolean, nullable=False, default=False)

    session = relationship("CartSession", back_populates="items")
    product = relationship("Product")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_cart_quantity"),
    )


class ShoppingHistory(Base):
    __tablename__ = "shopping_history"

    history_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.store_id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("cart_sessions.session_id"))
    total_amount = Column(Integer, nullable=False, default=0)
    item_count = Column(Integer, nullable=False, default=0)
    shopped_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="shopping_history")
