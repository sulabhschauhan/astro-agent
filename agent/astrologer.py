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
from ingestion.query_engine import search
from agent.prompt_builder import build_prompts, DISCLAIMER
from agent.session_manager import SessionManager

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
DEFAULT_N_RESULTS = 5
MAX_HISTORY_TURNS = 6  # sliding window: last 6 user+assistant pairs = 12 messages
LOW_CONFIDENCE_THRESHOLD = 0.45  # based on observed good-query range 0.57-0.60;
                                  # tune down if too many false low-confidence flags
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BASE_DELAY = 10  # seconds; doubles each retry (10, 20, 40)

# TODO: move to config.py in next session (agreed action list item 6)
REWRITE_MAP = {
    "rich":      "wealth financial prosperity 2nd house 11th house",
    "money":     "wealth income financial gains",
    "love":      "relationship marriage 7th house Venus",
    "marriage":  "marriage partner 7th house",
    "job":       "career profession 10th house",
    "health":    "health vitality 6th house",
    "children":  "children 5th house Jupiter",
    "travel":    "foreign travel 12th house",
}


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
    palm_description: str | None = None,
    n_results: int = DEFAULT_N_RESULTS,
    introduce: bool = False,
    session: SessionManager | None = None,
    **query_filters,
) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → GPT-4o-mini → structured response.

    Args:
        question: User question (must be non-empty).
        kundali_context: Optional birth chart summary string.
        palm_description: Optional palm reading description string.
        n_results: Number of chunks to retrieve (default 5).
        introduce: If True, Parashara introduces himself — suppressed if session
                   already has history (avoids mid-conversation re-introduction).
        session: Optional SessionManager. If provided, last MAX_HISTORY_TURNS of
                 conversation history are prepended to the GPT messages, and
                 question+answer are appended to the session on success.
        **query_filters: Passed to query_engine.search() — book_name, topic, page_type.

    Returns:
        {
            "answer":         str,        # Parashara's response
            "sources":        list[dict], # 9-field dicts from query_engine (backend use)
            "low_confidence": bool,       # True if top score < LOW_CONFIDENCE_THRESHOLD
            "model":          str,        # model used for inference
        }

    Raises:
        ValueError: Empty question.
        RuntimeError: ChromaDB collection empty.
        openai.RateLimitError: All retries exhausted.
    """
    if not question.strip():
        raise ValueError("question must not be empty.")

    # Step 1 — retrieve (rewritten query for search only; original question goes to GPT)
    search_query = _rewrite_query(question)
    sources = search(search_query, n_results=n_results, **query_filters)

    if not sources:
        return {
            "answer": (
                "I couldn't find relevant passages in my texts to answer this question. "
                "Could you rephrase or give me more context?\n\n" + DISCLAIMER
            ),
            "sources": [],
            "low_confidence": True,
            "model": MODEL,
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
        palm_description=palm_description,
        introduce=effective_introduce,
        low_confidence=low_confidence,
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

    if session:
        session.add_message("user", question)
        session.add_message("assistant", answer)

    return {
        "answer":         answer,
        "sources":        sources,
        "low_confidence": low_confidence,
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
