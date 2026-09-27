"""S141 EXPERT-MODE PILOT -- throwaway, measurement only. NOT wired to production.

WHY: Path B's cited-claim interpreter produces naive answers vs the desktop
benchmark (Output.txt). This pilot tests Sulabh's hypothesis: give the LLM the
SAME inputs Path B builds (real computed chart facts + retrieved BPHS verses) but
let it answer like an expert instead of emitting verse-cited JSON claims. Facts
stay hard-grounded (the prompt forbids inventing any placement/date/yoga);
interpretation is freed.

Run on a machine WITH OpenAI access (the Cowork sandbox is firewalled):
    python scripts/expert_pilot.py [marriage_past|marriage_future|ketu_md|career]
Output -> stdout + diagnostics/latest_run.md. Compare against Output.txt.
Delete this file once the approach is decided; it is not part of the pipeline.
"""
from __future__ import annotations
import os, sys, datetime

from agent.chart_calculator import calculate_chart
from agent.astro.chart_facts import build_chart_facts
from agent.astro import pipeline, planner
from agent.calculations.vargas.navamsa import compute_navamsa
from agent.astro.yoga_facts import build_yoga_facts
from agent.astro.transit_facts import build_transit_facts
from agent.astro.kp_facts import build_kp_facts
from agent.astro.kp_significator_facts import build_kp_significator_facts

SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")

# (question, domains, houses, time_scope) -- domains/houses hardcoded so the pilot
# needs NO planner LLM call; these mirror what the planner produces for each.
QUESTIONS = {
    "marriage_past":   ("Predict my marriage timing window only as per my chart. When would I have got married?",
                        ["marriage", "timing_dasha"], [7, 2, 11, 8], "past"),
    "marriage_future": ("When will I get married?",
                        ["marriage", "timing_dasha"], [7, 2, 11, 8], "future"),
    "ketu_md":         ("What does my current Ketu mahadasha mean for me?",
                        ["timing_dasha"], [1, 9], "present"),
    "career":          ("When will my career take off?",
                        ["career", "timing_dasha"], [10, 1, 2, 11], "future"),
}

EXPERT_SYSTEM = """You are an expert Vedic astrologer in the Parashari tradition (Brihat Parashara Hora Shastra, Phaladeepika, Saravali), also fluent in the KP and Lal Kitab systems. You are reading ONE person's birth chart and answering their question directly, for THEM to read.

You are given (1) the COMPUTED CHART FACTS for this person and (2) relevant classical passages. Work from these.

HARD RULE -- facts are not yours to invent:
- Every chart FACT you state -- a planet's house or sign, which house a lord occupies, a dignity, a yoga, a dasha/antardasha period or its dates, a transit placement (where a planet was transiting, and relative to what, at a given time), a KP (Krishnamurti Paddhati) house-cusp sub-lord, or a KP house significator (which houses a planet signifies) -- MUST come from the CHART FACTS given below. Never invent, guess, or compute a placement or a date. If a fact you would need is not in the block, say what the given facts support and name the limit rather than filling the gap.
- A NATAL fact (fixed for this chart -- a placement, a dignity, a house's own sub-lord) and a TRANSIT fact (a planet's moving position at a given time) are DIFFERENT quantities. Two facts that merely name the same planet are not automatically related -- treat them as corroborating each other only when the specific technique you are applying actually connects them, never just because the name matches.
- INTERPRETATION -- what a placement or period MEANS -- may draw on your expert knowledge of the classical texts and the passages provided. Never use pop astrology or unverified sources.

ANSWER LIKE AN EXPERT WOULD:
- Lead with the real answer to their question -- the bottom line first, including the uncomfortable part if there is one. No throat-clearing.
- Be specific to THIS chart: name the actual placements and periods driving your reading. For any timing, give the real date windows from the dasha facts as month/quarter ranges (the dates are approximate, +/-37 days -- say so once, not repeatedly). A retrospective question ("when would I have...") is answered with the correct PAST period, not a future one.
- For a timing/ranking question, survey EVERY dasha sub-period the fact block gives you before ranking candidates, not just the ones that first come to mind. A period you silently skip is a period you have implicitly ruled out without saying so -- if you rule one out, name it and give a one-line reason, even briefly.
- Structure however the question demands -- a timing question wants ranked windows; a "what does X mean" question wants themes, perhaps a short period-by-period read. Short paragraphs or a few grouped points, whatever reads best. Do not pad.
- Say how sure you are in plain words -- very likely / likely / possible / uncertain -- and why, tied to the facts.
- Plain second-person language ("you", "your"). Translate every technical term (say "your marriage ruler", or name it once in brackets). NO citations, NO verse ids -- write as an astrologer speaking to a client, not a footnoted paper.
- Be honest and non-fatalistic. Report difficult indications plainly, without drama, false alarm, or false reassurance."""


