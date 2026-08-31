"""
agent/interpretive/provenance.py

Structured rule-provenance parser + the G1-G8 consistency checks (S121
governance #1). Replaces the free-string `schema_flags: [str]` convention
with typed, machine-checkable structures -- see the S121 provenance
census (diagnostics/latest_run.md) for the classification (A token-coupled
/ B status / C doctrine caveat / D prose) this schema is derived from.

ADDITIVE ONLY. This task creates the module and its tests; NOTHING in the
codebase imports or calls it yet, no rule file carries a `provenance` key
yet, and no CI gate runs these checks yet. Wiring, rule migration, and
baseline capture are separate, later steps.

=== WHY THIS EXISTS (the failure it makes mechanical) ===

The census found 5 HARD-STALE flags -- prose that asserts a binding the
rule's antecedent no longer carries:

  FT_001[0] / FT_009[0]  say "mapped to Depth=well_marked"; the antecedent
                         has been `Depth = deep` since e982a92 (S121 #5A)
  FT_007[0] / FT_008[0]  say "termination attribute Ending_Point->Position";
                         the antecedents moved to typed `stopped_by` at S112
  L_026[1]               says "against set-valued Convergence"; all three
                         antecedents moved to `joins_at_origin` at S99

Every one of those is a plain string-equality failure that no existing
gate can see. Critically, the reachability scan CANNOT see it either:
`classify_antecedent("Line of Fate", "Depth", "well_marked", None)`
returns status "yes", because `well_marked` is still a legal member of
the flat `depth_values` pool. It is not a DANGLING token, it is a WRONG
one -- registry-legal, but not what the rule fires on, and (per the
emission menus) not emittable either. G1 is the only check in the
codebase that would catch it.

The generalisable root cause, from the census:

    A migration note written as a PRESENT-TENSE BINDING ("mapped to X",
    "the attribute is Position") goes stale the instant the token moves.
    A note written as NARRATIVE PAST with both endpoints ("was X -> now Y")
    stays true forever.

Prose cannot enforce that distinction. The `superseded[]` ledger plus G1
and G3 make the failing shape unrepresentable: G1 pins the binding to the
live antecedent, G3 forbids a supersession record from naming the live
token, so a half-applied migration fails loudly instead of silently.

=== DESIGN NOTES ===

  - PURE. No I/O beyond reading the ontology registry (cached at import,
    same convention as emission_menus.py / observation_extractor.py) and
    the two `git ls-files` calls G7 needs. No LLM, no network, no writes.
    Every check is a function of (rule, provenance) returning a list of
    violation strings; empty list == pass. Nothing raises on a violation.

  - ORACLES ARE IMPORTED, NEVER REIMPLEMENTED. G5 uses
    `scripts.gate_rule_citations.normalize` (the same whitespace/OCR
    normalisation that gate already applies to authored quotes -- S119
    INVARIANT 2's authenticity discipline, reused rather than forked).
    G6 uses `scripts.vocab_reachability_scan.classify_antecedent` as its
    reachability oracle. Both are injectable (see the `normalize_fn` /
    `oracle` parameters) so tests can exercise the check logic without
    monkeypatching a module global -- the default is always the real one.

    DEPENDENCY DIRECTION, flagged not hidden: this is the FIRST module
    under agent/ to import from scripts/. That is deliberate and narrow --
    provenance.py is a validator, not a runtime interpretation path, and
    nothing in the live reading pipeline imports it. If a future change
    ever puts this module on the serve-time path, that import direction
    must be revisited (relocate the two helpers to a shared leaf module)
    rather than silently accepted.

  - ABSENT `provenance` KEY IS VALID. `parse_provenance` returns None,
    and `validate_rule` returns no violations. 41 of the 102 flag-bearing
    rules hold an empty `schema_flags: []` today; those must migrate to
    an ABSENT provenance key, never a populated skeleton -- a skeleton
    would make "never assessed" indistinguishable from "assessed, and the
    answer is unset", which is the exact ambiguity this schema removes.

  - MALFORMED provenance RAISES `ProvenanceError`. A violation means "the
    rule is inconsistent"; a raise means "this structure is not
    provenance at all". Those are different failures and are not
    collapsed into one channel.

  - G9 IS NOT HERE. The advisory prose check (no registry token may
    appear in a class-D `notes` entry) belongs to the enforcement step,
    per the census: it is promoted to hard only after the 10 existing
    class-D notes are measured clean.
"""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from scripts.gate_rule_citations import normalize as _gate_normalize
from scripts.vocab_reachability_scan import classify_antecedent as _reachability_oracle

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_REGISTRY_PATH = _REPO_ROOT / "data" / "ontology_registry.json"


