"""
AI 도구 (Tools) - AI 쇼핑 도우미가 호출할 수 있는 기능 정의
MCP 스타일 도구 인터페이스
"""
from uuid import UUID
from typing import Optional

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductPrice, ProductCategory, ProductLocation
from app.models.ai import Recipe, RecipeIngredient, ProductAssociation
from app.models.user import CartSession, CartItem


# ── 도구 정의 (MCP 형식) ──

TOOL_DEFINITIONS = [
    {
        "name": "search_product",
        "description": "상품을 이름, 카테고리, 키워드로 검색합니다.",
        "parameters": {
            "keyword": {"type": "string", "description": "검색 키워드"},
            "category_code": {"type": "string", "description": "카테고리 코드 (선택)"},
        },
    },
    {
        "name": "search_recipe",
        "description": "레시피를 이름이나 재료로 검색합니다.",
        "parameters": {
            "keyword": {"type": "string", "description": "레시피명 또는 재료명"},
        },
    },
    {
        "name": "add_to_cart",
        "description": "상품을 장바구니에 추가합니다.",
        "parameters": {
            "product_id": {"type": "string", "description": "상품 UUID"},
            "quantity": {"type": "integer", "description": "수량 (기본 1)"},
        },
    },
    {
        "name": "get_cart",
        "description": "현재 장바구니 내용을 조회합니다.",
        "parameters": {},
    },
    {
        "name": "get_price",
        "description": "상품의 가격 정보를 조회합니다.",
        "parameters": {
            "product_id": {"type": "string", "description": "상품 UUID"},
        },
    },
    {
        "name": "get_associations",
        "description": "특정 상품과 함께 자주 구매되는 연관 상품을 조회합니다.",
        "parameters": {
            "product_id": {"type": "string", "description": "상품 UUID"},
        },
    },
]


# ── 도구 실행 함수들 ──

async def execute_search_product(
    db: AsyncSession,
    keyword: str,
    store_id: Optional[UUID] = None,
    category_code: Optional[str] = None,
) -> dict:
    """상품 검색"""
    stmt = (
        select(Product)
        .options(selectinload(Product.prices), selectinload(Product.category))
        .where(Product.is_active == True)
    )

    if keyword:
        kw_filter = or_(
            Product.product_name.ilike(f"%{keyword}%"),
            Product.manufacturer.ilike(f"%{keyword}%"),
            Product.description.ilike(f"%{keyword}%"),
        )
        stmt = stmt.where(kw_filter)

    if category_code:
        stmt = stmt.join(ProductCategory).where(ProductCategory.category_code == category_code)

    stmt = stmt.limit(10)
    result = await db.execute(stmt)
    products = result.scalars().unique().all()

    # 전체 키워드 매칭 실패 시 단어별 분리 검색
    if not products and keyword:
        words = keyword.split()
        for word in words:
            if len(word) < 2:
                continue
            stmt2 = (
                select(Product)
                .options(selectinload(Product.prices), selectinload(Product.category))
                .where(
                    Product.is_active == True,
                    or_(
                        Product.product_name.ilike(f"%{word}%"),
                        Product.manufacturer.ilike(f"%{word}%"),
                        Product.description.ilike(f"%{word}%"),
                    ),
                )
                .limit(10)
            )
            result2 = await db.execute(stmt2)
            products = result2.scalars().unique().all()
            if products:
                break

    items = []
    for p in products:
        price_info = None
        if p.prices:
            # store_id에 해당하는 가격 또는 첫 번째 가격
            for pr in p.prices:
                if store_id and pr.store_id == store_id:
                    price_info = pr
                    break
            if not price_info and p.prices:
                price_info = p.prices[0]

        items.append({
            "product_id": str(p.product_id),
            "product_name": p.product_name,
            "manufacturer": p.manufacturer,
            "specification": p.specification,
            "category": p.category.category_name if p.category else None,
            "regular_price": price_info.regular_price if price_info else None,
            "sale_price": price_info.sale_price if price_info else None,
            "avg_rating": float(p.avg_rating) if p.avg_rating else None,
        })

    return {"products": items, "count": len(items)}


async def execute_search_recipe(
    db: AsyncSession,
    keyword: str,
) -> dict:
    """레시피 검색 (전체 키워드 → 단어별 분리 → 재료명 순으로 검색)"""
    # 1차: 전체 키워드로 검색
    stmt = (
        select(Recipe)
        .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.product))
        .where(
            or_(
                Recipe.recipe_name.ilike(f"%{keyword}%"),
                Recipe.description.ilike(f"%{keyword}%"),
            )
        )
        .limit(5)
    )
    result = await db.execute(stmt)
    recipes = result.scalars().unique().all()

    # 2차: 전체 매칭 실패 시 단어별로 분리하여 검색
    if not recipes:
        words = keyword.split()
        for word in words:
            if len(word) < 2:
                continue
            stmt2 = (
                select(Recipe)
                .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.product))
                .where(
                    or_(
                        Recipe.recipe_name.ilike(f"%{word}%"),
                        Recipe.description.ilike(f"%{word}%"),
                    )
                )
                .limit(5)
            )
            result2 = await db.execute(stmt2)
            recipes = result2.scalars().unique().all()
            if recipes:
                break

    # 3차: 재료명으로 검색
    if not recipes:
        for word in keyword.split():
            if len(word) < 2:
                continue
            stmt3 = (
                select(Recipe)
                .options(selectinload(Recipe.ingredients).selectinload(RecipeIngredient.product))
                .join(RecipeIngredient)
                .where(RecipeIngredient.ingredient_name.ilike(f"%{word}%"))
                .limit(5)
            )
            result3 = await db.execute(stmt3)
            recipes = result3.scalars().unique().all()
            if recipes:
                break

    items = []
    for r in recipes:
        ingredients = []
        for ing in r.ingredients:
            ingredients.append({
                "ingredient_name": ing.ingredient_name,
                "quantity_text": ing.quantity_text,
                "is_essential": ing.is_essential,
                "product_id": str(ing.product_id) if ing.product_id else None,
                "product_name": ing.product.product_name if ing.product else None,
            })

        items.append({
            "recipe_id": r.recipe_id,
            "recipe_name": r.recipe_name,
            "description": r.description,
            "difficulty": r.difficulty,
            "cooking_time_min": r.cooking_time_min,
            "servings": r.servings,
            "instructions": r.instructions,
            "ingredients": ingredients,
        })

    return {"recipes": items, "count": len(items)}


