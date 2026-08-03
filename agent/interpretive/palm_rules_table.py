"""
agent/interpretive/palm_rules_table.py
Deterministic rule-matching engine for the offline-verified-extraction
pilot -- SUPERSEDES the small hand-authored schema this module carried
before (backed up verbatim to palm_rules_table.py.bak). This rewrite
loads Sulabh's real validated rule set (data/palm_rules/palm_rules_head_heart_v1.json,
`validated_candidates` only -- `parked_pending_relation_target` rules are
schema-blocked, per that file's own schema_flags, and are never loaded
here) and matches it against an observation graph.

Four layers, in order:
  1. load_rules() -- pure I/O + shape validation for a SINGLE rule-book
     file, no matching logic.
  2. load_rule_set() -- merges every top-level rule-book file under
     data/palm_rules/ (non-recursive; data/palm_rules/_candidates/ drafts
     are never auto-loaded), fail-closed on cross-file rule_id collisions.
  3. match() -- fires rules whose antecedents are ALL satisfied by the
     observation (+ magnitudes, for comparative antecedents). Independent
     per rule; does not know about topic_group or suppression.
  4. resolve_priority() -- takes the fired set and suppresses any rule
     that is a strict antecedent-subset of another FIRED rule in the SAME
     topic_group (most_specific_wins, matching
     data/palm_rules/_candidates/deterministic_rule_book.json's own
     engine_priority doctrine: "resolution_strategy": "most_specific_wins",
     "scope": "within_topic_group").

SCHEMA NOTE: `logic_join` exists in the source JSON (always "AND" across
all 43 validated_candidates) but is NOT one of the fields this task's own
PalmRule schema lists. Per that literal field list, it is dropped, not
silently carried through as an extra attribute -- match() hardcodes
AND-of-all-antecedents rather than branching on a stored field, which is
equivalent for this dataset (100% AND) but would need revisiting if a
non-AND rule is ever authored.

Does NOT emit Claim objects, does NOT touch claim_voicing.py -- that
wiring is a later prompt. NOT wired into palm_reading.py.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

logger = logging.getLogger(__name__)

_DEFAULT_RULES_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "palm_rules" / "palm_rules_head_heart_v1.json"
)

# Directory of top-level rule-book JSON files -- load_rule_set() globs this
# directory ONLY (non-recursive), so data/palm_rules/_candidates/ (unratified
# drafts like deterministic_rule_book.json) is never picked up automatically.
_DEFAULT_RULES_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "palm_rules"

# The 6 antecedent fields this task's schema specifies. Any OTHER key
# present on a raw antecedent dict (e.g. H_011's "hand_side": "both") is
# silently dropped when building an Antecedent -- not an error, just out
# of this schema's scope; see the module's own report for the one
# concrete instance this drops in the current data (H_011).
_ANTECEDENT_FIELDS = ("feature", "attribute", "value", "condition_type", "comparator", "comparator_feature")


@dataclass(frozen=True)
class Antecedent:
    feature: str
    attribute: str
    value: str | None
    condition_type: str
    comparator: str | None
    comparator_feature: str | None

    def signature(self) -> tuple:
        """Hashable identity used for antecedent-SET comparison in
        resolve_priority() -- two antecedents are "the same condition"
        only if every field matches, so a comparative antecedent (value
        is always None) is never confused with a standard one."""
        return (self.feature, self.attribute, self.value, self.condition_type, self.comparator, self.comparator_feature)


@dataclass(frozen=True)
class PalmRule:
    rule_id: str
    source_page: int
    topic_group: str
    is_compound: bool
    antecedents: tuple[Antecedent, ...]
    claim: str
    source_quote: str
    verified: bool
    verifier: str | None
    verified_date: str | None
    source_fidelity: str | None
    schema_flags: tuple[str, ...]
    baseline: bool = False

    def antecedent_set(self) -> frozenset:
        return frozenset(a.signature() for a in self.antecedents)


def _build_antecedent(raw: dict) -> Antecedent:
    return Antecedent(**{k: raw.get(k) for k in _ANTECEDENT_FIELDS})


def load_rules(path: Path | str = _DEFAULT_RULES_PATH) -> tuple[PalmRule, ...]:
    """Reads `validated_candidates` ONLY from the given rule file --
    `parked_pending_relation_target` entries are never loaded here (their
    own schema_flags document why: missing relation-target machinery this
    engine doesn't have yet). Builds a PalmRule per candidate, regardless
    of that candidate's own `verified` value -- match() is what actually
    enforces verified==True at match time (fail-closed skip, not raise);
    the loader's job is only to log a WARNING with the unverified count so
    a stale/incomplete verification pass is visible, never to crash.

    Raises:
        FileNotFoundError / json.JSONDecodeError: propagated as-is --
        a missing or malformed rule file is a genuinely fatal condition
        for this module, not a per-rule fail-closed case.
    """
    import json

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    candidates = raw.get("validated_candidates", [])

    unverified_count = sum(1 for c in candidates if c.get("verified") is not True)
    if unverified_count:
        logger.warning(
            "palm_rules_table.load_rules: %d of %d validated_candidates in %s "
            "are NOT yet verified==true -- they will load but match() will "
            "skip them at match time until Sulabh flips them.",
            unverified_count, len(candidates), path,
        )

    rules = []
    for c in candidates:
        antecedents = tuple(_build_antecedent(a) for a in c.get("antecedents", []))
        rules.append(PalmRule(
            rule_id=c["rule_id"],
            source_page=c["source_page"],
            topic_group=c["topic_group"],
            is_compound=c["is_compound"],
            antecedents=antecedents,
            claim=c["claim"],
            source_quote=c["source_quote"],
            verified=c.get("verified", False),
            verifier=c.get("verifier"),
            verified_date=c.get("verified_date"),
            source_fidelity=c.get("source_fidelity"),
            schema_flags=tuple(c.get("schema_flags", [])),
            baseline=c.get("baseline", False),
        ))
    return tuple(rules)


def load_rule_set(rules_dir: Path | str = _DEFAULT_RULES_DIR) -> tuple[PalmRule, ...]:
    """Loads and merges every top-level rule-book JSON file in `rules_dir`
    (non-recursive glob -- `_candidates/` subdirectories, e.g. the
    unratified deterministic_rule_book.json draft, are never picked up).
    Each file goes through the SAME load_rules() used for a single file --
    no separate parsing path -- so a malformed file still raises exactly
    as load_rules() documents (propagated, not swallowed here).

    Fail-closed on cross-file rule_id collisions: two files are allowed to
    each define their own ids freely, but if the SAME rule_id appears in
    two different files, that's a genuine authoring error (which rule
    fires?) -- raised immediately, naming the id and both files, rather
    than silently keeping one and dropping the other.

    Raises:
        ValueError: `rules_dir` doesn't exist, or a duplicate rule_id is
        found across files (message names the dir / the id and files).
        FileNotFoundError / json.JSONDecodeError: propagated as-is from
        load_rules() for a malformed individual file -- not caught here.
    """
    rules_dir = Path(rules_dir)
    if not rules_dir.is_dir():
        raise ValueError(f"palm_rules_table.load_rule_set: rules_dir does not exist or is not a directory: {rules_dir}")

    all_rules: list[PalmRule] = []
    seen_by_id: dict[str, Path] = {}
    for file_path in sorted(rules_dir.glob("*.json")):
        file_rules = load_rules(file_path)
        for rule in file_rules:
            if rule.rule_id in seen_by_id:
                raise ValueError(
                    f"palm_rules_table.load_rule_set: duplicate rule_id {rule.rule_id!r} "
                    f"found in both {seen_by_id[rule.rule_id]} and {file_path}"
                )
            seen_by_id[rule.rule_id] = file_path
        all_rules.extend(file_rules)

    return tuple(all_rules)


def _antecedent_fires(antecedent: Antecedent, observation: dict, magnitudes: dict) -> bool:
    if antecedent.condition_type == "comparative":
        feature_mags = magnitudes.get(antecedent.feature)
        other_mags = magnitudes.get(antecedent.comparator_feature)
        if feature_mags is None or other_mags is None:
            return False
        a = feature_mags.get(antecedent.attribute)
        b = other_mags.get(antecedent.attribute)
        if a is None or b is None:
            return False
        if antecedent.comparator == ">":
            return a > b
        if antecedent.comparator == "<":
            return a < b
        if antecedent.comparator == "=":
            return a == b
        return False
    # standard (or any other condition_type): plain equality lookup.
    # Unknown feature/attribute -> .get(...) chain returns None, which
    # never equals a real value string -- fails silently, no raise.
    return observation.get(antecedent.feature, {}).get(antecedent.attribute) == antecedent.value


def match(
    observation: dict[str, dict[str, str]],
    magnitudes: dict[str, dict[str, object]],
    rules: Sequence[PalmRule],
) -> list[PalmRule]:
    """Returns the FIRED set (pre-priority) -- every verified rule whose
    antecedents ALL fire against `observation`/`magnitudes`. Unverified
    rules are skipped here (fail-closed, no exception) -- this is where
    the loader's "may load unverified" contract actually gets enforced."""
    fired = []
    for rule in rules:
        if rule.verified is not True:
            continue
        if rule.antecedents and all(_antecedent_fires(a, observation, magnitudes) for a in rule.antecedents):
            fired.append(rule)
    return fired


