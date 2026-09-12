"""Tests for agent/astro/answer_view.py -- the user-facing surface.

The fixtures here are the REAL claims from the S129 live run (project file
Output.txt), not invented ones, so the tests assert against what a user
actually saw rather than what we imagine they see.
"""
from __future__ import annotations

import pytest

from agent.astro import answer_view as AV

# Verbatim from the 2026-09-12 live run.
_LIVE_CLAIMS = [
    {"statement": "With the 10th lord in the 4th (an auspicious kendra), one will always gain "
                  "through royal patronage and in business.", "segment_ids": ["ch21_s005"]},
    {"statement": "With the 10th lord in the 4th joining the 9th lord there, the native will "
                  "obtain kingdom (high status).", "segment_ids": ["ch39_s015"]},
    {"statement": "With the 5th lord in the 2nd, the native will have wealth, be honourable, "
                  "and be famous in the world.", "segment_ids": ["ch24_s036"]},
]
_LIVE_SILENT_ON = [
    "Whether the 10th lord is exalted/own sign/strong, or aspected by Jupiter or benefics, "
    "is unknown; verses that require such conditions (e.g., ch21_s004, ch21_s012) cannot be applied.",
    "Combinations depending on Atmakaraka, Amatyakaraka, Karakamsa/Arudha or divisional "
    "dignities (e.g., ch40_s001–ch40_s015) cannot be judged from the provided facts.",
]
_DECLINE = ("I can't tell you when. The dasha period calculation isn't wired into the chart "
            "facts I can read yet, so any date or timeframe I gave you would be invented "
            "rather than calculated.")


def _result(**kw):
    base = {"kept_claims": [], "silent_on": [], "declined": [], "answer": "<lab fallback>"}
    base.update(kw)
    return base


# ── the diagnostics wall must not reach the user ───────────────────────────

def test_silent_on_never_appears_in_the_user_answer():
    out = AV.render_user_answer(_result(kept_claims=_LIVE_CLAIMS, silent_on=_LIVE_SILENT_ON))
    assert "Not addressed" not in out
    for token in ("Atmakaraka", "Karakamsa", "ch21_s004", "ch40_s001", "divisional dignities"):
        assert token not in out, f"internal diagnostics leaked to the user: {token}"


def test_raw_segment_ids_never_appear_inline():
    out = AV.render_user_answer(_result(kept_claims=_LIVE_CLAIMS))
    for cid in ("[ch21_s005]", "[ch39_s015]", "[ch24_s036]"):
        assert cid not in out


def test_inline_citation_markers_are_stripped_from_statement_text():
    r = _result(kept_claims=[{"statement": "You gain through patronage. [ch21_s005]",
                              "segment_ids": ["ch21_s005"]}])
    out = AV.render_user_answer(r)
    assert "[ch21_s005]" not in out
    assert "You gain through patronage." in out


# ── source line ────────────────────────────────────────────────────────────

def test_source_line_names_chapters_once_in_first_cited_order():
    line = AV.source_line(["ch24_s036", "ch21_s005", "ch24_s103", "ch34_s011"])
    assert line.startswith("Source: Brihat Parashara Hora Shastra")
    assert line.count("ch. 24") == 1, "a chapter cited twice must appear once"
    assert line.index("ch. 24") < line.index("ch. 21") < line.index("ch. 34")


def test_source_line_uses_the_real_chapter_name_when_it_is_clean():
    assert "Yoga Karakas" in AV.source_line(["ch34_s011"])


def test_ocr_garbage_title_degrades_to_the_chapter_number_only():
    """bphs1_ch39's title_raw is a run-on sentence, not a heading."""
    line = AV.source_line(["ch39_s015"])
    assert "ch. 39" in line
    assert "ncgligible" not in line and "Vosi yoga" not in line


def test_unknown_id_does_not_crash_and_is_shown_as_given():
    assert "totally_made_up" in AV.source_line(["totally_made_up_s001"])


def test_empty_citations_yield_no_source_line():
    assert AV.source_line([]) == ""


