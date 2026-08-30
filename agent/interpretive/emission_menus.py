"""
agent/interpretive/emission_menus.py

THE single accessor over data/ontology_registry.json's `emission_menus`
block (S121 plan item #2a). Outside-in spine: the vision prompt (#2b-ii),
the extractor guard/parse (#2c), and the CI reachability gate (#3) are all
meant to read closed emission menus through THIS module and nowhere else --
no second, independently-authored copy of any menu.

ADDITIVE ONLY. This task creates the module and its tests; nothing in the
codebase imports or calls it yet. `agent/palm_processor.py`'s vision-prompt
menus and `agent/interpretive/observation_extractor.py`'s
`attribute_value_binding` guard remain exactly as they were -- this module
does not touch, derive from, or get derived by either yet.

Design, deliberately narrow:
  - NO alias logic. The forced-list/no-alias design (S121, ratified) means
    there is no synonym-collapse mechanism here or anywhere -- a rule keyed
    on a non-menu token is wrong and must be corrected at the SOURCE (see
    `normalization_worklist()`), never silently mapped around at read time.
  - NO flat-pool fallback. An attribute the registry's `emission_menus`
    does not bind for a given feature is UNBOUND -- `menu_for` returns
    `None`, never `ontology_registry.json`'s `values` flat pools. Falling
    back to the flat pool for an unbound attribute is the exact "flat pool
    is the bug" failure mode the whole #2 series exists to retire (see
    `diagnostics/latest_run.md`'s S121 2a report, and
    `observation_extractor.py::_values_for_attribute`'s own docstring,
    which is the CURRENT flat-pool-fallback mechanism this module is
    designed to eventually replace -- not this task).
  - `is_unbound(feature, attribute)` is exactly `menu_for(feature,
    attribute) is None` -- this accessor is a thin, pure reader; it does
    not attempt to distinguish "deliberately parked pending a human ruling"
    (the registry's `unbound` section) from "this (feature, attribute)
    combination was simply never authored" (e.g. `Mount of Venus`.`Depth`,
    which is not a real combination at all). Both read as "no bound menu
    exists," which is all a caller needs to know to avoid inventing a
    fallback.
"""
from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "ontology_registry.json"
)

# Keys at the top of the registry's `emission_menus` block that are NOT
# feature names -- annotation/spec blocks, not per-(feature, attribute)
# menu data. Everything else under `emission_menus` is a feature name
# whose value is {attribute: {"menu": [...], ...}}.
_NON_FEATURE_KEYS = frozenset({"_meta", "normalization_worklist", "_mounts_note", "unbound"})


def _load_emission_menus(registry_path: Path = _DEFAULT_REGISTRY_PATH) -> dict:
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
        return registry["emission_menus"]
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"emission_menus: ontology registry not found at {registry_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"emission_menus: {registry_path} is not valid JSON: {exc}"
        ) from exc
    except KeyError as exc:
        raise RuntimeError(
            f"emission_menus: {registry_path} has no top-level 'emission_menus' key "
            "-- expected S121 plan item #2a to have added one"
        ) from exc


# Module-level cache -- the registry is read from disk exactly once, at
# import time, same convention as observation_extractor.py's `_REGISTRY`.
_EMISSION_MENUS: dict = _load_emission_menus()


def _build_menu_cache(emission_menus: dict) -> dict[str, dict[str, tuple[str, ...]]]:
    """{feature: {attribute: (token, ...)}}, built once from the raw
    registry block -- every feature key except the reserved
    `_NON_FEATURE_KEYS` ones, every attribute entry that carries a "menu"
    list."""
    cache: dict[str, dict[str, tuple[str, ...]]] = {}
    for feature, attrs in emission_menus.items():
        if feature in _NON_FEATURE_KEYS:
            continue
        cache[feature] = {
            attribute: tuple(spec["menu"])
            for attribute, spec in attrs.items()
            if isinstance(spec, dict) and "menu" in spec
        }
    return cache


_MENU_CACHE: dict[str, dict[str, tuple[str, ...]]] = _build_menu_cache(_EMISSION_MENUS)


def menu_for(feature: str, attribute: str) -> tuple[str, ...] | None:
    """The closed tuple of legal tokens for `(feature, attribute)`, or
    `None` if that combination is UNBOUND -- no menu is authored for it
    (whether explicitly parked under the registry's `unbound` section, or
    simply never authored at all). Never falls back to the flat
    `values` pools."""
    return _MENU_CACHE.get(feature, {}).get(attribute)


def all_menus() -> dict[str, dict[str, tuple[str, ...]]]:
    """The full {feature: {attribute: (token, ...)}} map, one shallow copy
    per call (the inner tuples are already immutable and shared; only the
    dict structure is copied, so a caller mutating the returned dicts
    cannot corrupt the module cache)."""
    return {feature: dict(attrs) for feature, attrs in _MENU_CACHE.items()}


def is_unbound(feature: str, attribute: str) -> bool:
    """True iff no bound menu exists for `(feature, attribute)` -- exactly
    `menu_for(feature, attribute) is None`. See module docstring: this
    does not distinguish a deliberately-parked-pending-ruling attribute
    from a combination that was simply never authored."""
    return menu_for(feature, attribute) is None


def normalization_worklist() -> tuple[dict, ...]:
    """The committed rule-id -> canonical-token rewrite spec (S121 #2a's
    `emission_menus.normalization_worklist.entries`) -- task #5 reads its
    rewrite spec from HERE, not from chat history. Returns the 14 entry
    dicts verbatim (each: rule_id, feature, attribute, from, to, fix_type,
    optionally to_attribute/note) -- does NOT include the separate
    `out_of_scope_untouched` list, which documents rules deliberately left
    alone (comparative Depth, parked granularity tokens, unbound Clarity),
    not rewrites to apply."""
    return tuple(_EMISSION_MENUS["normalization_worklist"]["entries"])
