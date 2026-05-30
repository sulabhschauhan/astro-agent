"""
astrologer.py
Orchestrates: query_engine → prompt_builder → GPT-4o-mini → structured response.
"""

import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.query_engine import search, multi_source_search
from agent.prompt_builder import build_prompts, DISCLAIMER, needs_disclaimer
from agent.session_manager import SessionManager
from agent.config import REWRITE_MAP
from agent.context_classifier import classify
from agent.context_bundle import ContextBundle

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
DEFAULT_N_RESULTS = 5
MAX_HISTORY_TURNS = 6  # sliding window: last 6 user+assistant pairs = 12 messages
LOW_CONFIDENCE_THRESHOLD = 0.45  # based on observed good-query range 0.57-0.60;
                                  # tune down if too many false low-confidence flags
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BASE_DELAY = 10  # seconds; doubles each retry (10, 20, 40)


def _rewrite_query(q: str) -> str:
    q_lower = q.lower()
    extras = [v for k, v in REWRITE_MAP.items() if k in q_lower]
    return f"{q} {' '.join(extras)}".strip() if extras else q


def _call_gpt(client: OpenAI, messages: list[dict]) -> str:
    """Call GPT-4o-mini with exponential backoff on rate limit."""
    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.4,
            )
            return response.choices[0].message.content
        except RateLimitError:
            if attempt == RATE_LIMIT_RETRIES - 1:
                raise
            delay = RATE_LIMIT_BASE_DELAY * (2 ** attempt)
            logger.warning(f"Rate limit — retrying in {delay}s (attempt {attempt + 1}/{RATE_LIMIT_RETRIES})")
            time.sleep(delay)


def ask(
    question: str,
    kundali_context: str | None = None,
    pdf_context: str | None = None,
    palm_left: str | None = None,
    palm_right: str | None = None,
    spouse_pdf: str | None = None,
    hand_detail: str | None = None,
    n_results: int = DEFAULT_N_RESULTS,
    multi_source: bool = False,
    introduce: bool = False,
    session: SessionManager | None = None,
    context_order: list[str] | None = None,
    **query_filters,
) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → GPT-4o-mini → structured response.

    Phase 1 gate: classify() builds a ContextBundle and makes a single GPT-4o-mini
    call to determine retrieval profile, context order, and gating. Hard-blocked
    requests return immediately with gated=True — no retrieval or inference cost.

    Args:
        question: User question (must be non-empty).
        kundali_context: Optional birth chart summary string.
        pdf_context: Optional user's AstroSage annual report text.
        palm_left: Optional left-hand palm description string.
        palm_right: Optional right-hand palm description string.
        spouse_pdf: Optional spouse's AstroSage annual report text.
        hand_detail: Optional detailed hand photograph analysis string.
        n_results: Number of chunks to retrieve (default 5).
        multi_source: If True, calls multi_source_search() — 2 chunks per book
                      across all source books — instead of a single top-n query.
        introduce: If True, Parashara introduces himself — suppressed if session
                   already has history (avoids mid-conversation re-introduction).
        session: Optional SessionManager. If provided, last MAX_HISTORY_TURNS of
                 conversation history are prepended to the GPT messages, and
                 question+answer are appended to the session on success.
        **query_filters: Passed to query_engine.search() — book_name, topic, page_type.

    Returns:
        {
            "answer":         str,        # Parashara's response (or block message if gated)
            "sources":        list[dict], # 9-field dicts from query_engine (empty if gated)
            "low_confidence": bool,       # True if top score < LOW_CONFIDENCE_THRESHOLD
            "gated":          bool,       # True if Phase 1 hard-blocked the request
            "nudges":         list[str],  # enriching-context suggestions (empty if gated)
            "model":          str,        # model used for inference (absent if gated)
        }

    Raises:
        ValueError: Empty question.
        RuntimeError: ChromaDB collection empty.
        openai.RateLimitError: All retries exhausted.
    """
    if not question.strip():
        raise ValueError("question must not be empty.")

    # Phase 1 — build ContextBundle and classify intent
    bundle = ContextBundle(
        kundali=kundali_context,
        own_pdf=pdf_context,
        spouse_pdf=spouse_pdf,
        palm_left=palm_left,
        palm_right=palm_right,
        hand_detail=hand_detail,
    )

    # Extract last Q&A pair from session for contextual carry-forward
    _last_user_q: str | None = None
    _last_assistant_answer: str | None = None
    if session:
        _recent = session.get_recent_history(n=1)
        if len(_recent) >= 2:
            _last_user_q = _recent[0]["content"]
            _last_assistant_answer = _recent[1]["content"]

    classification = classify(
        question=question,
        bundle=bundle,
        last_user_q=_last_user_q,
        last_assistant_answer=_last_assistant_answer,
    )

    if classification["hard_block"]:
        return {
            "answer":         classification["required_message"],
            "low_confidence": False,
            "sources":        [],
            "gated":          True,
        }

    # Step 1 — retrieve (rewritten query for search only; original question goes to GPT)
    search_query = _rewrite_query(question)
    query_filters.pop("context_order", None)
    if multi_source:
        sources = multi_source_search(search_query)
    else:
        sources = search(search_query, n_results=n_results, **query_filters)

    if not sources:
        return {
            "answer": (
                "I couldn't find relevant passages in my texts to answer this question. "
                "Could you rephrase or give me more context?\n\n" + DISCLAIMER
            ),
            "sources":        [],
            "low_confidence": True,
            "gated":          False,
            "model":          MODEL,
        }

    # Step 2 — assess confidence
    top_score = sources[0]["score"]
    low_confidence = top_score < LOW_CONFIDENCE_THRESHOLD

    # Suppress introduction if session already has prior turns
    effective_introduce = introduce and not (session and session.get_history())

    # Step 3 — build prompts
    prompts = build_prompts(
        question=question,
        sources=sources,
        kundali_context=kundali_context,
        pdf_context=pdf_context,
        palm_left=palm_left,
        palm_right=palm_right,
        spouse_pdf=spouse_pdf,
        hand_detail=hand_detail,
        introduce=effective_introduce,
        low_confidence=low_confidence,
        context_order=classification["context_order"],
    )

    # Step 4 — assemble messages with sliding history window
    history = session.get_recent_history(MAX_HISTORY_TURNS) if session else []
    messages = (
        [{"role": "system", "content": prompts["system"]}]
        + history
        + [{"role": "user", "content": prompts["user"]}]
    )

    # Step 5 — call GPT-4o-mini (session updated only on success)
    client = OpenAI()
    answer = _call_gpt(client, messages)
    if needs_disclaimer(answer):
        answer += "\n\n" + DISCLAIMER

    if session:
        session.add_message("user", question)
        session.add_message("assistant", answer)

    return {
        "answer":         answer,
        "sources":        sources,
        "low_confidence": low_confidence,
        "gated":          False,
        "nudges":         classification.get("nudges", []),
        "model":          MODEL,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    question = "What is the effect of Jupiter in the 7th house?"
    print(f"Question: {question}\n")

    result = ask(question, introduce=True)

    print(f"Low confidence: {result['low_confidence']} (top score: {result['sources'][0]['score'] if result['sources'] else 'n/a'})")
    print(f"Model: {result['model']}")
    print(f"Sources retrieved: {len(result['sources'])}")
    print()
    print("--- Parashara says ---")
    print(result["answer"])