async def execute_add_to_cart(
    db: AsyncSession,
    user_id: UUID,
    product_id: UUID,
    quantity: int = 1,
) -> dict:
    """장바구니에 상품 추가"""
    # 상품 존재 확인
    prod_result = await db.execute(
        select(Product).where(Product.product_id == product_id, Product.is_active == True)
    )
    product = prod_result.scalar_one_or_none()
    if not product:
        return {"success": False, "message": "상품을 찾을 수 없습니다"}

    # 활성 세션 확보
    session_result = await db.execute(
        select(CartSession)
        .options(selectinload(CartSession.items))
        .where(CartSession.user_id == user_id, CartSession.status == "active")
    )
    session = session_result.scalar_one_or_none()

    if not session:
        session = CartSession(user_id=user_id)
        db.add(session)
        await db.flush()

    # 이미 장바구니에 있으면 수량 증가
    existing = await db.execute(
        select(CartItem).where(
            CartItem.session_id == session.session_id,
            CartItem.product_id == product_id,
        )
    )
    item = existing.scalar_one_or_none()

    if item:
        item.quantity += quantity
    else:
        item = CartItem(
            session_id=session.session_id,
            product_id=product_id,
            quantity=quantity,
            source="ai",
        )
        db.add(item)

    await db.flush()

    return {
        "success": True,
        "message": f"'{product.product_name}' {quantity}개를 장바구니에 추가했습니다",
        "product_name": product.product_name,
        "quantity": quantity,
    }


async def execute_get_cart(
    db: AsyncSession,
    user_id: UUID,
) -> dict:
    """장바구니 조회"""
    result = await db.execute(
        select(CartSession)
        .options(selectinload(CartSession.items).selectinload(CartItem.product))
        .where(CartSession.user_id == user_id, CartSession.status == "active")
    )
    session = result.scalar_one_or_none()

    if not session or not session.items:
        return {"items": [], "count": 0, "message": "장바구니가 비어있습니다"}

    items = []
    for item in session.items:
        items.append({
            "product_id": str(item.product_id),
            "product_name": item.product.product_name if item.product else "알 수 없음",
            "quantity": item.quantity,
            "source": item.source,
        })

    return {"items": items, "count": len(items)}


async def execute_get_price(
    db: AsyncSession,
    product_id: UUID,
    store_id: Optional[UUID] = None,
) -> dict:
    """가격 조회"""
    stmt = select(ProductPrice, Product).join(
        Product, ProductPrice.product_id == Product.product_id
    ).where(ProductPrice.product_id == product_id)

    if store_id:
        stmt = stmt.where(ProductPrice.store_id == store_id)

    result = await db.execute(stmt)
    rows = result.all()

    if not rows:
        return {"message": "가격 정보를 찾을 수 없습니다"}

    prices = []
    product_name = None
    for price, product in rows:
        product_name = product.product_name
        prices.append({
            "regular_price": price.regular_price,
            "sale_price": price.sale_price,
            "sale_end_date": str(price.sale_end_date) if price.sale_end_date else None,
        })

    return {
        "product_name": product_name,
        "prices": prices,
    }


async def execute_get_associations(
    db: AsyncSession,
    product_id: UUID,
) -> dict:
    """연관 상품 조회"""
    # product_a → product_b 방향
    result_a = await db.execute(
        select(ProductAssociation, Product)
        .join(Product, ProductAssociation.product_b_id == Product.product_id)
        .where(ProductAssociation.product_a_id == product_id)
        .order_by(ProductAssociation.score.desc())
        .limit(5)
    )

    # product_b → product_a 방향
    result_b = await db.execute(
        select(ProductAssociation, Product)
        .join(Product, ProductAssociation.product_a_id == Product.product_id)
        .where(ProductAssociation.product_b_id == product_id)
        .order_by(ProductAssociation.score.desc())
        .limit(5)
    )

    items = []
    for assoc, product in result_a.all():
        items.append({
            "product_id": str(product.product_id),
            "product_name": product.product_name,
            "score": float(assoc.score),
            "reason": assoc.reason,
        })
    for assoc, product in result_b.all():
        items.append({
            "product_id": str(product.product_id),
            "product_name": product.product_name,
            "score": float(assoc.score),
            "reason": assoc.reason,
        })

    # 점수순 정렬
    items.sort(key=lambda x: x["score"], reverse=True)

    return {"associations": items[:5], "count": len(items[:5])}
