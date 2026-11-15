"""tests/astro/test_fact_block_completeness.py
D1 -- "real chart in -> every MUST fact section is non-empty", with NO model call.

WHY THIS EXISTS: from S156 to S157 the Varshaphal (annual) section was SILENTLY
EMPTY on every real chart -- build_varshaphal_facts read lat/lon from meta (None on
a real calculate_chart output; coords live in birth_details) and fail-soft-returned
{} -- while the whole suite stayed green. The existing varshaphal tests all
MONKEYPATCH the ephemeris (see test_varshaphal_facts.py), so none of them exercised
the real pravesh path, and the gap was invisible. This test closes that class of
gap: it runs a REAL calculate_chart() for the Sulabh reference chart, assembles the
real fact block (static block + the answer-time varshaphal composer, called exactly
as pipeline.answer_question calls it), and asserts each section that MUST be
populated for any valid chart is non-empty.

NOT a model test: no OpenAI, no interpreter, no planner. Pure fact assembly over
swisseph. It needs the Swiss-ephemeris files present (same assumption as the other
real-chart tests in this package, e.g. test_chart_facts.test_real_* -- they do not
skip either).

SCOPE -- MUST vs MAY (THRESHOLD DISCIPLINE):
  MUST = computable from birth data alone for ANY valid chart, so an empty value is
         a regression. Asserted below.
  MAY  = legitimately empty for a valid chart, so NOT asserted (asserting them would
         false-red):
           - dignity        : holds ONLY exalted/deb/own-sign; a chart with none is
                               empty, and it is not even a top-level fact key.
           - yogas          : the *fired* set can be empty on a plain chart.
           - kp / kp_cusp_sub_lords / kp_planet_significations : withheld when the
                               birth time is not minute-accurate (input-conditional).
           - masa / ingress / combustion / muhurta : planner-gated DATED facts,
                               composed only when a dated question triggers them;
                               they are NOT in the static+varshaphal assembly at all.
           - life_context   : user-stated marital status, injected at answer time
                               only if the dropdown was filled; empty by default.
  TUNING NOTE: the MUST/MAY split is a product ruling (Sulabh, S-review 14 Nov), not
  a fit to this chart. Move a key across the line only on a recorded re-ruling. If a
  MAY key here is later promoted (e.g. kp_planet_significations made MUST for a
  minute-accurate chart), add it to _MUST with its own reason.

CHART: Sulabh's reference chart only (minute-accurate -> the KP path is present).
One chart is the agreed scope; a non-minute-accurate chart (to exercise the
KP-withheld branch) is a separate fixture, not added here.
"""
from __future__ import annotations

from agent.chart_calculator import calculate_chart
from agent.astro.static_facts import build_static_facts
from agent.astro.varshaphal_facts import build_varshaphal_facts

# Same birth data the rest of the suite uses for Sulabh
# (tests/astro/test_chart_facts.py:20).
_SULABH = ("Sulabh", "6 Apr 1988", "00:30", "Calcutta, India")

# Sections that MUST be non-empty for any valid chart. Each is produced by the
# static assembler build_static_facts() EXCEPT "varshaphal", which S157 moved to
# answer-time compose in pipeline.answer_question and which this test composes the
# same way (build_varshaphal_facts(chart), default as_of=today).
_MUST = (
    "ascendant_sign",      # the ascendant
    "lord_house_map",      # the 12 house-lord placements
    "planet_positions",    # per-graha house + sign
    "house_lords",         # which planet rules each house
    "aspects",             # conjunctions / aspects
    "navamsa",             # D9 (composed into the chart before build_chart_facts)
    "dasha_periods",       # Vimshottari MD + AD tree
    "transits",            # per-antardasha Saturn gochara + Sade Sati phase
    "shadbala",            # six-fold strength
    "ashtakavarga",        # SAV / BAV
    "jaimini",             # chara karakas + Arudha/Upapada
    "divisional",          # domain vargas (D10/D7/...)
    "friendship",          # pancha-dha maitri
    "yogini",              # Yogini Mahadasha
    "narayana",            # Narayana rasi dasa
    "ashtottari",          # Ashtottari dasa
    "lucky_unlucky",       # favourable / avoid weekdays
    "varshaphal",          # Tajika annual chart -- the S157 regression guard
)


def _assembled_facts() -> dict:
    """The real fact block the interpreter would read, assembled WITHOUT any model
    call: the static block, plus varshaphal composed exactly as answer_question
    does it (default as_of -> current solar year). build_static_facts is fail-soft,
    so a crashed composer leaves its key ABSENT -- which _MUST catches as a miss."""
    chart = calculate_chart(*_SULABH)
    facts = build_static_facts(chart)
    vp = build_varshaphal_facts(chart)   # real pravesh path, NO monkeypatch
    if vp:
        facts["varshaphal"] = vp
    return facts


def test_every_must_fact_section_is_non_empty_for_the_sulabh_chart():
    facts = _assembled_facts()
    empty = [k for k in _MUST if not facts.get(k)]
    assert not empty, (
        "MUST fact sections empty/absent on the real Sulabh chart: "
        f"{empty}. A section here is a regression (e.g. the S157 varshaphal "
        "lat/lon bug), not a chart property -- trace the composer, do not relax "
        "this list without a recorded re-ruling."
    )


def test_varshaphal_populates_on_the_real_chart_not_just_the_mocked_path():
    # Pointed restatement of the S157 regression, independent of the loop above so
    # a failure names varshaphal directly. The pre-fix composer returned {} here.
    chart = calculate_chart(*_SULABH)
    vp = build_varshaphal_facts(chart)
    assert vp, ("build_varshaphal_facts returned empty on the REAL Sulabh chart -- "
                "the S157 lat/lon-in-birth_details regression has returned.")
    assert vp.get("year"), "varshaphal produced no solar year on the real chart"
