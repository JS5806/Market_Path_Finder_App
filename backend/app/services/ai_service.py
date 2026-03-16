"""
AI 쇼핑 도우미 서비스
- Local LLM 연동 (LangChain)
- LLM 미사용 시 규칙 기반 fallback
- 도구 실행 및 대화 로그 저장
"""
import logging
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai import AiPrompt, AiChatLog
from app.services import ai_tools

logger = logging.getLogger(__name__)


# ── LLM 클라이언트 (Lazy init) ──

_llm_client = None


def _get_llm_client():
    """LangChain LLM 클라이언트를 가져옵니다 (최초 1회 초기화)"""
    global _llm_client
    if _llm_client is not None:
        return _llm_client

    try:
        from langchain_community.llms import VLLMOpenAI
        _llm_client = VLLMOpenAI(
            openai_api_base=settings.LLM_API_BASE,
            model_name=settings.LLM_MODEL_NAME,
            max_tokens=1024,
            temperature=0.7,
            timeout=30,
        )
        logger.info(f"LLM client initialized: {settings.LLM_API_BASE}")
        return _llm_client
    except Exception as e:
        logger.warning(f"LLM client init failed (fallback mode): {e}")
        return None


# ── 의도 분석 (규칙 기반 fallback) ──

def _extract_keyword(message: str) -> str:
    """
    사용자 메시지에서 불필요한 조사/동사/명령어를 제거하고 핵심 키워드를 추출합니다.
    """
    noise_words = [
        "추천해줘", "추천해", "알려줘", "알려", "보여줘", "보여",
        "찾아줘", "찾아", "검색해줘", "검색해", "해줘", "해",
        "있어", "있나", "어디", "뭐", "좀", "주세요", "줘",
        "만들고 싶어", "하고 싶어", "먹고 싶어",
        "레시피", "요리법", "만드는 법", "조리법",
        "가격", "얼마", "할인", "세일",
        "담아줘", "담아", "넣어줘", "넣어", "추가해줘", "추가해",
        "장바구니에", "카트에",
        "뭐 같이", "함께", "어울리는", "곁들일",
    ]
    cleaned = message.strip()
    for nw in noise_words:
        cleaned = cleaned.replace(nw, "")
    # 공백 정리
    cleaned = " ".join(cleaned.split()).strip()
    return cleaned if cleaned else message.strip()


def analyze_intent(message: str) -> dict:
    """
    사용자 메시지에서 의도를 분석합니다.

    Returns:
        {"intent": str, "entities": dict}
    """
    msg = message.lower().strip()

    # 레시피 관련
    recipe_keywords = ["레시피", "만들", "요리", "조리", "끓이", "구이", "볶음", "찌개", "국", "파티"]
    for kw in recipe_keywords:
        if kw in msg:
            keyword = _extract_keyword(message)
            return {"intent": "search_recipe", "entities": {"keyword": keyword}}

    # 장바구니 조회
    cart_view_keywords = ["장바구니", "카트", "담은 것", "뭐 담", "뭐 넣"]
    for kw in cart_view_keywords:
        if kw in msg:
            return {"intent": "get_cart", "entities": {}}

    # 추천 / 연관 상품
    recommend_keywords = ["추천", "뭐 더", "함께", "같이", "어울리", "곁들"]
    for kw in recommend_keywords:
        if kw in msg:
            keyword = _extract_keyword(message)
            return {"intent": "get_associations", "entities": {"keyword": keyword}}

    # 가격 조회
    price_keywords = ["가격", "얼마", "비용", "원", "할인", "세일"]
    for kw in price_keywords:
        if kw in msg:
            keyword = _extract_keyword(message)
            return {"intent": "get_price", "entities": {"keyword": keyword}}

    # 상품 검색 (기본)
    search_keywords = ["찾아", "검색", "있어", "어디", "사고 싶", "구매", "사려고"]
    for kw in search_keywords:
        if kw in msg:
            keyword = _extract_keyword(message)
            return {"intent": "search_product", "entities": {"keyword": keyword}}

    # 장바구니 추가 의도
    add_keywords = ["담아", "넣어", "추가", "장바구니에", "카트에"]
    for kw in add_keywords:
        if kw in msg:
            keyword = _extract_keyword(message)
            return {"intent": "add_to_cart", "entities": {"keyword": keyword}}

    # 인사 / 일반
    greet_keywords = ["안녕", "하이", "헬로", "도와", "도움"]
    for kw in greet_keywords:
        if kw in msg:
            return {"intent": "greeting", "entities": {}}

    # 기본: 상품 검색으로 fallback
    return {"intent": "search_product", "entities": {"keyword": message}}


# ── 메인 채팅 처리 ──

