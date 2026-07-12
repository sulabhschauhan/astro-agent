"""
agent/interpretive/answer_renderer.py
Deterministic DomainAnswer -> layman display-text renderer.

Zero LLM (CLAUDE.md "V1 scope" lock, Session 23): deterministic
calculation-engine output (result_formatter.py's DomainAnswer) is V1's only
structured Q&A surface -- this module is the final presentation layer on
top of it, pure Python template-fill only. Companion to
agent/infra/result_formatter.py, which builds the DomainAnswer this module
reads; this module never recomputes or reinterprets a payload value, it
only chooses plain-language wording for values already present.

Every payload field this file reads was verified against
agent/infra/result_formatter.py's/agent/infra/chart_profile.py's ACTUAL
branch code before being used here -- never guessed from a field name's
sound. Where a field's semantics were not already documented in those
files (e.g. muhurta_scorer.py's MuhurtaTier value strings, sade_sati's
phase Literal), the underlying calculation module was read directly (see
each _render_* helper's own comments for its specific source).

No Ring 1 runtime jargon/validation check lives in THIS module (unlike
agent/interpretive/palm_reading.py's ValidationReport) -- that module
validates untrusted LLM output at runtime, a genuine safety gate; this
module's output is fully self-authored/deterministic, so the burden of
proving language-quality compliance (no unglossed jargon) lives in this
module's own test suite (tests/interpretive/test_answer_renderer.py),
not as a baked-in runtime check with nothing untrusted to validate
against.
"""

from __future__ import annotations

from agent.infra.chart_profile import AnswerTier, DomainAnswer

# muhurta_scorer.MuhurtaTier value strings (TIER_1/TIER_2/TIER_3) -> layman
# labels. Closes the CLAUDE.md Session 64 carry-forward ("Per-window
# MuhurtaTier value strings are internal jargon") -- this is the "V1's
# answer-text layer" that carry-forward entry names as the correct place
# for this relabeling. SENSITIVE_TO muhurta_scorer.py's MuhurtaTier enum:
# if a 4th tier value is ever added there, this dict must be extended too
# (the .get() fallback below renders the raw string rather than crashing,
# but that raw string would itself be internal jargon leaking through).
_MUHURTA_TIER_LABELS: dict[str, str] = {
    "TIER_1": "excellent",
    "TIER_2": "good",
    "TIER_3": "favorable for you specifically",
}

# sade_sati.py's PhaseWindow/SadeSatiStatus `phase` Literal (read directly
# from agent/calculations/transits/sade_sati.py before use, not guessed):
# Literal["RISING", "PEAK", "SETTING", "NONE"]. "NONE" is never actually
# looked up here -- _render_sade_sati() only consults this dict when
# active=True, and phase is guaranteed != "NONE" whenever active=True
# (sade_sati.py's own `active = phase != "NONE"` construction).
_SADE_SATI_PHASE_LABELS: dict[str, str] = {
    "RISING": "the rising phase (roughly the first 2.5 years of the cycle)",
    "PEAK": "the peak phase (the middle 2.5 years, traditionally considered the most intense)",
    "SETTING": "the setting phase (roughly the final 2.5 years of the cycle)",
}

# marriage_compatibility's answer_payload["koota_scores"] keys, verbatim
# from result_formatter._format_marriage()'s koota_scores dict construction
# -- read from that function's source before writing this, not guessed.
_KOOTA_LABELS: dict[str, str] = {
    "varna": "Varna (temperament compatibility)",
    "vashya": "Vashya (mutual attraction and control)",
    "tara": "Tara (birth-star compatibility)",
    "yoni": "Yoni (physical and instinctive compatibility)",
    "graha_maitri": "Graha Maitri (planetary friendship)",
    "gana": "Gana (temperament grouping)",
    "bhakoota": "Bhakoota (emotional and family harmony)",
    "nadi": "Nadi (health and genetic compatibility)",
}

_MARRIAGE_VERDICT_LABELS: dict[str, str] = {
    "highly_compatible": "highly compatible",
    "compatible": "compatible",
    "moderately_compatible": "moderately compatible",
    "incompatible": "not well matched",
}