class ProvenanceError(ValueError):
    """Raised when a `provenance` block is structurally malformed -- i.e.
    it is not provenance at all. Distinct from a CHECK VIOLATION, which is
    returned as a string and never raised."""


# ─── closed vocabularies ────────────────────────────────────────────────
# Every one of these is closed by design. A value outside the set is a
# ProvenanceError, not a silently-tolerated extension: an open vocabulary
# here would let a typo'd `bound_field` skip G1 entirely, which is the
# whole check.

BOUND_FIELDS = frozenset({"attribute", "value", "relation_target", "location"})

BINDING_KINDS = frozenset({"literal", "proxy", "computed", "template"})

REACHABILITY_STATES = frozenset({"pass", "fail", "unemittable", "unchecked", "interpreted"})

VISION_EMISSION_STATES = frozenset({"unproven", "confirmed", "refuted"})

CAVEAT_KINDS = frozenset(
    {
        "proxy_mapping",
        "shared_sentence",
        "cross_chapter",
        "quote_spans_pages",
        "ocr_artifact",
        "no_base_row",
        "base_meaning_disjunction",
        "unrepresented_precondition",
        "schema_limitation",
        "coined_doctrine_id",
        "omitted_detail",
    }
)

# Reachability states that contradict `fireable: true` (G6).
_UNFIREABLE_REACHABILITY = frozenset({"fail", "unemittable"})

# vocab_reachability_scan.classify_antecedent's own status vocabulary,
# mapped onto this module's `reachability` vocabulary. The oracle owns the
# verdict; this map only renames it. "INTERPRETED-TERM" is deliberately
# NOT folded into "fail": per the S95 laws it means "compute the term and
# feed it" (a COMPUTED-TERM, law (c)), which is a wiring obligation, not
# an unreachable token.
_ORACLE_STATUS_TO_REACHABILITY = {
    "yes": "pass",
    "NO": "fail",
    "UNEMITTABLE": "unemittable",
    "INTERPRETED-TERM": "interpreted",
}

# G8: the closed set of blocker kinds, each mapped to the registry
# collection whose ABSENCE the blocker asserts. Every kind is
# registry-backed on purpose -- a kind with no registry to check against
# would be an unfalsifiable blocker. (H_011's `hand_side` blocker is
# expressed as `ontology:attribute:hand_side`, which validates correctly:
# `hand_side` is genuinely absent from the attributes registry.)
BLOCKER_KINDS = frozenset({"feature", "attribute", "value", "relation_target"})

_BLOCKER_PREFIX = "ontology:"


# ─── typed structures ───────────────────────────────────────────────────


@dataclass(frozen=True)
class SupersededBinding:
    """One entry in a token_binding's append-only migration ledger: a
    token this binding USED to name, and the authority that retired it."""

    chosen_token: str
    attribute: str | None = None
    authority: str | None = None
    reason: str | None = None


@dataclass(frozen=True)
class TokenBinding:
    """CLASS A. Binds one antecedent field to the token the rule actually
    fires on, plus the source phrase that token stands in for."""

    antecedent_index: int
    bound_field: str
    chosen_token: str
    attribute: str | None = None
    binding_kind: str = "literal"
    source_phrase: str | None = None
    authority: str | None = None
    superseded: tuple[SupersededBinding, ...] = ()


@dataclass(frozen=True)
class ProvenanceStatus:
    """CLASS B. Verification / fireability state, structured."""

    fireable: bool | None = None
    reachability: str | None = None
    reachability_authority: str | None = None
    vision_emission: str = "unproven"
    vision_evidence: str | None = None
    blocked_on: tuple[str, ...] = ()


@dataclass(frozen=True)
class Caveat:
    """CLASS C. Doctrine / source-fidelity caveat: a closed kind plus the
    irreducible human note, and the ruling that settled it if any."""

    kind: str
    note: str
    human_ruling: str | None = None


@dataclass(frozen=True)
class Provenance:
    token_bindings: tuple[TokenBinding, ...] = ()
    status: ProvenanceStatus | None = None
    caveats: tuple[Caveat, ...] = ()
    notes: tuple[str, ...] = ()


