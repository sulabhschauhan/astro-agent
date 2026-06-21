"""SPIKE -- throwaway interpretive-text feasibility harness. NOT production
code. Nothing in agent/ or ingestion/ may ever import from spikes/, and
nothing here should be relied on beyond this one-off comparison run.

Goal: produce a single comparison artifact (AstroSage paragraph vs.
RAG+GPT-4o-mini standalone vs. RAG+GPT-4o-mini layered-over-AstroSage) for
Sulabh to manually score against a 4-dimension rubric. See SESSION_LOG.md
Session 21's "Interpretive-text feasibility spike" backlog item.

RETARGET NOTE: original spike scope said Saturn-in-6th-from-Lagna for
Sheridan at the canonical anchor. Step 1 verification (compute_gochara)
showed Saturn is actually in the 11th house from Lagna at that moment, not
the 6th -- retargeted to match reality rather than silently testing a
fabricated position. Saturn-from-Moon=12, consistent with the locked Sade
Sati RISING phase (P2.2.2).
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))  # project root

import swisseph as swe
from openai import OpenAI

from agent.calculations.transits.gochara import compute_gochara
from agent.chart_calculator import _calc_planets, calculate_chart
from ingestion.query_engine import search

MODEL = "gpt-4o-mini"
TARGET_HOUSE_FROM_LAGNA = 11
RAG_QUERY = "Saturn transit eleventh house effects classical"
RAG_TOP_K = 8

# Sulabh will paste Sheridan's AstroSage transit paragraph for "Saturn in
# 11th house" here before running for real. LLM calls (steps 3-4) only
# fire once this is no longer the placeholder.
ASTROSAGE_PARA = (
    "SATURN is in Pisces in your 11th House. Physically as well as "
    "mentally you will be very courageous during this period. This is "
    "a good phase for your relatives. Go for attempts in your career "
    "life as the success is assured. Gain of material things is also "
    "indicated. You will purchase land and machinery during this period. "
    "Substantial gains in your business and trades are assured. Your "
    "enemies will not be able to plunk before you. You will come into "
    "contact with people from far off places. This period is also very "
    "good as far as love life is concerned. You will receive full "
    "support from your family members."
)

_ANCHOR_JD = swe.julday(2026, 6, 20, 18.5)  # canonical anchor, gochara.py

_SYSTEM_PROMPT = (
    "You are a classical Vedic astrologer speaking in the voice of "
    "Parashara, grounded strictly in BPHS, Phaladeepika, and Saravali. "
    "No pop astrology, no generic positivity, no hedging disclaimers. "
    "Respond in approximately 200 words."
)


def _natal_lons(name: str, dob: str, tob: str, place: str) -> tuple[float, float]:
    """Same pattern as test_gochara.py's _natal_lons -- not redefined as a
    shared helper since this file is throwaway."""
    chart = calculate_chart(name, dob, tob, place)
    jd_ut = chart["meta"]["jd_ut"]
    asc_lon = chart["meta"]["asc_lon_sidereal"]
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    natal_planets = _calc_planets(jd_ut, asc_lon)
    return asc_lon, natal_planets["Moon"]["longitude"]


def step1_verify_transit():
    asc_lon, moon_lon = _natal_lons(
        "Sheridan", "27 May 1984", "08:00", "Durban, South Africa"
    )
    snapshot = compute_gochara(_ANCHOR_JD, asc_lon, moon_lon)
    saturn = next(p for p in snapshot.placements if p.planet_name == "Saturn")
    print(
        f"Saturn sign={saturn.sign} house_from_lagna={saturn.house_from_lagna} "
        f"house_from_moon={saturn.house_from_moon} retrograde={saturn.is_retrograde}"
    )
    if saturn.house_from_lagna != TARGET_HOUSE_FROM_LAGNA:
        sys.exit(
            f"ABORT: spike claims Saturn is in house {TARGET_HOUSE_FROM_LAGNA} "
            f"from Lagna, but compute_gochara found house_from_lagna="
            f"{saturn.house_from_lagna}. Not silently testing a different "
            f"position -- fix TARGET_HOUSE_FROM_LAGNA (or the anchor) and rerun."
        )
    return saturn


def step2_retrieve_chunks():
    chunks = search(RAG_QUERY, n_results=RAG_TOP_K)
    print(f"\nRAG query: {RAG_QUERY!r} -> {len(chunks)} chunks\n")
    for i, c in enumerate(chunks, 1):
        print(f"[{i}] score={c['score']} | {c['book_name']} p.{c['page_ref']}")
        print(f"     {c['text'][:200]}")
    return chunks


def _chunks_block(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['book_name']} p.{c['page_ref']}]\n{c['text']}" for c in chunks
    )


def step3_generate_standalone(chunks: list[dict]) -> tuple[str, object]:
    """Returns (content, usage) -- usage is None if the call failed."""
    user_prompt = (
        "Sheridan, Aries Moon native, currently has transit Saturn in her "
        "11th house from Lagna. Based on the following classical "
        "references, give a classical interpretation.\n\n" + _chunks_block(chunks)
    )
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        return response.choices[0].message.content, response.usage
    except Exception as exc:
        return f"[GPT call failed: {exc}]", None


def step4_generate_layered(chunks: list[dict]) -> tuple[str, object]:
    """Returns (content, usage) -- usage is None if the call failed."""
    user_prompt = (
        "Sheridan, Aries Moon native, currently has transit Saturn in her "
        "11th house from Lagna. Based on the following classical "
        "references, give a classical interpretation.\n\n" + _chunks_block(chunks)
        + f"\n\nAstroSage provides this templated reading: {ASTROSAGE_PARA}\n\n"
        "Add classical depth and specificity beyond what AstroSage states; "
        "do not contradict it; maintain Parashara voice."
    )
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
        )
        return response.choices[0].message.content, response.usage
    except Exception as exc:
        return f"[GPT call failed: {exc}]", None


def step5_write_artifact(saturn, chunks, output_b, output_c):
    out_path = Path(__file__).parent / "saturn_11th_comparison.md"
    lines = []
    lines.append("# Saturn 11th-from-Lagna Interpretive-Text Spike -- Sheridan\n")

    lines.append("## Transit fact\n")
    lines.append(f"- Saturn sign (1-12): {saturn.sign}")
    lines.append(f"- House from Lagna: {saturn.house_from_lagna}")
    lines.append(f"- House from Moon: {saturn.house_from_moon}")
    lines.append("- Transit moment: 2026-06-20 18:30 UTC (canonical anchor)\n")

    lines.append("## Section A: AstroSage paragraph\n")
    lines.append(ASTROSAGE_PARA + "\n")

    lines.append("## Section B: RAG+mini standalone output\n")
    lines.append((output_b or "[not generated -- ASTROSAGE_PARA still placeholder]") + "\n")

    lines.append("## Section C: RAG+mini layered output\n")
    lines.append((output_c or "[not generated -- ASTROSAGE_PARA still placeholder]") + "\n")

    lines.append("## RAG chunks retrieved\n")
    for i, c in enumerate(chunks, 1):
        lines.append(f"### [{i}] {c['book_name']} p.{c['page_ref']} (score={c['score']})\n")
        lines.append(c["text"] + "\n")

    lines.append("## Rubric scoring\n")
    lines.append("Dimension 1 (specificity beyond A): [ ]")
    lines.append("Dimension 2 (voice): [ ]")
    lines.append("Dimension 3 (no contradiction): [ ]")
    lines.append("Dimension 4 (personalization): [ ]")
    lines.append("Decision: [ ]\n")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {out_path}")


def main():
    saturn = step1_verify_transit()
    chunks = step2_retrieve_chunks()

    if ASTROSAGE_PARA == "<<<PASTE FROM ASTROSAGE>>>":
        print(
            "\nASTROSAGE_PARA is still the placeholder -- skipping live "
            "GPT-4o-mini calls (Sections B/C). Artifact will note this."
        )
        output_b = None
        output_c = None
    else:
        t0 = time.perf_counter()
        output_b, usage_b = step3_generate_standalone(chunks)
        output_c, usage_c = step4_generate_layered(chunks)
        elapsed = time.perf_counter() - t0

        total_prompt = sum(u.prompt_tokens for u in (usage_b, usage_c) if u)
        total_completion = sum(u.completion_tokens for u in (usage_b, usage_c) if u)
        total_tokens = sum(u.total_tokens for u in (usage_b, usage_c) if u)
        print(
            f"\nLLM steps (B+C): {elapsed:.2f}s wall clock | "
            f"tokens prompt={total_prompt} completion={total_completion} "
            f"total={total_tokens}"
        )

    step5_write_artifact(saturn, chunks, output_b, output_c)


if __name__ == "__main__":
    main()
