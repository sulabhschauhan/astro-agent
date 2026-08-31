"""
agent/interpretive/vocab_adapter.py

S121 adapter #1 (additive only -- see diagnostics/adapter_requirement_ledger_S121.md,
commit 8b33901, for the requirement set this module executes against). A
pure, deterministic value-channel adapter: given a raw vision phrase
reported for one (feature, attribute), resolves it to a canonical
emission_menus token, or reports honestly that it cannot.

NOT WIRED into observation_extractor / palm_reading / palm_processor by
this task. Nothing calls adapt() in production yet -- this module exists so
a later, separate wiring task has a tested, invariant-checked primitive to
call. capture_unmapped() below is likewise a no-op stub for the same
reason -- wiring it to a real sink is a later task.

DESIGN, deliberately narrow (mirrors emission_menus.py's own posture):
  - NO fuzzy matching, NO nearest-neighbor guessing, NO LLM call. A raw
    phrase either already equals a menu token, or is a table-evidenced
    synonym of one, or it is honestly Unmapped. Guessing an unevidenced
    mapping is exactly the "flat pool is the bug" / wrong-map failure mode
    this module exists to prevent (S121 ledger gap classes D3/D5).
  - The synonym table is SCOPED per (feature, attribute), never global.
    "wide" -> "broad" is evidenced ONLY for Line of Heart's Width
    (ledger rule ids HL_013/HL_018/HL_020); Line of Head's Width menu also
    contains "broad", but adapt("Line of Head", "Width", "wide") is
    Unmapped BY DESIGN -- extending an evidenced synonym to a sibling
    (feature, attribute) pair it was never verified against is exactly
    the kind of invented mapping this task was told not to make. See
    tests/interpretive/test_vocab_adapter.py's wrong-map guard test.
  - HARD INVARIANT: every Mapped(token) this module ever returns has
    token IN emission_menus.menu_for(feature, attribute) at the moment of
    return -- enforced in code (_mapped(), below), not just by
    construction, so a future edit to this file cannot silently violate
    it. The synonym table itself is also validated against menu_for() at
    IMPORT time (see the validation loop below) so a drifted table fails
    loudly at load rather than emitting a bad token at call time.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    from agent.interpretive import emission_menus
except Exception as exc:  # noqa: BLE001 -- re-raised immediately, named, not swallowed
    raise RuntimeError(
        "vocab_adapter: failed to load agent.interpretive.emission_menus "
        f"(which itself loads data/ontology_registry.json): {exc}"
    ) from exc


@dataclass(frozen=True)
class Mapped:
    """raw_phrase resolved to a canonical emission_menus token."""

    token: str


@dataclass(frozen=True)
class Unmapped:
    """A real value attempt with no canonical route -- the rule stays
    silent on this observation; nothing is guessed. `reason` is one of
    "attribute unbound" (menu_for returned None -- no menu exists to map
    into at all) or "no canonical route" (a menu exists but neither an
    exact match nor a table-evidenced synonym resolved this raw_phrase)."""

    raw_phrase: str | None
    reason: str


@dataclass(frozen=True)
class NotPerceived:
    """Vision declined to observe this dimension at all (a perception-null
    phrase: "not clearly visible" / "" / "none" / "n/a"), as distinct from
    an observed-but-unmappable value (Unmapped)."""


AdaptResult = Mapped | Unmapped | NotPerceived


_PERCEPTION_NULL_PHRASES = frozenset({"not clearly visible", "", "none", "n/a"})


def _is_perception_null(raw_phrase: str | None) -> bool:
    if raw_phrase is None:
        return True
    return raw_phrase.strip().lower() in _PERCEPTION_NULL_PHRASES


# ─── Synonym table -- D5-class near-misses, one (feature, attribute) key
# per evidenced pair ────────────────────────────────────────────────────
# Seeded from diagnostics/adapter_requirement_ledger_S121.md's D5 gap class
# (commit 8b33901, ledger rows 47-53 -- 7 gap units / 10 antecedent
# instances). Cross-checked against emission_menus.normalization_worklist()
# entries directly below each key so drift between the two is visible at a
# glance, not just at the import-time assertion further down.
#
# H_004's and H_020's Direction->Slope worklist entries ('straight'->
# 'straight', fix_type=attribute_migration, no value change) are NOT
# reproduced here: 'straight' already equals a Slope menu token verbatim,
# so adapt() resolves it via the exact-match step with no synonym-table
# entry needed at all -- adding one would be redundant, not wrong, but
# this table only carries entries that do real work.
_SYNONYM_TABLE: dict[tuple[str, str], dict[str, str]] = {
    ("Line of Fate", "Depth"): {
        "well_marked": "deep",  # normalization_worklist: FT_001
    },
    ("Line of Head", "Depth"): {
        "well_marked": "deep",  # normalization_worklist: FT_009
    },
    ("Line of Head", "Continuity"): {
        "clear": "unbroken",  # normalization_worklist: H_004 (value_normalization half)
    },
    ("Line of Head", "Slope"): {
        "sloping": "downward",  # normalization_worklist: H_018, H_019 (Direction->Slope migration)
    },
    ("Line of Heart", "Slope"): {
        "drooping": "downward",  # normalization_worklist: HL_012 (Direction->Slope migration)
    },
    ("Line of Heart", "Width"): {
        "thin": "narrow",  # normalization_worklist: HL_014
        "wide": "broad",  # normalization_worklist: HL_013, HL_018, HL_020
    },
}

# Verified-empty (see module comment above the table): a fresh read of
# diagnostics/adapter_requirement_ledger_S121.md's D5 rows at commit
# 8b33901 found no gap unit outside _SYNONYM_TABLE above -- every D5 row
# is already covered by a normalization_worklist entry. Kept as an
# explicit, documented placeholder (rather than omitted) so a future
# ledger revision that DOES surface a new near-miss has an obvious place
# to add it, with its own inline source note -- never invented ahead of
# evidence.
_EXTRA_SYNONYMS: dict[tuple[str, str], dict[str, str]] = {}

_FULL_SYNONYM_TABLE: dict[tuple[str, str], dict[str, str]] = {
    key: {**_SYNONYM_TABLE.get(key, {}), **_EXTRA_SYNONYMS.get(key, {})}
    for key in set(_SYNONYM_TABLE) | set(_EXTRA_SYNONYMS)
}

# Fail-closed sanity check at import time (mirrors contact_mapper.py's own
# verb-table-vs-registry check): every synonym-table target token must
# itself be a real member of its own menu, or the table is malformed --
# catches drift immediately rather than emitting a bad token at call time.
for _feature, _attribute in _FULL_SYNONYM_TABLE:
    _menu = emission_menus.menu_for(_feature, _attribute)
    if _menu is None:
        raise RuntimeError(
            f"vocab_adapter: synonym table has an entry for ({_feature!r}, "
            f"{_attribute!r}), but that (feature, attribute) has no bound "
            "emission_menus menu at all -- fix the table or the registry."
        )
    _bad_targets = {v for v in _FULL_SYNONYM_TABLE[(_feature, _attribute)].values() if v not in _menu}
    if _bad_targets:
        raise RuntimeError(
            f"vocab_adapter: synonym table for ({_feature!r}, {_attribute!r}) "
            f"maps to token(s) {sorted(_bad_targets)} not present in "
            f"menu_for(...) = {_menu!r} -- fix the table."
        )
del _feature, _attribute, _menu, _bad_targets


def _mapped(token: str, menu: tuple[str, ...], feature: str, attribute: str) -> Mapped:
    """The ONLY place a Mapped() is ever constructed -- enforces the hard
    invariant (module docstring) at the return boundary itself, not just
    by construction, so a future edit elsewhere in this file cannot
    silently emit a non-canonical token."""
    if token not in menu:
        raise RuntimeError(
            "vocab_adapter internal invariant violation: about to return "
            f"Mapped({token!r}) for ({feature!r}, {attribute!r}) but "
            f"{token!r} is not a member of menu_for(...) = {menu!r}."
        )
    return Mapped(token=token)


def capture_unmapped(record: dict) -> None:
    """No-op stub. Wiring this to a real sink (log line, capture-net file,
    telemetry) is a LATER, separate task -- this task is additive only and
    wires nothing into production. Kept as a module-level function (not a
    private helper) so that later task can monkeypatch/replace it without
    touching adapt()'s body."""
    return None