# ─── registry access (cached at import, same convention as siblings) ────


def _load_registry(registry_path: Path = _DEFAULT_REGISTRY_PATH) -> dict:
    try:
        return json.loads(registry_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"provenance: ontology registry not found at {registry_path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"provenance: {registry_path} is not valid JSON: {exc}"
        ) from exc


_REGISTRY = _load_registry()


def _registry_tokens(kind: str, registry: dict) -> frozenset[str]:
    """The flat token set a G8 blocker of `kind` asserts absence from.

    Each is a UNION across the registry's own grouping, because a blocker
    says "this token exists NOWHERE", not "not in this one category" --
    e.g. `Depth` lives under `line_attributes`, but a blocker naming it
    must fail regardless of which group holds it."""
    try:
        if kind == "feature":
            return frozenset(
                name for group in registry["features"].values() for name in group
            )
        if kind == "attribute":
            return frozenset(
                name for group in registry["attributes"].values() for name in group
            )
        if kind == "value":
            return frozenset(
                token for pool in registry["values"].values() for token in pool
            )
        if kind == "relation_target":
            return frozenset(registry["relation_target_registry"])
    except (KeyError, AttributeError, TypeError) as exc:
        raise RuntimeError(
            f"provenance: ontology registry is missing or malformed for blocker kind {kind!r}: {exc}"
        ) from exc
    raise ProvenanceError(
        f"unknown blocker kind {kind!r} -- expected one of {sorted(BLOCKER_KINDS)}"
    )


# ─── git-tracking oracle (G7) ───────────────────────────────────────────


def is_git_tracked(path: str | Path, repo_root: Path = _REPO_ROOT) -> bool:
    """True iff `path` is tracked by git in `repo_root`.

    Working Style #16: an uncommitted probe cannot be audited, so evidence
    that exists only in the working tree does not count. This is exactly
    M_001's situation today -- `diagnostics/venus_grade_probe_S119_raw.json`
    shows 6/6 confirmed Venus emission across two hands, but the file is
    untracked, so the flag cannot yet be closed on it.

    Returns False (never raises) when git is absent or the call fails --
    a missing git toolchain must not turn a provenance check into a hard
    error; it degrades to "cannot confirm tracked", which is the
    conservative direction."""
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "--", str(path)],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


# ─── parsing ────────────────────────────────────────────────────────────


def _require_dict(obj: object, what: str) -> dict:
    if not isinstance(obj, dict):
        raise ProvenanceError(f"{what} must be an object, got {type(obj).__name__}")
    return obj


def _require_str(obj: object, what: str) -> str:
    if not isinstance(obj, str) or not obj:
        raise ProvenanceError(f"{what} must be a non-empty string, got {obj!r}")
    return obj


def _optional_str(obj: object, what: str) -> str | None:
    if obj is None:
        return None
    if not isinstance(obj, str):
        raise ProvenanceError(f"{what} must be a string or null, got {obj!r}")
    return obj


def _require_in(value: str, allowed: frozenset[str], what: str) -> str:
    if value not in allowed:
        raise ProvenanceError(
            f"{what} must be one of {sorted(allowed)}, got {value!r}"
        )
    return value