def render_answer(answer: DomainAnswer) -> str:
    """
    Render a DomainAnswer into plain-language display text.

    REFUSAL short-circuits everything else (rule 2): answer_payload's
    "user_message" is returned exactly as-is -- no domain dispatch (a
    REFUSAL's domain may be None, see result_formatter.format_refusal()),
    and demotion_reason is NOT separately appended for REFUSAL, because
    format_refusal() already used demotion_reason to select user_message
    in the first place (appending it again would be a redundant/confusing
    second statement of the same refusal reason, not a genuine additional
    accuracy caveat on an otherwise-valid answer).

    For every other tier, dispatches on answer.domain to one of 7
    domain-specific renderers, then appends answer.demotion_reason (when
    present) as a plain-language "Accuracy note:" paragraph -- verbatim,
    never dropped, never reworded (rule 3; demotion_reason is a downstream
    machine contract elsewhere in this pipeline, e.g. golden-harness
    substring assertions, so its text is never altered here).

    Raises:
        ValueError: answer.domain is not one of the 7 routed domains this
            renderer knows about (mirrors calc_router._route_to_domain's
            defensive `else: raise ValueError` precedent).
        KeyError: propagates from any domain renderer's direct payload
            indexing -- a missing expected key is a contract violation
            upstream, never silently defaulted here.
    """
    if answer.tier == AnswerTier.REFUSAL:
        return answer.answer_payload["user_message"]

    domain = answer.domain
    payload = answer.answer_payload

    if domain == "current_dasha":
        body = _render_current_dasha(payload)
    elif domain == "sade_sati":
        body = _render_sade_sati(payload)
    elif domain == "career_strength":
        body = _render_career(payload)
    elif domain == "marriage_compatibility":
        body = _render_marriage(payload)
    elif domain == "arudha_lagna":
        body = _render_arudha_lagna(payload)
    elif domain == "upapada_lagna":
        body = _render_upapada_lagna(payload)
    elif domain == "muhurta_window":
        body = _render_muhurta_window(payload)
    else:
        raise ValueError(f"answer_renderer.render_answer: unknown domain {domain!r}")

    if answer.demotion_reason:
        body += "\n\nAccuracy note: " + answer.demotion_reason

    return body


def _render_timing_enrichment(block: dict) -> str:
    """Renders the OPTIONAL "timing_enrichment" block shared by
    career_strength/current_dasha (result_formatter._render_av_timing()'s
    output shape, read from that function's source). Rendered plainly
    (rule 1: unclear semantics -> render plainly, don't interpret) --
    this project's dogfood has not yet exercised this optional block live
    (result_formatter.py's own docstring notes the upstream convergence
    layer that populates it does not exist yet), so no per-domain happy
    path test below relies on it; included for contract completeness only.
    """
    envelope = block["dasha_envelope"]
    return (
        f"Timing check for the {block['transit_planet'].title()} transit: "
        f"within your current Antardasha (sub-period) window "
        f"({envelope['start']} to {envelope['end']}), "
        f"{len(block['sub_windows'])} ranked timing window(s) were found."
    )


def _render_current_dasha(payload: dict) -> str:
    """current_dasha payload keys verbatim from
    result_formatter._format_dasha(): mahadasha/antardasha (each
    {"lord", "start", "end"}), near_boundary (bool), boundary_note
    (str | None), optional timing_enrichment.

    boundary_note is deliberately NOT rendered here even though it is
    always present in the payload dict: reading _format_dasha()'s source
    shows boundary_note and demotion_reason are set together, from the
    same `if near_boundary:` branch, and carry the same +/-37-day-drift
    caveat -- rendering both would duplicate the identical message (once
    here, once via render_answer()'s top-level "Accuracy note:" append).
    Relying solely on demotion_reason for this caveat is safe precisely
    because the two fields are never decoupled by this formatter's own
    code -- not an assumption, verified against the source.
    """
    maha = payload["mahadasha"]
    antar = payload["antardasha"]

    lines = [
        f"You are currently in a Mahadasha (major life period) ruled by "
        f"{maha['lord'].title()}, running from {maha['start']} to "
        f"{maha['end']}.",
        f"Within that, you are in an Antardasha (a shorter sub-period "
        f"inside the Mahadasha) ruled by {antar['lord'].title()}, from "
        f"{antar['start']} to {antar['end']}.",
    ]

    enrichment = payload.get("timing_enrichment")
    if enrichment is not None:
        lines.append("")
        lines.append(_render_timing_enrichment(enrichment))

    return "\n".join(lines)


