"""
상품 API 라우터
- 상품 검색/조회, 카테고리 목록
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.common import ApiResponse, PaginatedResponse
from app.schemas.product import ProductOut, ProductDetailOut, CategoryOut
from app.services import product_service

router = APIRouter(prefix="/products", tags=["상품"])


@router.get("", response_model=PaginatedResponse[ProductOut])
async def search_products(
    keyword: Optional[str] = Query(None, description="검색 키워드"),
    category_code: Optional[str] = Query(None, description="카테고리 코드"),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    on_sale: Optional[bool] = Query(None, description="할인 상품만"),
    store_id: Optional[UUID] = Query(None, description="매장 ID (가격 필터 시 필수)"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """상품 검색 (키워드, 카테고리, 가격 필터링)"""
    products, total = await product_service.search_products(
        db, keyword=keyword, category_code=category_code,
        min_price=min_price, max_price=max_price,
        on_sale=on_sale, store_id=store_id,
        page=page, size=size,
    )
    def product_to_out(p) -> ProductOut:
        """Product ORM → ProductOut (가격 포함)"""
        # store_id 기준으로 해당 매장 가격 먼저, 없으면 첫 번째 가격 사용
        price = None
        if p.prices:
            if store_id:
                price = next((pr for pr in p.prices if str(pr.store_id) == str(store_id)), None)
            if price is None:
                price = p.prices[0]

        data = ProductOut.model_validate(p)
        if price:
            data.regular_price = price.regular_price
            data.sale_price = price.sale_price
            data.sale_end_date = price.sale_end_date
        return data

    return PaginatedResponse(
        items=[product_to_out(p) for p in products],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size else 0,
    )


@router.get("/categories", response_model=ApiResponse[list[CategoryOut]])
async def list_categories(db: AsyncSession = Depends(get_db)):
    """전체 카테고리 목록 조회"""
    cats = await product_service.get_categories(db)
    return ApiResponse(data=[CategoryOut.model_validate(c) for c in cats])


@router.get("/{product_id}", response_model=ApiResponse[ProductDetailOut])
async def get_product_detail(product_id: UUID, db: AsyncSession = Depends(get_db)):
    """상품 상세 조회 (가격, 카테고리 포함)"""
    product = await product_service.get_product_by_id(db, product_id)
    if not product:
        return ApiResponse(success=False, message="상품을 찾을 수 없습니다", data=None)
    return ApiResponse(data=ProductDetailOut.model_validate(product))