async def process_chat(
    db: AsyncSession,
    user_id: UUID,
    message: str,
    store_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
) -> dict:
    """
    사용자 메시지를 처리하고 AI 응답을 생성합니다.

    1. 사용자 메시지 로그 저장
    2. 의도 분석
    3. 도구 실행
    4. 응답 생성 (LLM 또는 규칙 기반)
    5. AI 응답 로그 저장
    """
    # 1. 사용자 메시지 로그 저장
    user_log = AiChatLog(
        user_id=user_id,
        session_id=session_id,
        role="user",
        content=message,
    )
    db.add(user_log)
    await db.flush()

    # 2. 의도 분석
    intent_result = analyze_intent(message)
    intent = intent_result["intent"]
    entities = intent_result["entities"]

    # 3. 도구 실행 + 응답 생성
    tool_calls = []
    recommendations = []
    cart_updates = []
    response_message = ""

    if intent == "greeting":
        response_message = (
            "안녕하세요! 스마트마트 쇼핑 도우미입니다. "
            "상품 검색, 레시피 추천, 장바구니 관리를 도와드릴게요. "
            "무엇을 도와드릴까요?"
        )

    elif intent == "search_recipe":
        keyword = entities.get("keyword", message)
        result = await ai_tools.execute_search_recipe(db, keyword)
        tool_calls.append({
            "tool_name": "search_recipe",
            "arguments": {"keyword": keyword},
            "result": result,
        })

        if result["recipes"]:
            recipe = result["recipes"][0]
            ingredients_text = ", ".join(
                f"{ing['ingredient_name']}({ing['quantity_text']})"
                for ing in recipe["ingredients"]
            )
            response_message = (
                f"'{recipe['recipe_name']}' 레시피를 찾았어요!\n\n"
                f"난이도: {recipe['difficulty']} | "
                f"조리시간: {recipe['cooking_time_min']}분 | "
                f"인분: {recipe['servings']}인분\n\n"
                f"필요한 재료: {ingredients_text}\n\n"
                f"재료를 장바구니에 추가할까요? '재료 담아줘'라고 말씀해주세요!"
            )

            # 매칭 가능한 상품을 추천 목록에 추가
            for ing in recipe["ingredients"]:
                if ing["product_id"]:
                    recommendations.append({
                        "product_id": ing["product_id"],
                        "product_name": ing["product_name"] or ing["ingredient_name"],
                        "reason": f"{recipe['recipe_name']} 재료",
                    })
        else:
            response_message = f"'{keyword}'와 관련된 레시피를 찾지 못했어요. 다른 키워드로 검색해보시겠어요?"

    elif intent == "search_product":
        keyword = entities.get("keyword", message)
        result = await ai_tools.execute_search_product(db, keyword, store_id)
        tool_calls.append({
            "tool_name": "search_product",
            "arguments": {"keyword": keyword},
            "result": result,
        })

        if result["products"]:
            products_text = "\n".join(
                f"• {p['product_name']} ({p['specification'] or ''}) - "
                f"{'할인가 ' + format(p['sale_price'], ',') + '원' if p['sale_price'] else format(p['regular_price'], ',') + '원' if p['regular_price'] else '가격정보 없음'}"
                for p in result["products"][:5]
            )
            response_message = f"검색 결과 {result['count']}개 상품을 찾았어요:\n\n{products_text}\n\n장바구니에 추가하시겠어요?"

            for p in result["products"][:5]:
                recommendations.append({
                    "product_id": p["product_id"],
                    "product_name": p["product_name"],
                    "reason": "검색 결과",
                    "price": p["regular_price"],
                    "sale_price": p["sale_price"],
                })
        else:
            response_message = f"'{keyword}'와 관련된 상품을 찾지 못했어요. 다른 키워드로 검색해보시겠어요?"

    elif intent == "add_to_cart":
        # 가장 최근 검색/추천 상품을 장바구니에 추가
        # 먼저 키워드로 상품 검색
        keyword = entities.get("keyword", message)
        search_result = await ai_tools.execute_search_product(db, keyword, store_id)

        if search_result["products"]:
            added_items = []
            for p in search_result["products"][:3]:
                add_result = await ai_tools.execute_add_to_cart(
                    db, user_id, UUID(p["product_id"]), 1
                )
                tool_calls.append({
                    "tool_name": "add_to_cart",
                    "arguments": {"product_id": p["product_id"], "quantity": 1},
                    "result": add_result,
                })
                if add_result["success"]:
                    added_items.append(add_result["product_name"])
                    cart_updates.append({
                        "action": "add",
                        "product_id": p["product_id"],
                        "product_name": add_result["product_name"],
                        "quantity": 1,
                    })

            if added_items:
                response_message = f"장바구니에 추가했어요: {', '.join(added_items)}"
            else:
                response_message = "상품을 장바구니에 추가하지 못했어요."
        else:
            response_message = "추가할 상품을 찾지 못했어요. 상품명을 다시 말씀해주세요."

    elif intent == "get_cart":
        result = await ai_tools.execute_get_cart(db, user_id)
        tool_calls.append({
            "tool_name": "get_cart",
            "arguments": {},
            "result": result,
        })

        if result["items"]:
            items_text = "\n".join(
                f"• {item['product_name']} x{item['quantity']}"
                for item in result["items"]
            )
            response_message = f"현재 장바구니에 {result['count']}개 상품이 있어요:\n\n{items_text}"
        else:
            response_message = "장바구니가 비어있어요. 상품을 검색해서 추가해보세요!"

    elif intent == "get_price":
        keyword = entities.get("keyword", message)
        # 먼저 상품 검색
        search_result = await ai_tools.execute_search_product(db, keyword, store_id)

        if search_result["products"]:
            p = search_result["products"][0]
            price_result = await ai_tools.execute_get_price(
                db, UUID(p["product_id"]), store_id
            )
            tool_calls.append({
                "tool_name": "get_price",
                "arguments": {"product_id": p["product_id"]},
                "result": price_result,
            })

            if price_result.get("prices"):
                pr = price_result["prices"][0]
                if pr["sale_price"]:
                    response_message = (
                        f"'{p['product_name']}'의 가격:\n"
                        f"정가: {format(pr['regular_price'], ',')}원\n"
                        f"할인가: {format(pr['sale_price'], ',')}원 "
                        f"(~{pr['sale_end_date']}까지)"
                    )
                else:
                    response_message = f"'{p['product_name']}'의 가격: {format(pr['regular_price'], ',')}원"
            else:
                response_message = f"'{p['product_name']}'의 가격 정보를 찾지 못했어요."
        else:
            response_message = "해당 상품을 찾지 못했어요."

    elif intent == "get_associations":
        keyword = entities.get("keyword", message)
        search_result = await ai_tools.execute_search_product(db, keyword, store_id)

        if search_result["products"]:
            p = search_result["products"][0]
            assoc_result = await ai_tools.execute_get_associations(
                db, UUID(p["product_id"])
            )
            tool_calls.append({
                "tool_name": "get_associations",
                "arguments": {"product_id": p["product_id"]},
                "result": assoc_result,
            })

            if assoc_result["associations"]:
                assoc_text = "\n".join(
                    f"• {a['product_name']} - {a['reason']}"
                    for a in assoc_result["associations"]
                )
                response_message = (
                    f"'{p['product_name']}'와 함께 자주 구매하는 상품:\n\n{assoc_text}"
                )
                for a in assoc_result["associations"]:
                    recommendations.append({
                        "product_id": a["product_id"],
                        "product_name": a["product_name"],
                        "reason": a["reason"],
                    })
            else:
                response_message = f"'{p['product_name']}'의 연관 상품 정보가 아직 없어요."
        else:
            response_message = "해당 상품을 찾지 못했어요."

    # 4. LLM 보정 시도 (연결 가능 시)
    llm = _get_llm_client()
    if llm and intent != "greeting":
        try:
            # 시스템 프롬프트 로드
            prompt_result = await db.execute(
                select(AiPrompt).where(
                    AiPrompt.prompt_name == "shopping_assistant",
                    AiPrompt.is_active == True,
                )
            )
            ai_prompt = prompt_result.scalar_one_or_none()
            system_persona = ai_prompt.persona if ai_prompt else "당신은 마트 쇼핑 도우미 AI입니다."

            # LLM으로 응답 보정
            llm_prompt = (
                f"{system_persona}\n\n"
                f"사용자 질문: {message}\n"
                f"도구 실행 결과: {response_message}\n\n"
                f"위 정보를 바탕으로 친절하고 간결하게 한국어로 응답해주세요:"
            )
            llm_response = await _call_llm_async(llm, llm_prompt)
            if llm_response:
                response_message = llm_response
        except Exception as e:
            logger.debug(f"LLM enhancement skipped: {e}")

    # 5. AI 응답 로그 저장
    ai_log = AiChatLog(
        user_id=user_id,
        session_id=session_id,
        role="assistant",
        content=response_message,
        tool_calls=[tc for tc in tool_calls] if tool_calls else None,
    )
    db.add(ai_log)
    await db.flush()

    return {
        "message": response_message,
        "recommendations": recommendations,
        "cart_updates": cart_updates,
        "tool_calls": tool_calls,
        "session_id": session_id,
    }


async def _call_llm_async(llm, prompt: str) -> Optional[str]:
    """LLM 비동기 호출 (타임아웃 포함)"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, llm.invoke, prompt),
            timeout=15.0,
        )
        return result.strip() if result else None
    except Exception:
        return None


async def get_chat_history(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 20,
) -> list[dict]:
    """채팅 히스토리 조회"""
    result = await db.execute(
        select(AiChatLog)
        .where(AiChatLog.user_id == user_id)
        .order_by(AiChatLog.created_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()

    return [
        {
            "log_id": log.log_id,
            "role": log.role,
            "content": log.content,
            "tool_calls": log.tool_calls,
            "created_at": log.created_at,
        }
        for log in reversed(logs)
    ]