@pytest.mark.parametrize("raw,ok", [
    ("Yoga Karakas", True),
    ("Effects Of The Bhava Lords", True),
    ("", False),
    ("due to Nabhasa yogas etc. be also known which I narrate as under.", False),
    ("x" * 61, False),
    ("x" * 60, True),
])
def test_title_usability_guard(raw, ok):
    assert bool(AV._usable_title(raw)) is ok


# ── second person ──────────────────────────────────────────────────────────

def test_the_native_becomes_you():
    out = AV.render_user_answer(_result(kept_claims=_LIVE_CLAIMS))
    assert "the native" not in out.lower()
    assert "you will obtain kingdom" in out


def test_possessive_form_is_handled_before_the_bare_form():
    r = _result(kept_claims=[{"statement": "The native's wealth grows.", "segment_ids": ["ch24_s036"]}])
    assert "your wealth grows" in AV.render_user_answer(r).lower()
    assert "you's" not in AV.render_user_answer(r).lower()


def test_sentence_capitalisation_survives_the_swap():
    r = _result(kept_claims=[{"statement": "The native will travel. The native will gain.",
                              "segment_ids": ["ch24_s036"]}])
    out = AV.render_user_answer(r)
    assert "- You will travel. You will gain." in out


def test_third_party_nouns_are_not_rewritten():
    """A question about a child must not have 'your child' turned into 'you'."""
    r = _result(kept_claims=[{"statement": "With the 2nd lord strong, your child will prosper.",
                              "segment_ids": ["ch24_s036"]}])
    assert "your child will prosper" in AV.render_user_answer(r)


# ── the claim itself is never rewritten ────────────────────────────────────

def test_claim_wording_is_otherwise_untouched():
    """Only pronouns and citation markers may change. Paraphrasing a cited,
    gate-checked claim here would put unverified words in front of the user."""
    original = ("With the 10th lord in the 4th (an auspicious kendra), one will always gain "
                "through royal patronage and in business.")
    out = AV.render_user_answer(_result(kept_claims=[{"statement": original,
                                                      "segment_ids": ["ch21_s005"]}]))
    assert original in out, "answer_view must not rewrite claim content"


def test_checkable_placement_clause_is_preserved():
    """The silence gate reads 'the Nth lord ... in the Mth'. If the view ever
    mangled that clause the audit trail would stop matching the answer."""
    out = AV.render_user_answer(_result(kept_claims=_LIVE_CLAIMS))
    assert "With the 10th lord in the 4th" in out
    assert "With the 5th lord in the 2nd" in out


# ── refusal / decline paths ────────────────────────────────────────────────

def test_no_claims_gives_one_plain_sentence_plus_the_decline():
    out = AV.render_user_answer(_result(declined=[("dasha_timing", _DECLINE)]))
    assert out.startswith("I can't answer this from your chart")
    assert _DECLINE in out
    assert "Not addressed" not in out


def test_no_claims_and_no_decline_is_a_single_honest_sentence():
    out = AV.render_user_answer(_result())
    assert "I can't answer this" in out
    assert out.count("\n\n") == 0


def test_decline_is_appended_after_the_claims_not_instead_of_them():
    out = AV.render_user_answer(_result(kept_claims=_LIVE_CLAIMS,
                                        declined=[("dasha_timing", _DECLINE)]))
    assert "you will obtain kingdom" in out
    assert out.index("obtain kingdom") < out.index("I can't tell you when")


# ── never lose the answer ──────────────────────────────────────────────────

def test_malformed_result_falls_back_to_the_pipeline_answer():
    out = AV.render_user_answer({"kept_claims": "not-a-list", "answer": "<lab fallback>"})
    assert out == "<lab fallback>"


def test_claims_with_blank_statements_are_skipped_not_rendered_empty():
    r = _result(kept_claims=[{"statement": "   ", "segment_ids": ["ch21_s005"]},
                             {"statement": "You gain.", "segment_ids": ["ch21_s005"]}])
    out = AV.render_user_answer(r)
    assert out.count("- ") == 1
    assert "You gain." in out
