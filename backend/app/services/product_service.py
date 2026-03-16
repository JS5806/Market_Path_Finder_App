"""
상품 서비스 - 상품 조회, 검색, 가격 관련 비즈니스 로직
"""
from uuid import UUID
from typing import Optional

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductPrice, ProductCategory


async def get_product_by_id(db: AsyncSession, product_id: UUID) -> Optional[Product]:
    """상품 ID로 상세 조회 (가격, 카테고리 포함)"""
    stmt = (
        select(Product)
        .options(selectinload(Product.prices), selectinload(Product.category))
        .where(Product.product_id == product_id, Product.is_active == True)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_product_by_sku(db: AsyncSession, sku: str) -> Optional[Product]:
    """SKU로 상품 조회"""
    stmt = select(Product).where(Product.sku == sku, Product.is_active == True)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def search_products(
    db: AsyncSession,
    keyword: Optional[str] = None,
    category_code: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    on_sale: Optional[bool] = None,
    store_id: Optional[UUID] = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Product], int]:
    """상품 검색 (필터링 + 페이지네이션)"""
    stmt = (
        select(Product)
        .options(selectinload(Product.prices), selectinload(Product.category))
        .where(Product.is_active == True)
    )
    count_stmt = select(func.count()).select_from(Product).where(Product.is_active == True)

    # 키워드 검색
    if keyword:
        kw_filter = or_(
            Product.product_name.ilike(f"%{keyword}%"),
            Product.manufacturer.ilike(f"%{keyword}%"),
            Product.description.ilike(f"%{keyword}%"),
        )
        stmt = stmt.where(kw_filter)
        count_stmt = count_stmt.where(kw_filter)

    # 카테고리 필터
    if category_code:
        stmt = stmt.join(ProductCategory).where(ProductCategory.category_code == category_code)
        count_stmt = count_stmt.join(ProductCategory).where(ProductCategory.category_code == category_code)

    # 가격 필터 (store_id가 있을 때만)
    if store_id and (min_price is not None or max_price is not None or on_sale):
        stmt = stmt.join(ProductPrice).where(ProductPrice.store_id == store_id)
        count_stmt = count_stmt.join(ProductPrice).where(ProductPrice.store_id == store_id)

        if min_price is not None:
            price_col = func.coalesce(ProductPrice.sale_price, ProductPrice.regular_price)
            stmt = stmt.where(price_col >= min_price)
            count_stmt = count_stmt.where(price_col >= min_price)
        if max_price is not None:
            price_col = func.coalesce(ProductPrice.sale_price, ProductPrice.regular_price)
            stmt = stmt.where(price_col <= max_price)
            count_stmt = count_stmt.where(price_col <= max_price)
        if on_sale:
            stmt = stmt.where(ProductPrice.sale_price.isnot(None))
            count_stmt = count_stmt.where(ProductPrice.sale_price.isnot(None))

    # 페이지네이션
    offset = (page - 1) * size
    stmt = stmt.offset(offset).limit(size).order_by(Product.product_name)

    result = await db.execute(stmt)
    products = list(result.scalars().unique().all())

    count_result = await db.execute(count_stmt)
    total = count_result.scalar() or 0

    return products, total


async def get_categories(db: AsyncSession) -> list[ProductCategory]:
    """전체 카테고리 목록 조회"""
    stmt = select(ProductCategory).order_by(ProductCategory.depth, ProductCategory.category_name)
    result = await db.execute(stmt)
    return list(result.scalars().all())