def _render_sade_sati(payload: dict) -> str:
    """sade_sati payload keys verbatim from
    result_formatter._format_sade_sati(): active (bool), phase (str),
    next_cycle_start (str, always present); current_cycle_start/end
    present only when active=True, previous_cycle_end present only when
    active=False (mirrors that function's own if/else payload assembly).
    """
    active = payload["active"]
    phase = payload["phase"]
    next_cycle_start = payload["next_cycle_start"]

    lines: list[str] = []
    if active:
        phase_text = _SADE_SATI_PHASE_LABELS.get(phase, phase)
        current_start = payload["current_cycle_start"]
        current_end = payload["current_cycle_end"]
        lines.append(
            "You are currently in Sade Sati (Saturn's roughly 7.5-year "
            f"transit around your Moon sign) — specifically {phase_text}."
        )
        lines.append(
            f"This current cycle runs from {current_start} to {current_end}."
        )
    else:
        previous_end = payload["previous_cycle_end"]
        lines.append(
            "You are not currently in Sade Sati (Saturn's roughly "
            "7.5-year transit around your Moon sign)."
        )
        lines.append(f"Your previous Sade Sati cycle ended {previous_end}.")

    lines.append(
        f"Your next Sade Sati cycle is expected to begin around "
        f"{next_cycle_start}."
    )
    return "\n".join(lines)


def _render_career(payload: dict) -> str:
    """career_strength payload keys verbatim from
    result_formatter._format_career(): career_significators
    ({"tenth_lord", "sun", "saturn"}, each a _significator_block shape --
    {"planet", "rupa", "ratio", "rank", "label", "above_min"}),
    strongest_planet, weakest_planet, bhava_10_rupa, optional
    timing_enrichment.

    Rank is rendered "of 7" (not guessed): result_formatter._format_career()
    itself derives weakest_planet via `row["rank"] == 7`, confirming
    shadbala ranks span the 7 classical grahas (Sun..Saturn, no
    Rahu/Ketu), read from that source rather than assumed.
    """
    sig = payload["career_significators"]
    tenth_lord = sig["tenth_lord"]
    sun = sig["sun"]
    saturn = sig["saturn"]
    strongest = payload["strongest_planet"]
    weakest = payload["weakest_planet"]
    bhava_10_rupa = payload["bhava_10_rupa"]

    def _significator_line(label: str, block: dict) -> str:
        return (
            f"- {label} ({block['planet'].title()}): {block['label']} "
            f"(strength ratio {block['ratio']:.2f}, rank {block['rank']} of 7)"
        )

    lines = [
        "Career strength is read from three key significators (planets "
        "whose condition speaks to this area of life):",
        _significator_line("10th house lord (your career house's own ruler)", tenth_lord),
        _significator_line("Sun (authority, government, visibility)", sun),
        _significator_line("Saturn (discipline, long-term effort, service)", saturn),
        "",
        f"Overall, {strongest.title()} is your strongest planet and "
        f"{weakest.title()} is your weakest in this chart.",
        f"Your 10th house (career house) itself carries a strength score "
        f"of {bhava_10_rupa:.1f}.",
    ]

    enrichment = payload.get("timing_enrichment")
    if enrichment is not None:
        lines.append("")
        lines.append(_render_timing_enrichment(enrichment))

    return "\n".join(lines)


def _render_marriage(payload: dict) -> str:
    """marriage_compatibility payload keys verbatim from
    result_formatter._format_marriage(): total_score, max_score,
    koota_scores (8 keys, see _KOOTA_LABELS), mangal_dosha
    ({"boy", "girl", "both_have"}), verdict (one of
    _MARRIAGE_VERDICT_LABELS' 4 keys).
    """
    total = payload["total_score"]
    max_score = payload["max_score"]
    verdict = payload["verdict"]
    kootas = payload["koota_scores"]
    mangal = payload["mangal_dosha"]

    verdict_text = _MARRIAGE_VERDICT_LABELS.get(verdict, verdict)

    lines = [
        f"Overall compatibility score: {total:.1f} out of {max_score:.1f} "
        f"— this pairing is {verdict_text}.",
        "",
        "This score is built from 8 traditional Vedic compatibility "
        "factors (Ashtakoot), each scored out of its own maximum:",
    ]
    for key, label in _KOOTA_LABELS.items():
        score = kootas[key]
        lines.append(f"- {label}: {score['score']:.1f} / {score['max']:.1f}")

    lines.append("")
    if mangal["both_have"]:
        lines.append(
            "Mangal Dosha (a specific Mars placement some traditions "
            "weigh heavily for marriage) is present for BOTH partners — "
            "when both charts carry it, many traditions consider it "
            "cancelled out."
        )
    elif mangal["boy"]:
        lines.append(
            "Mangal Dosha (a specific Mars placement some traditions "
            "weigh heavily for marriage) is present in the groom's chart "
            "only."
        )
    elif mangal["girl"]:
        lines.append(
            "Mangal Dosha (a specific Mars placement some traditions "
            "weigh heavily for marriage) is present in the bride's chart "
            "only."
        )
    else:
        lines.append(
            "Mangal Dosha (a specific Mars placement some traditions "
            "weigh heavily for marriage) is not present in either chart."
        )

    return "\n".join(lines)


