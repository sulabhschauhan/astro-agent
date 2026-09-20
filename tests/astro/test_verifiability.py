"""S140 — the standing verifiability ledger. Pure-stdlib, no chart deps."""
from agent.astro import verifiability as V


def _full_stats():
    """A silence-gate `stats` dict shaped like the real S139 emission."""
    return {
        "claims_in": 8,
        "typed_decided": 8,
        "prose_decided": 0,
        "predicate_coverage": {
            "claim_verdicts": {"satisfied": 6, "contradicted": 2, "unevaluable": 0},
            "typed_coverage": 1.0,
        },
        "silences_in": 7,
        "silences_typed": 6,
        "silences_caught_miss": 1,
        "silences_justified": 4,
        "silences_uncheckable": 2,
        "silences_fragile_downgraded": 0,
    }


def test_summarize_full_first_and_second_class():
    L = V.summarize(_full_stats())
    assert L["ledger_version"] == V.LEDGER_VERSION
    c = L["claims"]
    assert c["known"] is True
    assert c["first_class"] == 8      # satisfied + contradicted
    assert c["second_class"] == 0     # unevaluable
    assert L["rates"]["first_class_pct"] == 100.0
    assert L["rates"]["typed_share_pct"] == 100.0
    # P-033 gate = caught_miss / typed silences
    assert L["rates"]["caught_miss_rate_pct"] == round(100 * 1 / 6, 1)


def test_summarize_second_class_counts_unevaluable():
    s = _full_stats()
    s["predicate_coverage"]["claim_verdicts"] = {"satisfied": 5, "contradicted": 1, "unevaluable": 2}
    s["claims_in"] = 8
    L = V.summarize(s)
    assert L["claims"]["first_class"] == 6
    assert L["claims"]["second_class"] == 2
    assert L["rates"]["first_class_pct"] == 75.0
    # uncheckable_rate = (unevaluable 2 + uncheckable silences 2) / (claims 8 + silences 7)
    assert L["rates"]["uncheckable_rate_pct"] == round(100 * 4 / 15, 1)


def test_old_capture_without_predicate_coverage_is_unknown_not_zero():
    """The fail-safe that stops old captures from under-counting the ledger."""
    s = _full_stats()
    del s["predicate_coverage"]
    L = V.summarize(s)
    assert L["claims"]["known"] is False
    assert L["claims"]["first_class"] is None
    assert L["claims"]["second_class"] is None
    assert L["rates"]["first_class_pct"] is None
    assert L["rates"]["uncheckable_rate_pct"] is None
    # silences are still measured on an old-era block
    assert L["silences"]["caught_miss"] == 1
    assert L["rates"]["caught_miss_rate_pct"] == round(100 * 1 / 6, 1)


def test_summarize_empty_and_none_never_crash():
    for arg in (None, {}, {"silences_in": 0}):
        L = V.summarize(arg)
        assert L["claims"]["known"] is False
        assert L["silences"]["in"] == 0
        assert L["rates"]["typed_share_pct"] is None  # 0/0 -> None, never fake 0.0


def test_pct_zero_denominator_is_none():
    assert V._pct(0, 0) is None
    assert V._pct(3, 0) is None
    assert V._pct(1, 4) == 25.0


def test_rollup_excludes_unknown_claims_but_keeps_silences():
    known = V.summarize(_full_stats())
    old = _full_stats(); del old["predicate_coverage"]
    unknown = V.summarize(old)
    agg = V.rollup([known, unknown])
    assert agg["turns"] == 2
    assert agg["turns_claims_known"] == 1
    assert agg["turns_claims_unknown"] == 1
    # claim totals come ONLY from the known turn
    assert agg["first_class"] == 8
    assert agg["claims_total"] == 8
    # silences summed across BOTH turns
    assert agg["sil_in"] == 14
    assert agg["sil_typed"] == 12
    assert agg["sil_caught_miss"] == 2
    assert agg["rates"]["caught_miss_rate_pct"] == round(100 * 2 / 12, 1)


def test_rollup_empty_is_safe():
    agg = V.rollup([])
    assert agg["turns"] == 0
    assert agg["rates"]["first_class_pct"] is None
    assert agg["rates"]["caught_miss_rate_pct"] is None
