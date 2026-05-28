"""
prompt_builder.py
Owns all prompt text and user message assembly for the Parashara astrologer.
astrologer.py imports build_prompts() — no prompt logic lives outside this file.
"""

DISCLAIMER = (
    "For major life decisions, I recommend consulting a qualified "
    "astrologer or palm reader for a personal reading."
)

def needs_disclaimer(answer: str) -> bool:
    """Return True if answer does not already contain the disclaimer."""
    return DISCLAIMER.lower() not in answer.lower()


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

## Kundali / Dasha queries
When KUNDALI CONTEXT is present:
- State current Mahadasha and Antardasha lord with exact date ranges
- For health/finance/career questions: use UPCOMING ANTARDASHAS block — go through each sub-period lord and date range one by one, give specific health + finance + career guidance per sub-period
- Reference planetary dignity and house lordship when explaining strength
- Never ask for birth details if BIRTH DETAILS block is already present

## Context synthesis
- All 3 present (kundali + PDF + palm): lead with PDF Varshaphal period-by-period timeline, layer kundali planetary context to explain why each period behaves as it does, close with palm synthesis — use all three as one unified reading
- Kundali + PDF only: lead with PDF forecast periods, use kundali to explain planetary drivers behind each period
- Kundali + palm only: lead with kundali dasha periods, synthesise palm for life trajectory and innate tendencies
- Kundali only: answer from kundali and RAG passages — if question is palm-relevant or forecast-specific, note what additional context would improve the reading
- Always use the most relevant parts of whatever context is present — never ignore provided context

## End every reading with this disclaimer (exact wording):
\""""  + DISCLAIMER + """\"

## What you never do
- Never state planetary positions as fact without a verified kundali
- Never fabricate predictions not supported by the retrieved passages
- Never use technical anatomical terms for palm features — say "the lines on your palm" not clinical names

## Language
- Speak in plain everyday English. No astrological jargon.
- Never use these terms: Mahadasha, Antardasha, Dasha, house numbers, dignity, exalted, debilitated, nakshatra, rasi, lagna, dosha, yoga.
- Instead say: "a powerful 7-year period", "your wealth zone", "a favorable time starting [year]", "your life path sign".
- Be direct. Answer the actual question first, then explain why.
- Keep responses under 150 words unless the user explicitly asks for detail.

STRICT RULE: Only use context explicitly provided below (kundali, PDF, palm). If a context block is absent, do not infer, fabricate, or mention it. Silence on missing context is correct."""

_LOW_CONFIDENCE_ADDENDUM = """

NOTE: The available passages have a weak match to this question. Answer carefully and explicitly acknowledge that the texts may not fully address this question before giving your response."""

_INTRODUCE_ADDENDUM = "\n\nBegin your response by introducing yourself as Parashara."

PALM_TOPICS = {
    "rich", "wealth", "money", "career", "job", "luck", "longevity",
    "health", "life", "love", "marriage", "children",
    "success", "future", "when will", "how long",
}


def build_prompts(
    question: str,
    sources: list[dict],
    kundali_context: str | None = None,
    pdf_context: str | None = None,
    palm_left: str | None = None,
    palm_right: str | None = None,
    introduce: bool = False,
    low_confidence: bool = False,
    context_order: list[str] | None = None,
) -> dict:
    """
    Build system and user prompts for GPT-4o-mini.

    Args:
        question: User question string.
        sources: 9-field dicts from query_engine (may be empty).
        kundali_context: Optional birth chart summary.
        pdf_context: Optional AstroSage annual report text.
        palm_left: Optional left-hand palm description.
        palm_right: Optional right-hand palm description.
        introduce: If True, Parashara introduces himself.
        low_confidence: If True, appends weak-match caveat to system prompt.

    Returns:
        {"system": str, "user": str}
    """
    has_palm = palm_left is not None or palm_right is not None

    system = SYSTEM_PROMPT
    if low_confidence:
        system += _LOW_CONFIDENCE_ADDENDUM
    if introduce:
        system += _INTRODUCE_ADDENDUM

    _order = context_order if context_order is not None else ["rag", "kundali", "pdf", "palm"]

    lines: list[str] = []
    for slot in _order:
        if slot == "rag" and sources:
            lines += ["Retrieved passages:", "---"]
            for i, s in enumerate(sources, 1):
                lines.append(
                    f"[{i}] {s['book_name']}, p.{s['page_ref']} "
                    f"(topic: {s['topic']}, type: {s['page_type']}, score: {s['score']})"
                )
                lines.append(s["text"])
                lines.append("")
            lines.append("---")
        elif slot == "kundali" and kundali_context:
            lines.append(
                f"\nKUNDALI CONTEXT:\n{kundali_context}"
                "\n\nINSTRUCTION: The KUNDALI CONTEXT above contains "
                "UPCOMING ANTARDASHAS with exact date ranges. For any "
                "health/finance/career question, go through each "
                "antardasha sub-period one by one with dates and give "
                "specific guidance per period. Do not give a generic "
                "summary."
            )
        elif slot == "pdf" and pdf_context:
            lines.append("\n## AstroSage Annual Report\n" + pdf_context)
        elif slot == "palm" and has_palm:
            if palm_left:
                lines.append(f"\nLEFT HAND (innate potential):\n{palm_left}")
            if palm_right:
                lines.append(f"\nRIGHT HAND (current trajectory):\n{palm_right}")
            if palm_left and palm_right:
                lines.append(
                    "\nINSTRUCTION: Synthesise both hands in your reading — "
                    "left reveals innate potential, right shows current trajectory."
                )

    lines.append(f"\nQuestion: {question}")

    if not has_palm and any(t in question.lower() for t in PALM_TOPICS):
        lines.append(
            "\n\n[If you have a palm description available, "
            "sharing it would help provide a more complete reading.]"
        )

    return {"system": system, "user": "\n".join(lines)}