def _render_arudha_lagna(payload: dict) -> str:
    """arudha_lagna payload keys verbatim from
    result_formatter._format_arudha_lagna(): arudha_sign, lagna_sign,
    lord, co_lord_deciding_step (str | None).
    """
    arudha_sign = payload["arudha_sign"]
    lagna_sign = payload["lagna_sign"]
    lord = payload["lord"]
    co_lord_step = payload["co_lord_deciding_step"]

    lines = [
        f"Your Arudha Lagna (a Jaimini indicator of how your persona and "
        f"public image appear to the outside world) falls in "
        f"{arudha_sign}.",
        f"Your natal Lagna (Ascendant, the sign rising at birth) is "
        f"{lagna_sign}.",
        f"The Arudha Lagna's ruling planet (lord) is {lord.title()}.",
    ]
    if co_lord_step:
        lines.append(
            f"This sign has two traditional rulers (co-lords); the tie "
            f"was resolved via cascade step '{co_lord_step}'."
        )
    return "\n".join(lines)


def _render_upapada_lagna(payload: dict) -> str:
    """upapada_lagna payload keys verbatim from
    result_formatter._format_upapada(): upapada_sign, lagna_sign, lord,
    co_lord_deciding_step (str | None) -- field-for-field identical shape
    to _render_arudha_lagna() above except "upapada_sign" in place of
    "arudha_sign" (matches _format_upapada()'s own documented mirroring
    of _format_arudha_lagna()).
    """
    upapada_sign = payload["upapada_sign"]
    lagna_sign = payload["lagna_sign"]
    lord = payload["lord"]
    co_lord_step = payload["co_lord_deciding_step"]

    lines = [
        f"Your Upapada Lagna (a Jaimini marriage/spouse indicator read "
        f"from your own chart alone) falls in {upapada_sign}.",
        f"Your natal Lagna (Ascendant, the sign rising at birth) is "
        f"{lagna_sign}.",
        f"The Upapada Lagna's ruling planet (lord) is {lord.title()}.",
    ]
    if co_lord_step:
        lines.append(
            f"This sign has two traditional rulers (co-lords); the tie "
            f"was resolved via cascade step '{co_lord_step}'."
        )
    return "\n".join(lines)


def _render_muhurta_window(payload: dict) -> str:
    """muhurta_window payload keys verbatim from
    result_formatter._format_muhurta_window(): windows (list of dicts,
    each {"start", "end", "tier", "favorable_count", "warnings", ...}),
    summary ({"tier1_window_count", "earliest_tier1_start"}).

    Per-window "tier" is muhurta_scorer.MuhurtaTier's value string
    (TIER_1/TIER_2/TIER_3) -- relabeled via _MUHURTA_TIER_LABELS above,
    NEVER confused with this DomainAnswer's own pipeline-level
    AnswerTier.TIER_3_MUHURTA (same distinction result_formatter.py's own
    comments insist on).
    """
    windows = payload["windows"]
    summary = payload["summary"]

    lines = [
        "Here are the auspicious-timing (Muhurta) windows found in the "
        "scanned range:",
        "",
    ]
    for window in windows:
        tier_label = _MUHURTA_TIER_LABELS.get(window["tier"], window["tier"])
        line = f"- {window['start']} to {window['end']}: {tier_label}"
        if window["warnings"]:
            line += f" (notable factors: {', '.join(window['warnings'])})"
        lines.append(line)

    lines.append("")
    tier1_count = summary["tier1_window_count"]
    earliest = summary["earliest_tier1_start"]
    lines.append(
        f"{tier1_count} window(s) rated excellent were found; the "
        f"earliest begins {earliest}."
    )
    return "\n".join(lines)