def _facts():
    chart = calculate_chart(*SULABH)
    try:  # D9, fail-soft, same composition as frontend/app.py
        meta = chart.get("meta") or {}
        d9 = compute_navamsa(meta["jd_ut"], meta["asc_lon_sidereal"])
        chart = dict(chart, navamsa={
            "d9_lagna_sign": d9.d9_lagna_sign,
            "placements": {p: {"sign": pl.d9_sign, "house": pl.d9_house}
                           for p, pl in d9.placements.items()}})
    except Exception as e:  # noqa: BLE001
        print(f"[pilot] D9 skipped: {type(e).__name__}: {e}", file=sys.stderr)
    cf = build_chart_facts(chart)
    try:
        cf["yogas"] = build_yoga_facts(chart, cf)
    except Exception as e:  # noqa: BLE001
        print(f"[pilot] yogas skipped: {type(e).__name__}: {e}", file=sys.stderr)
    try:  # S142: Sade Sati / Saturn gochara per antardasha, same composition style
        cf["transits"] = build_transit_facts(chart, cf)
    except Exception as e:  # noqa: BLE001
        print(f"[pilot] transits skipped: {type(e).__name__}: {e}", file=sys.stderr)
    try:  # S143: KP 7th-cusp sub-lord, same composition style
        cf["kp"] = build_kp_facts(chart)
    except Exception as e:  # noqa: BLE001
        print(f"[pilot] KP skipped: {type(e).__name__}: {e}", file=sys.stderr)
    try:  # S144: KP house significators, ephemeris-COMPUTED from `chart`
        # (no PDF -- see agent/calculations/kp/significator_engine.py). Same
        # composition style as the fact classes above.
        cf["kp_planet_significations"] = build_kp_significator_facts(chart)
    except Exception as e:  # noqa: BLE001
        print(f"[pilot] KP significators skipped: {type(e).__name__}: {e}",
              file=sys.stderr)
    return cf


def _verses(payload):
    parts = [s["text"].strip() for s in payload.get("segments", []) if s.get("kept")]
    parts += [u["text"].strip() for u in payload.get("units", [])]
    return "\n\n".join(parts)


def run(key):
    q, domains, houses, ts = QUESTIONS[key]
    cf = _facts()
    fact_block = pipeline._fact_block(cf)
    # S144: append the deterministic timing ranking for this question's houses
    # (same path production uses in pipeline.answer_question).
    from agent.astro import timing_ranker
    _rk = timing_ranker.render_ranking(timing_ranker.build_timing_ranking(cf, houses))
    if _rk:
        fact_block = fact_block + "\n" + _rk
    plan = planner.Plan(question=q, domains=domains, houses=houses,
                        whose_chart="self", time_scope=ts, in_scope=True,
                        reasoning="expert-mode pilot")
    built = planner.build_from_plan(plan, cf)
    payload = built.get("payload") or {}
    approx = built.get("tokens")
    user = (f"CHART FACTS (the only chart facts you may state):\n{fact_block}\n\n"
            f"CLASSICAL PASSAGES (for interpretation):\n{_verses(payload)}\n\n"
            f"QUESTION: {q}\n\nAnswer the person directly, as an expert astrologer.")

    from openai import OpenAI
    client = OpenAI()
    resp = client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "system", "content": EXPERT_SYSTEM},
                  {"role": "user", "content": user}])
    ans = resp.choices[0].message.content or ""
    u = resp.usage

    header = (f"# EXPERT-MODE PILOT -- {key}\n\n"
              f"- question: {q}\n- payload approx-tokens: {approx}\n"
              f"- prompt_tokens: {getattr(u,'prompt_tokens',0)} | completion: {getattr(u,'completion_tokens',0)}\n"
              f"- ran: {datetime.datetime.utcnow().isoformat()}Z\n\n"
              f"## EXPERT ANSWER\n\n{ans}\n\n"
              f"## THE FACT BLOCK IT WAS GIVEN (audit invented facts against this)\n\n"
              f"```\n{fact_block}\n```\n")
    os.makedirs("diagnostics", exist_ok=True)
    with open("diagnostics/latest_run.md", "w", encoding="utf-8") as f:
        f.write(header)
    print("\n" + "=" * 70 + f"\nEXPERT ANSWER ({key}):\n" + "=" * 70 + f"\n{ans}\n")
    print(f"[pilot] full output + fact block -> diagnostics/latest_run.md")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "marriage_past"
    if key not in QUESTIONS:
        print(f"unknown key {key!r}; choose from {list(QUESTIONS)}"); sys.exit(1)
    run(key)