def _unmapped(feature: str, attribute: str, raw_phrase: str | None, reason: str) -> Unmapped:
    capture_unmapped({
        "feature": feature,
        "attribute": attribute,
        "raw_phrase": raw_phrase,
        "reason": reason,
    })
    return Unmapped(raw_phrase=raw_phrase, reason=reason)


def adapt(feature: str, attribute: str, raw_phrase: str | None) -> AdaptResult:
    """Resolves one raw vision phrase for (feature, attribute) to a
    canonical emission_menus token, or reports honestly that it cannot.

    Order (module docstring governs the no-guessing discipline behind it):
      1. perception-null raw_phrase -> NotPerceived.
      2. attribute unbound (menu_for returns None) -> Unmapped("attribute
         unbound") -- no fallback to the flat registry value pool.
      3. raw_phrase already equals a menu token (whitespace-insensitive
         only, no case-folding) -> Mapped.
      4. normalized (stripped + lowercased) raw_phrase resolves through
         the (feature, attribute)-scoped synonym table to a token that is
         itself a menu member -> Mapped.
      5. else -> Unmapped("no canonical route").
    """
    if _is_perception_null(raw_phrase):
        return NotPerceived()

    menu = emission_menus.menu_for(feature, attribute)
    if menu is None:
        return _unmapped(feature, attribute, raw_phrase, "attribute unbound")

    stripped = raw_phrase.strip()
    if stripped in menu:
        return _mapped(stripped, menu, feature, attribute)

    normalized = stripped.lower()
    candidate = _FULL_SYNONYM_TABLE.get((feature, attribute), {}).get(normalized)
    if candidate is not None:
        return _mapped(candidate, menu, feature, attribute)

    return _unmapped(feature, attribute, raw_phrase, "no canonical route")
