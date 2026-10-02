"""Generic AI service for AgriNova Agriculture Assistant.

Acts as the single entrypoint for Django views, manages RAG context retrieval,
formats agricultural system prompts, and orchestrates Gemini primary with Groq fallback.
"""

import logging
from typing import Any, Dict, List, Optional

from .fallback_service import FallbackService
from .rag_service import RAGService

from forecasting.models import PriceRecord
from marketplace.models import CropCategory
from agrinova.constants import TAMIL_NADU_DISTRICTS

logger = logging.getLogger(__name__)

AGRICULTURE_SYSTEM_PROMPT = """You are AgriNova Assistant, an AI helper for a Tamil Nadu agriculture marketplace.

Your scope is strictly limited to:
- Farming guidance and best practices
- Crop information (especially Tamil Nadu crops like rice, tomato, potato, cotton, pulses)
- Fertilizer and soil recommendations
- Pest and disease management basics
- How to use the AgriNova marketplace (listing crops, buying, orders, dashboard)

Politely decline unrelated topics (politics, entertainment, coding, etc.) and redirect to agriculture or marketplace help.

Keep responses concise, practical, and friendly. Use simple English suitable for farmers and buyers."""


def build_system_instruction(context: Optional[str] = None) -> str:
    """
    Build the system prompt with ground-truth agricultural knowledge from RAG.
    """
    if not context or not context.strip():
        return AGRICULTURE_SYSTEM_PROMPT

    return (
        f"{AGRICULTURE_SYSTEM_PROMPT}\n\n"
        f"### GROUND TRUTH AGRICULTURE KNOWLEDGE BASE:\n"
        f"{context.strip()}\n\n"
        f"### INSTRUCTIONS FOR USING KNOWLEDGE BASE:\n"
        f"1. Prioritize the above retrieved agriculture context for crop, soil, fertilizer, disease, and farming facts.\n"
        f"2. Synthesize a natural, clear, and farmer-friendly answer rather than copying raw text.\n"
        f"3. Do not invent unsupported agricultural facts or dosages.\n"
        f"4. If the retrieved context does not contain enough specific information for a regional query, state clearly and suggest consulting a local Krishi Vigyan Kendra (KVK) or extension officer."
    )
def get_market_price_context(question: str) -> Optional[str]:
    """
    Find the latest available market price when the user
    asks about a crop price in a Tamil Nadu district.
    """

    question_lower = question.lower()

    # Find the crop mentioned in the user's question
    crop = None

    for item in CropCategory.objects.all():
        if item.name.lower() in question_lower:
            crop = item
            break

    if crop is None:
        return None

    # Find the district mentioned in the user's question
    district = None

    for district_value, district_label in TAMIL_NADU_DISTRICTS:
        if (
            district_value.lower() in question_lower
            or district_label.lower() in question_lower
        ):
            district = district_value
            break

    if district is None:
        return None

    # Get the latest available price from the database
    latest_record = (
        PriceRecord.objects
        .filter(
            crop=crop,
            district=district
        )
        .order_by("-date", "-id")
        .first()
    )

    if latest_record is None:
        return None

    data_type = (
        "Simulated/Demo Data"
        if latest_record.is_synthetic
        else "Market Data"
    )

    return (
        "### LATEST MARKET PRICE DATA\n"
        f"Crop: {crop.name}\n"
        f"District: {district}\n"
        f"Latest available price: ₹{latest_record.price}\n"
        f"Price date: {latest_record.date.strftime('%d %B %Y')}\n"
        f"Data type: {data_type}\n\n"
        "IMPORTANT: Use this database price and date when "
        "answering the user's market-price question. "
        "Do not invent a different price or date."
    )


def generate_response(
    question: str,
    context: Optional[str] = None,
    chat_history: Optional[List[Dict[str, str]]] = None,
    fallback_service: Optional[FallbackService] = None,
    rag_service: Optional[RAGService] = None,
    use_rag: bool = True,
) -> Dict[str, Any]:
    """
    Generate an AI response for a user's question with RAG retrieval and Gemini/Groq fallback.

    Args:
        question: The user's input question / prompt.
        context: Explicit context override (if provided, skips internal RAG retrieval).
        chat_history: List of previous conversation turns [{'role': 'user'|'assistant', 'content': '...'}].
        fallback_service: Optional FallbackService instance (for testing/dependency injection).
        rag_service: Optional RAGService instance (for testing/dependency injection).
        use_rag: Whether to perform RAG retrieval if context is not explicitly passed (default: True).

    Returns:
        dict: {
            'success': bool,
            'response': str,
            'provider': Optional[str],
            'response_time_ms': int,
            'error': Optional[str],
            'sources': Optional[List[str]],
        }
    """
    rag_sources = []
    rag_context = context

    # 1. RAG Retrieval if enabled and context not already provided
    if use_rag and rag_context is None:
        try:
            r_service = rag_service or RAGService()
            rag_result = r_service.retrieve_context(question=question)
            if rag_result.get('found') and rag_result.get('context'):
                rag_context = rag_result['context']
                rag_sources = rag_result.get('sources', [])
                logger.info("RAG context injected for question: '%s' (%d sources)", question[:50], len(rag_sources))
        except Exception as exc:
            logger.warning("RAG retrieval failed, proceeding without RAG context: %s", exc)
    # 2. Add latest database market price when relevant
    market_context = get_market_price_context(question)

    if market_context:
        if rag_context:
            rag_context = f"{market_context}\n\n{rag_context}"
        else:
            rag_context = market_context

    # 3. Build system instruction with context
    system_instruction = build_system_instruction(context=rag_context)
   
    # 4. Execute via Fallback Service (Gemini primary -> Groq fallback)
    service = fallback_service or FallbackService()
    result = service.execute(
        user_query=question,
        chat_history=chat_history or [],
        system_instruction=system_instruction,
    )

    # Attach RAG sources to response metadata
    result['sources'] = rag_sources
    return result
