"""
상품 관련 Pydantic 스키마 (요청/응답)
"""
from datetime import datetime, date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ── 상품 카테고리 ──
class CategoryOut(BaseModel):
    category_id: int
    category_code: str
    category_name: str
    parent_id: Optional[int] = None
    depth: int

    model_config = {"from_attributes": True}


# ── 상품 가격 ──
class PriceOut(BaseModel):
    price_id: int
    regular_price: int
    sale_price: Optional[int] = None
    sale_end_date: Optional[date] = None

    model_config = {"from_attributes": True}


# ── 상품 기본 응답 (목록 검색용 - 가격 포함) ──
class ProductOut(BaseModel):
    product_id: UUID
    sku: str
    product_name: str
    manufacturer: Optional[str] = None
    specification: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None
    nutrition_info: Optional[dict] = None
    image_thumb_url: Optional[str] = None
    avg_rating: Optional[float] = None
    review_count: Optional[int] = 0
    is_active: bool
    # 가격 (목록에서도 바로 표시하기 위해 포함)
    regular_price: Optional[int] = None
    sale_price: Optional[int] = None
    sale_end_date: Optional[date] = None

    model_config = {"from_attributes": True}


# ── 상품 상세 응답 (가격 포함) ──
class ProductDetailOut(ProductOut):
    prices: list[PriceOut] = []
    category: Optional[CategoryOut] = None


# ── 상품 검색 요청 ──
class ProductSearchQuery(BaseModel):
    keyword: Optional[str] = Field(None, description="상품명 검색 키워드")
    category_code: Optional[str] = Field(None, description="카테고리 코드")
    min_price: Optional[int] = Field(None, ge=0)
    max_price: Optional[int] = Field(None, ge=0)
    on_sale: Optional[bool] = Field(None, description="할인 중인 상품만")
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
