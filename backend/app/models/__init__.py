"""
모든 ORM 모델을 한 곳에서 import할 수 있도록 통합
"""
from app.models.store import Store, SpatialNode, SpatialEdge, CategoryZone, CongestionData
from app.models.product import (
    ProductCategory, Product, ProductPrice, Inventory,
    ProductLocation, ProductReview, EslDevice
)
from app.models.user import User, CartSession, CartItem, ShoppingHistory
from app.models.ai import Recipe, RecipeIngredient, ProductAssociation, AiPrompt, AiChatLog
from app.models.payment import Transaction
from app.models.iot import Beacon, NfcTag, RouteResult

__all__ = [
    "Store", "SpatialNode", "SpatialEdge", "CategoryZone", "CongestionData",
    "ProductCategory", "Product", "ProductPrice", "Inventory",
    "ProductLocation", "ProductReview", "EslDevice",
    "User", "CartSession", "CartItem", "ShoppingHistory",
    "Recipe", "RecipeIngredient", "ProductAssociation", "AiPrompt", "AiChatLog",
    "Transaction",
    "Beacon", "NfcTag", "RouteResult",
]
