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

## Palmistry queries
- For personalized readings: ask for a photo of the lines on the person's palm (maximum 2 photos at once)
- If the user declines a photo: answer from the texts and note the limitation
- For general questions: answer from the texts directly

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
- Keep responses under 150 words unless the user explicitly asks for detail."""

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
    palm_description: str | None = None,
    introduce: bool = False,
    low_confidence: bool = False,
) -> dict:
    """
    Build system and user prompts for GPT-4o-mini.

    Args:
        question: User question string.
        sources: 9-field dicts from query_engine (may be empty).
        kundali_context: Optional birth chart summary.
        palm_description: Optional palm reading description.
        introduce: If True, Parashara introduces himself.
        low_confidence: If True, appends weak-match caveat to system prompt.

    Returns:
        {"system": str, "user": str}
    """
    has_palm_description = palm_description is not None

    system = SYSTEM_PROMPT
    if low_confidence:
        system += _LOW_CONFIDENCE_ADDENDUM
    if introduce:
        system += _INTRODUCE_ADDENDUM

    lines: list[str] = []
    if sources:
        lines += ["Retrieved passages:", "---"]
        for i, s in enumerate(sources, 1):
            lines.append(
                f"[{i}] {s['book_name']}, p.{s['page_ref']} "
                f"(topic: {s['topic']}, type: {s['page_type']}, score: {s['score']})"
            )
            lines.append(s["text"])
            lines.append("")
        lines.append("---")

    if kundali_context:
        lines.append(
            f"\nKUNDALI CONTEXT:\n{kundali_context}"
            "\n\nINSTRUCTION: The KUNDALI CONTEXT above contains "
            "UPCOMING ANTARDASHAS with exact date ranges. For any "
            "health/finance/career question, go through each "
            "antardasha sub-period one by one with dates and give "
            "specific guidance per period. Do not give a generic "
            "summary."
        )
    if palm_description:
        lines.append(f"\nPalm description:\n{palm_description}")
    if has_palm_description:
        lines.append(
            "\n[You have both kundali and palm context — synthesise both in your reading.]"
        )

    lines.append(f"\nQuestion: {question}")

    if not has_palm_description and any(t in question.lower() for t in PALM_TOPICS):
        lines.append(
            "\n\n[If you have a palm description available, "
            "sharing it would help provide a more complete reading.]"
        )

    return {"system": system, "user": "\n".join(lines)}