def _parse_superseded(raw: object, where: str) -> tuple[SupersededBinding, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise ProvenanceError(f"{where}.superseded must be an array, got {type(raw).__name__}")
    out = []
    for i, entry in enumerate(raw):
        entry = _require_dict(entry, f"{where}.superseded[{i}]")
        out.append(
            SupersededBinding(
                chosen_token=_require_str(
                    entry.get("chosen_token"), f"{where}.superseded[{i}].chosen_token"
                ),
                attribute=_optional_str(
                    entry.get("attribute"), f"{where}.superseded[{i}].attribute"
                ),
                authority=_optional_str(
                    entry.get("authority"), f"{where}.superseded[{i}].authority"
                ),
                reason=_optional_str(entry.get("reason"), f"{where}.superseded[{i}].reason"),
            )
        )
    return tuple(out)


def _parse_token_binding(raw: object, index: int) -> TokenBinding:
    where = f"provenance.token_bindings[{index}]"
    raw = _require_dict(raw, where)

    antecedent_index = raw.get("antecedent_index")
    # bool is an int subclass in Python -- reject it explicitly, or
    # `antecedent_index: true` would silently resolve to antecedents[1].
    if not isinstance(antecedent_index, int) or isinstance(antecedent_index, bool):
        raise ProvenanceError(
            f"{where}.antecedent_index must be an integer, got {antecedent_index!r}"
        )

    bound_field = _require_in(
        _require_str(raw.get("bound_field"), f"{where}.bound_field"),
        BOUND_FIELDS,
        f"{where}.bound_field",
    )
    binding_kind = _require_in(
        _require_str(raw.get("binding_kind", "literal"), f"{where}.binding_kind"),
        BINDING_KINDS,
        f"{where}.binding_kind",
    )
    return TokenBinding(
        antecedent_index=antecedent_index,
        bound_field=bound_field,
        chosen_token=_require_str(raw.get("chosen_token"), f"{where}.chosen_token"),
        attribute=_optional_str(raw.get("attribute"), f"{where}.attribute"),
        binding_kind=binding_kind,
        source_phrase=_optional_str(raw.get("source_phrase"), f"{where}.source_phrase"),
        authority=_optional_str(raw.get("authority"), f"{where}.authority"),
        superseded=_parse_superseded(raw.get("superseded"), where),
    )


def _parse_status(raw: object) -> ProvenanceStatus:
    where = "provenance.status"
    raw = _require_dict(raw, where)

    fireable = raw.get("fireable")
    if fireable is not None and not isinstance(fireable, bool):
        raise ProvenanceError(f"{where}.fireable must be a boolean or null, got {fireable!r}")

    reachability = _optional_str(raw.get("reachability"), f"{where}.reachability")
    if reachability is not None:
        _require_in(reachability, REACHABILITY_STATES, f"{where}.reachability")

    vision_emission = _require_in(
        _require_str(raw.get("vision_emission", "unproven"), f"{where}.vision_emission"),
        VISION_EMISSION_STATES,
        f"{where}.vision_emission",
    )

    blocked_on = raw.get("blocked_on") or []
    if not isinstance(blocked_on, list):
        raise ProvenanceError(f"{where}.blocked_on must be an array, got {type(blocked_on).__name__}")
    for i, blocker in enumerate(blocked_on):
        _require_str(blocker, f"{where}.blocked_on[{i}]")

    return ProvenanceStatus(
        fireable=fireable,
        reachability=reachability,
        reachability_authority=_optional_str(
            raw.get("reachability_authority"), f"{where}.reachability_authority"
        ),
        vision_emission=vision_emission,
        vision_evidence=_optional_str(raw.get("vision_evidence"), f"{where}.vision_evidence"),
        blocked_on=tuple(blocked_on),
    )


def _parse_caveat(raw: object, index: int) -> Caveat:
    where = f"provenance.caveats[{index}]"
    raw = _require_dict(raw, where)
    return Caveat(
        kind=_require_in(
            _require_str(raw.get("kind"), f"{where}.kind"), CAVEAT_KINDS, f"{where}.kind"
        ),
        note=_require_str(raw.get("note"), f"{where}.note"),
        human_ruling=_optional_str(raw.get("human_ruling"), f"{where}.human_ruling"),
    )


def parse_provenance(rule: dict) -> Provenance | None:
    """Parse a rule's optional `provenance` block into typed structures.

    Returns None when the key is ABSENT -- that is a valid, complete state
    meaning "this rule carries no provenance", not an error and not an
    empty Provenance(). Raises ProvenanceError when the key is present but
    malformed."""
    if not isinstance(rule, dict):
        raise ProvenanceError(f"rule must be an object, got {type(rule).__name__}")
    if "provenance" not in rule:
        return None

    raw = rule["provenance"]
    if raw is None:
        return None
    raw = _require_dict(raw, "provenance")

    bindings_raw = raw.get("token_bindings") or []
    if not isinstance(bindings_raw, list):
        raise ProvenanceError(
            f"provenance.token_bindings must be an array, got {type(bindings_raw).__name__}"
        )
    caveats_raw = raw.get("caveats") or []
    if not isinstance(caveats_raw, list):
        raise ProvenanceError(
            f"provenance.caveats must be an array, got {type(caveats_raw).__name__}"
        )
    notes_raw = raw.get("notes") or []
    if not isinstance(notes_raw, list):
        raise ProvenanceError(
            f"provenance.notes must be an array, got {type(notes_raw).__name__}"
        )
    for i, note in enumerate(notes_raw):
        _require_str(note, f"provenance.notes[{i}]")

    status_raw = raw.get("status")

    return Provenance(
        token_bindings=tuple(
            _parse_token_binding(b, i) for i, b in enumerate(bindings_raw)
        ),
        status=_parse_status(status_raw) if status_raw is not None else None,
        caveats=tuple(_parse_caveat(c, i) for i, c in enumerate(caveats_raw)),
        notes=tuple(notes_raw),
    )


# ─── shared helpers for the checks ──────────────────────────────────────


def _antecedents(rule: dict) -> list[dict]:
    ants = rule.get("antecedents") or []
    if not isinstance(ants, list):
        raise ProvenanceError(
            f"rule.antecedents must be an array, got {type(ants).__name__}"
        )
    return ants


def _rule_id(rule: dict) -> str:
    return str(rule.get("rule_id", "<no rule_id>"))


def _resolve(rule: dict, binding: TokenBinding) -> dict | None:
    """The antecedent a binding points at, or None if the index is out of
    range (which G4 reports; the other checks then skip that binding
    rather than double-reporting the same defect)."""
    ants = _antecedents(rule)
    if 0 <= binding.antecedent_index < len(ants):
        return ants[binding.antecedent_index]
    return None


# ─── G1-G8 ──────────────────────────────────────────────────────────────


def check_g1(rule: dict, provenance: Provenance) -> list[str]:
    """G1: chosen_token == antecedents[i][bound_field].

    EXACT string equality. No difflib, no case-folding, no whitespace
    tolerance -- S94 already measured difflib nearest-token matching WRONG
    on 2 of 5 rules, so nothing fuzzy belongs in the load-bearing check.

    This is the assertion that would have failed the instant e982a92
    landed (chosen_token "well_marked" vs antecedent value "deep" on
    FT_001 and FT_009), and the one that fails today on FT_007, FT_008
    and L_026."""
    violations = []
    for binding in provenance.token_bindings:
        antecedent = _resolve(rule, binding)
        if antecedent is None:
            continue  # G4 reports the unresolvable index
        live = antecedent.get(binding.bound_field)
        if live != binding.chosen_token:
            violations.append(
                f"G1 {_rule_id(rule)}: token_binding[{binding.antecedent_index}]."
                f"{binding.bound_field} declares chosen_token {binding.chosen_token!r} "
                f"but the live antecedent holds {live!r}"
            )
    return violations


def check_g2(rule: dict, provenance: Provenance) -> list[str]:
    """G2: binding.attribute == antecedent.attribute.

    Skipped when the binding declares no attribute -- it is optional, and
    an absent attribute is not a mismatch."""
    violations = []
    for binding in provenance.token_bindings:
        if binding.attribute is None:
            continue
        antecedent = _resolve(rule, binding)
        if antecedent is None:
            continue
        live = antecedent.get("attribute")
        if live != binding.attribute:
            violations.append(
                f"G2 {_rule_id(rule)}: token_binding[{binding.antecedent_index}] declares "
                f"attribute {binding.attribute!r} but the live antecedent holds {live!r}"
            )
    return violations


def check_g3(rule: dict, provenance: Provenance) -> list[str]:
    """G3: no superseded entry names the live token.

    A supersession record says "this token was RETIRED". If it names the
    token the rule currently fires on, the migration was applied to the
    ledger but not to the antecedent (or vice versa) -- a half-applied
    migration, which is exactly the FT_007/FT_008/L_026 shape where a
    stale flag survived alongside its own replacement."""
    violations = []
    for binding in provenance.token_bindings:
        antecedent = _resolve(rule, binding)
        if antecedent is None:
            continue
        live = antecedent.get(binding.bound_field)
        for retired in binding.superseded:
            if retired.chosen_token == live:
                violations.append(
                    f"G3 {_rule_id(rule)}: token_binding[{binding.antecedent_index}] lists "
                    f"{retired.chosen_token!r} as superseded, but that is the LIVE "
                    f"antecedent {binding.bound_field} -- half-applied migration"
                )
    return violations


def check_g4(rule: dict, provenance: Provenance) -> list[str]:
    """G4: antecedent_index resolves; at most one binding per
    (antecedent_index, bound_field)."""
    violations = []
    ants = _antecedents(rule)
    seen: set[tuple[int, str]] = set()
    for binding in provenance.token_bindings:
        if not 0 <= binding.antecedent_index < len(ants):
            violations.append(
                f"G4 {_rule_id(rule)}: token_binding antecedent_index "
                f"{binding.antecedent_index} does not resolve -- rule has "
                f"{len(ants)} antecedent(s)"
            )
            continue
        key = (binding.antecedent_index, binding.bound_field)
        if key in seen:
            violations.append(
                f"G4 {_rule_id(rule)}: duplicate token_binding for "
                f"(antecedent_index={binding.antecedent_index}, "
                f"bound_field={binding.bound_field!r})"
            )
        seen.add(key)
    return violations


def check_g5(
    rule: dict,
    provenance: Provenance,
    normalize_fn: Callable[[str], str] = _gate_normalize,
) -> list[str]:
    """G5: binding_kind == "proxy" => normalized source_phrase is a
    substring of the normalized rule.source_quote.

    A proxy binding claims "the source says X, and we chose token Y to
    stand for it". That claim is only auditable if X is really in the
    source. This reuses gate_rule_citations.normalize -- the SAME
    normalisation that gate already applies when verifying authored quotes
    against the corpus (S119 INVARIANT 2), so the two cannot disagree
    about what "the same words" means."""
    violations = []
    quote_norm = normalize_fn(rule.get("source_quote") or "")
    for binding in provenance.token_bindings:
        if binding.binding_kind != "proxy":
            continue
        if binding.source_phrase is None:
            violations.append(
                f"G5 {_rule_id(rule)}: token_binding[{binding.antecedent_index}] has "
                f"binding_kind 'proxy' but no source_phrase -- a proxy mapping must "
                f"name the source words it stands in for"
            )
            continue
        phrase_norm = normalize_fn(binding.source_phrase)
        if not phrase_norm or phrase_norm not in quote_norm:
            violations.append(
                f"G5 {_rule_id(rule)}: token_binding[{binding.antecedent_index}] proxy "
                f"source_phrase {binding.source_phrase!r} does not appear in the rule's "
                f"source_quote"
            )
    return violations


def check_g6(
    rule: dict,
    provenance: Provenance,
    oracle: Callable[[str, str, object, object], dict] = _reachability_oracle,
) -> list[str]:
    """G6: status.fireable == true => reachability not in {fail, unemittable},
    with vocab_reachability_scan.classify_antecedent as the ORACLE.

    Two parts, both needed:
      (a) DECLARED self-consistency -- a rule cannot claim to be fireable
          while declaring its own vocabulary unreachable.
      (b) ORACLE agreement -- the declared reachability must match what
          the scan actually says about this rule's antecedents. Without
          (b), (a) is just prose checking prose: a rule could declare
          "pass" indefinitely while its tokens were unemittable.

    The oracle owns the verdict; this function only renames its status
    (see _ORACLE_STATUS_TO_REACHABILITY) and compares. It is never
    reimplemented here."""
    violations = []
    status = provenance.status
    if status is None:
        return violations

    # (a) declared self-consistency
    if status.fireable is True and status.reachability in _UNFIREABLE_REACHABILITY:
        violations.append(
            f"G6 {_rule_id(rule)}: status.fireable is true but status.reachability is "
            f"{status.reachability!r}"
        )

    # (b) oracle agreement -- skip when the rule declines to claim a state
    if status.reachability in (None, "unchecked"):
        return violations

    worst = "pass"
    worst_detail = ""
    for i, antecedent in enumerate(_antecedents(rule)):
        try:
            verdict = oracle(
                antecedent.get("feature"),
                antecedent.get("attribute"),
                antecedent.get("value"),
                antecedent.get("relation_target"),
            )
        except Exception as exc:  # oracle failure must not masquerade as a pass
            violations.append(
                f"G6 {_rule_id(rule)}: reachability oracle raised on antecedent[{i}]: {exc}"
            )
            return violations
        mapped = _ORACLE_STATUS_TO_REACHABILITY.get(verdict.get("status"))
        if mapped is None:
            violations.append(
                f"G6 {_rule_id(rule)}: reachability oracle returned unknown status "
                f"{verdict.get('status')!r} for antecedent[{i}]"
            )
            return violations
        # Any non-pass verdict is the rule's verdict: one unreachable
        # antecedent makes the whole ANDed rule unfireable.
        if mapped != "pass":
            worst = mapped
            worst_detail = f" (antecedent[{i}]: {verdict.get('detail')})"
            break

    if status.reachability != worst:
        violations.append(
            f"G6 {_rule_id(rule)}: status.reachability declares {status.reachability!r} "
            f"but the reachability oracle says {worst!r}{worst_detail}"
        )
    return violations


def check_g7(
    rule: dict,
    provenance: Provenance,
    is_tracked: Callable[[str | Path], bool] = is_git_tracked,
    repo_root: Path = _REPO_ROOT,
) -> list[str]:
    """G7: vision_emission != "unproven" => vision_evidence exists AND is
    git-tracked.

    Working Style #16: an uncommitted probe cannot be audited. A claim of
    confirmed (or refuted) vision emission that rests on a working-tree-only
    file is not yet evidence -- which is precisely M_001's state today."""
    violations = []
    status = provenance.status
    if status is None or status.vision_emission == "unproven":
        return violations

    if not status.vision_evidence:
        violations.append(
            f"G7 {_rule_id(rule)}: status.vision_emission is "
            f"{status.vision_emission!r} but no vision_evidence path is given"
        )
        return violations

    evidence_path = Path(status.vision_evidence)
    absolute = evidence_path if evidence_path.is_absolute() else repo_root / evidence_path
    if not absolute.exists():
        violations.append(
            f"G7 {_rule_id(rule)}: vision_evidence {status.vision_evidence!r} does not exist"
        )
        return violations
    if not is_tracked(status.vision_evidence):
        violations.append(
            f"G7 {_rule_id(rule)}: vision_evidence {status.vision_evidence!r} exists but is "
            f"NOT git-tracked -- an uncommitted probe cannot be audited (Working Style #16)"
        )
    return violations


def check_g8(
    rule: dict, provenance: Provenance, registry: dict | None = None
) -> list[str]:
    """G8: every blocked_on entry parses as "ontology:<kind>:<token>" and
    that token is genuinely ABSENT from the registry.

    The absence check is what makes a blocker self-clearing: the moment
    the ontology gains the token, the blocker fails loudly instead of
    sitting there stale. That closes H_011 / HL_015 / H_013 / HL_002 /
    H_022 as a class -- five flags whose whole content is "this token
    isn't in the ontology yet"."""
    violations = []
    status = provenance.status
    if status is None:
        return violations
    reg = registry if registry is not None else _REGISTRY

    for blocker in status.blocked_on:
        if not blocker.startswith(_BLOCKER_PREFIX):
            violations.append(
                f"G8 {_rule_id(rule)}: blocked_on entry {blocker!r} does not parse as "
                f"'ontology:<kind>:<token>'"
            )
            continue
        remainder = blocker[len(_BLOCKER_PREFIX) :]
        kind, sep, token = remainder.partition(":")
        if not sep or not kind or not token:
            violations.append(
                f"G8 {_rule_id(rule)}: blocked_on entry {blocker!r} does not parse as "
                f"'ontology:<kind>:<token>'"
            )
            continue
        if kind not in BLOCKER_KINDS:
            violations.append(
                f"G8 {_rule_id(rule)}: blocked_on entry {blocker!r} names unknown kind "
                f"{kind!r} -- expected one of {sorted(BLOCKER_KINDS)}"
            )
            continue
        if token in _registry_tokens(kind, reg):
            violations.append(
                f"G8 {_rule_id(rule)}: blocked_on entry {blocker!r} claims {token!r} is "
                f"absent, but it IS present in the ontology registry -- blocker is stale"
            )
    return violations


# ─── aggregate ──────────────────────────────────────────────────────────

_ALL_CHECKS: tuple[tuple[str, Callable[[dict, Provenance], list[str]]], ...] = (
    ("G1", check_g1),
    ("G2", check_g2),
    ("G3", check_g3),
    ("G4", check_g4),
    ("G5", check_g5),
    ("G6", check_g6),
    ("G7", check_g7),
    ("G8", check_g8),
)


def validate_provenance(rule: dict, provenance: Provenance) -> list[str]:
    """Run G1-G8 against an already-parsed Provenance. Returns every
    violation found, in check order; empty list == pass."""
    violations: list[str] = []
    for _name, check in _ALL_CHECKS:
        violations.extend(check(rule, provenance))
    return violations


def validate_rule(rule: dict) -> list[str]:
    """Parse `rule`'s provenance and run G1-G8 against it.

    A rule with NO provenance key returns no violations -- absence is
    valid (see the module docstring). Raises ProvenanceError if the key is
    present but malformed."""
    provenance = parse_provenance(rule)
    if provenance is None:
        return []
    return validate_provenance(rule, provenance)