def resolve_priority(fired: Sequence[PalmRule]) -> tuple[list[PalmRule], list[tuple[str, str]]]:
    """Returns (survivors, suppression_log). suppression_log is a list of
    (survivor_id, suppressed_id) pairs, one per suppression, for
    auditing (per the instructing prompt's own tuning note).

    Suppression rule: within the same topic_group, a fired rule is
    suppressed if its antecedent_set() is a PROPER subset of another
    FIRED rule's antecedent_set() in that same group (most_specific_wins,
    matching data/palm_rules/_candidates/deterministic_rule_book.json's
    engine_priority doctrine -- same formal spec, independently re-derived
    here for this engine).
    Cross-group rules never suppress each other. Rules with equal
    antecedent-set size (including identical sets) never suppress one
    another -- "benign siblings", same exemption as that doctrine's own
    text.
    """
    by_group: dict[str, list[PalmRule]] = defaultdict(list)
    for r in fired:
        by_group[r.topic_group].append(r)

    suppressed_ids: set[str] = set()
    suppression_log: list[tuple[str, str]] = []
    for group_rules in by_group.values():
        for r_i in group_rules:
            set_i = r_i.antecedent_set()
            for r_j in group_rules:
                if r_i.rule_id == r_j.rule_id:
                    continue
                set_j = r_j.antecedent_set()
                if set_i < set_j:  # proper subset
                    if r_i.rule_id not in suppressed_ids:
                        suppressed_ids.add(r_i.rule_id)
                        suppression_log.append((r_j.rule_id, r_i.rule_id))
                    break

    survivors = [r for r in fired if r.rule_id not in suppressed_ids]
    return survivors, suppression_log
