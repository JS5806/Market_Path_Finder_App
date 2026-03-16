"""
AI 추론/추천 + 레시피 + 연관상품 ORM 모델
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Text, JSON, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    recipe_id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_name = Column(String(200), nullable=False)
    description = Column(Text)
    difficulty = Column(String(10), nullable=False, default="easy")
    cooking_time_min = Column(Integer)
    servings = Column(Integer, default=2)
    instructions = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recipe_id = Column(Integer, ForeignKey("recipes.recipe_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"))
    ingredient_name = Column(String(100), nullable=False)
    quantity_text = Column(String(50))
    is_essential = Column(Boolean, nullable=False, default=True)

    recipe = relationship("Recipe", back_populates="ingredients")
    product = relationship("Product")


class ProductAssociation(Base):
    __tablename__ = "product_associations"

    association_id = Column(Integer, primary_key=True, autoincrement=True)
    product_a_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    product_b_id = Column(UUID(as_uuid=True), ForeignKey("products.product_id"), nullable=False)
    score = Column(Numeric(5, 4), nullable=False, default=0.0)
    reason = Column(String(200))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    product_a = relationship("Product", foreign_keys=[product_a_id])
    product_b = relationship("Product", foreign_keys=[product_b_id])

    __table_args__ = (
        UniqueConstraint("product_a_id", "product_b_id", name="uq_product_pair"),
    )


class AiPrompt(Base):
    __tablename__ = "ai_prompts"

    prompt_id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_name = Column(String(100), unique=True, nullable=False)
    persona = Column(Text, nullable=False)
    tool_rules = Column(JSON)
    response_format = Column(JSON)
    version = Column(Integer, nullable=False, default=1)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AiChatLog(Base):
    __tablename__ = "ai_chat_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    session_id = Column(UUID(as_uuid=True), ForeignKey("cart_sessions.session_id"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
