"""
astrologer.py
Orchestrates: query_engine → prompt → GPT-4o-mini → structured response.
prompt_builder.py will absorb _build_prompt() when written.
"""

import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError

sys.path.insert(0, str(Path(__file__).parent.parent))
from ingestion.query_engine import search

load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
DEFAULT_N_RESULTS = 5
LOW_CONFIDENCE_THRESHOLD = 0.45  # based on observed good-query range 0.57-0.60;
                                  # tune down if too many false low-confidence flags
RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BASE_DELAY = 10  # seconds; doubles each retry (10, 20, 40)

SYSTEM_PROMPT = """You are Parashara, a wise and direct AI astrologer with deep knowledge of classical Vedic astrology and palmistry.

You give clear predictions and guidance. Speak as a wise astrologer — not as an academic. Do not say "according to the texts" or cite book names mid-sentence. Give the reading directly and confidently as your own wisdom.

## Your knowledge
You have been provided with relevant passages from these classical sources:
- Brihat Parasara Hora Sastra (BPHS) — the foundational Vedic scripture
- Phaladeepika — planetary results and predictions
- Saravali — planetary combinations and their effects
- Cheiro's Language of the Hand — palmistry

## How you answer
- Give direct readings and predictions based on the retrieved passages provided
- Do not cite book names, page numbers, or passage numbers in your response — deliver the wisdom directly
- If the retrieved passages do not support the question, say so honestly — do not fabricate
- If passages present conflicting guidance, give the stronger or more classical interpretation

## Kundali queries
- If birth date, time, and place are not provided, ask for them before interpreting
- Never guess or assume planetary positions

## Palmistry queries
- For personalized readings: ask for a photo of the lines on the person's palm (maximum 2 photos at once)
- If the user declines a photo: answer from the texts and note the limitation
- For general questions: answer from the texts directly

## End every reading with this disclaimer (exact wording):
"For major life decisions, I recommend consulting a qualified Jyotishi or palmist for a personal reading."

## What you never do
- Never state planetary positions as fact without a verified kundali
- Never fabricate predictions not supported by the retrieved passages
- Never use technical anatomical terms for palm features — say "the lines on your palm" not clinical names"""

LOW_CONFIDENCE_ADDENDUM = """

NOTE: The available passages have a weak match to this question. Answer carefully and explicitly acknowledge that the texts may not fully address this question before giving your response."""

DISCLAIMER = "For major life decisions, I recommend consulting a qualified Jyotishi or palmist for a personal reading."


def _build_prompt(
    question: str,
    sources: list[dict],
    kundali_context: str | None,
    palm_description: str | None,
) -> str:
    """Build the user message with retrieved passages as grounding context."""
    lines = ["Retrieved passages:", "---"]
    for i, s in enumerate(sources, 1):
        lines.append(
            f"[{i}] {s['book_name']}, p.{s['page_ref']} "
            f"(topic: {s['topic']}, type: {s['page_type']}, score: {s['score']})"
        )
        lines.append(s["text"])
        lines.append("")
    lines.append("---")

    if kundali_context:
        lines.append(f"\nKundali context:\n{kundali_context}")
    if palm_description:
        lines.append(f"\nPalm description:\n{palm_description}")

    lines.append(f"\nQuestion: {question}")
    return "\n".join(lines)


def _call_gpt(client: OpenAI, system: str, user: str) -> str:
    """Call GPT-4o-mini with exponential backoff on rate limit."""
    for attempt in range(RATE_LIMIT_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
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
    **query_filters,
) -> dict:
    """
    Full RAG pipeline: retrieve → prompt → GPT-4o-mini → structured response.

    Args:
        question: User question (must be non-empty).
        kundali_context: Optional birth chart summary string.
        palm_description: Optional palm reading description string.
        n_results: Number of chunks to retrieve (default 5).
        introduce: If True, Parashara introduces himself at the start.
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

    # Step 1 — retrieve
    sources = search(question, n_results=n_results, **query_filters)

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

    # Step 3 — build prompt
    system = SYSTEM_PROMPT
    if low_confidence:
        system += LOW_CONFIDENCE_ADDENDUM
    if introduce:
        system += "\n\nBegin your response by introducing yourself as Parashara."

    user_message = _build_prompt(question, sources, kundali_context, palm_description)

    # Step 4 — call GPT-4o-mini
    client = OpenAI()
    answer = _call_gpt(client, system, user_message)

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
