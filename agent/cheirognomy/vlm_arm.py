"""
agent/cheirognomy/vlm_arm.py
VLM-only cheirognomy capture arm -- GPT-4o vision emits per-finger and whole-hand
PRIMITIVES; the whole-hand type is DERIVED deterministically from the rubric.

Rubric + schema: data/palm_rules/_doctrine/CHEIROGNOMY_HAND_TYPE.md

VOCABULARY IS THE CONTRACT
--------------------------
Every menu this module offers the model is PARSED FROM THE DOCTRINE FILE at load
time (S2 the 7-type table, S3 the arm split, S4 the capture schema, S7 the
spacing signal). Nothing here paraphrases the rubric: if the doctrine table
changes, the model's allowed vocabulary and the derive rubric change with it.
A value the model emits that is not on its menu is a FABRICATION -- it is
rejected and recorded, never coerced onto the nearest legal token.

Ingestion is NOT reimplemented: `palm_processor.validate_palm_image` is the
hand-presence / readability gate, and the base64 + OpenAI/.env pattern mirrors
`palm_processor` exactly.

Two distinct flags (they are NOT the same thing -- the doctrine uses one word for
both and they have opposite consequences, so they are split here explicitly):
  * `quality_flag`  -- HARD capture failure (no hand, unreadable, pervasive
    off-menu fabrication). Mutually exclusive with a populated result: when it
    is set, no type and no primitive is emitted at all.
  * `disagreement_flags` -- the SOFT S6 reconciliation flag: self-consistency
    runs disagreed on a primitive. Coexists with a populated result, lowers
    confidence, pushes the derived type toward `mixed`, and is surfaced in
    `disclosed_assumption_text`. S6: "disagreement -> a flag, not a forced call."

Fidelity-not-truth: there is no type-labeled oracle. Self-consistency across N
runs measures REPRODUCIBILITY, never correctness.

THUMB is out of scope (S4, own chapter); `nail_length` is captured only because
S2 lists it as a type criterion.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agent.palm_processor import validate_palm_image

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_REPO_ROOT / ".env")

logger = logging.getLogger(__name__)

DOCTRINE_PATH = _REPO_ROOT / "data" / "palm_rules" / "_doctrine" / "CHEIROGNOMY_HAND_TYPE.md"

_SOURCE_ARM = "vlm"
_MODEL = "gpt-4o"

# -- THRESHOLDS (CLAUDE.md Working Style #4: justification + scope guard + tuning note) --
#
# _N_RUNS = 3 -- self-consistency replaces the scrapped MediaPipe reference arm.
#   Odd, so a strict majority always exists for a 2-way split. 3 balances signal
#   against cost (3x vision calls per hand). SCOPE GUARD: this module only.
#   TUNING NOTE: re-tune against the S1 self-labeled consistency set once it
#   exists -- raise to 5 only if 3-run majorities prove unstable on that set.
_N_RUNS = 3
#
# _TEMPERATURE = 0.4 -- deliberately NOT 0: at temp 0 the runs are near-identical
#   and the agreement fraction measures nothing. 0.4 is high enough for genuine
#   sampling variation, low enough that the model stays on-menu. SCOPE GUARD:
#   the classify call only. TUNING NOTE: same consistency set; if off-menu rates
#   rise above a few percent, lower it before widening the menus.
_TEMPERATURE = 0.4
#
# _DOMINANCE_FLOOR = 0.50 -- a type must match at least half of its OWN evaluable
#   S2 criteria to be named. Below that, nothing dominates -> `mixed`.
# _DOMINANCE_MARGIN = 0.15 -- and it must beat the runner-up by this much, else
#   the two types are indistinguishable on the observed evidence -> `mixed`.
#   Both are judgment calls on an ordinal score, NOT measured -- S2 itself warns
#   "conic <-> psychic is a proportion continuum, not a clean boundary".
#   SCOPE GUARD: `_derive_type` only. TUNING NOTE: first real tuning evidence is
#   the consistency set's mixed-rate; a mixed-rate near 100% means the floor is
#   too high, near 0% means the margin is too low.
_DOMINANCE_FLOOR = 0.50
_DOMINANCE_MARGIN = 0.15
#
# _FINGER_CONSENSUS_MIN = 3 of 4 -- S5: "mixed therefore means fingers disagree".
#   3/4 tolerates one atypical finger (the little finger commonly differs)
#   without collapsing every hand to mixed. SCOPE GUARD: fingertip form only.
_FINGER_CONSENSUS_MIN = 3

# max_tokens=500: the response is ~15 short enum fields; 500 is ~3x the observed
# need. TUNING NOTE: raise only if a run is ever observed truncated.
_MAX_TOKENS = 500

# Engineering addition, NOT a doctrine word -- declared here rather than smuggled
# in: the model must have a legal way to say "I cannot see this", otherwise the
# closed menu itself pressures it into fabricating a value.
UNREADABLE = "not clearly visible"

# Structural wiring only (column header -> primitive key). This maps the S2
# table's SHAPE, it does not restate its CONTENT -- every value still comes from
# the file.
_COLUMN_SLOT = {
    "palm": "palm",
    "fingertips": "fingertip_form",
    "fingers/length": "finger_character",
    "joints": "joint_knottiness",
    "nails": "nail_length",
}
# The S2 criteria columns that the derive step scores against.
_DERIVE_SLOTS = ("palm", "fingertip_form", "finger_character", "joint_knottiness", "nail_length")

# Whole-hand primitives the model is asked for, in prompt order. Every key must
# be a menu key parsed out of the doctrine.
_HAND_PRIMITIVES = (
    "palm",
    "finger_character",
    "joint_knottiness",
    "nail_length",
    "broad_point",
    "overall_proportion",
    "finger_palm_ratio",
)


class CheirognomyDoctrineError(RuntimeError):
    """The doctrine file is missing, unreadable, or has lost a section this module parses."""


class VLMArmError(RuntimeError):
    """The VLM arm could not complete a capture."""


# =============================================================================
# Doctrine parsing -- the vocabulary contract
# =============================================================================

@dataclass(frozen=True)
class TypeCriteria:
    """One row of the S2 table: a type and the criteria cells it declares."""
    name: str
    src: str
    criteria: dict           # slot -> verbatim cell phrase (missing slot = an em-dash cell)
    fingertip_tokens: tuple  # the S3 menu words that appear in this row's Fingertips cell


@dataclass(frozen=True)
class Doctrine:
    types: dict              # name -> TypeCriteria (fallback type excluded)
    fallback_type: str
    menus: dict              # primitive key -> tuple of legal values
    finger_keys: tuple       # ("jupiter", "saturn", "apollo", "mercury")
    spacing_keys: tuple      # ("1_2", "2_3", "3_4")


def _sections(text):
    """Split the doctrine on its `## <n>. <title>` headers, keyed by section number."""
    out, current, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(\d+)\.\s", line)
        if m:
            if current is not None:
                out[current] = "\n".join(buf)
            current, buf = int(m.group(1)), []
        elif current is not None:
            buf.append(line)
    if current is not None:
        out[current] = "\n".join(buf)
    return out


def _clean_cell(cell):
    """Normalise one table cell. The em-dash placeholder means 'this type declares nothing here'."""
    cell = re.sub(r"\s*\([^)]*\)", "", cell).strip()   # drop parentheticals: "(asymmetric)", "(extreme)"
    cell = re.sub(r"\s+", " ", cell).strip().strip("*").strip()
    if cell in {"", "—", "-", "–"}:
        return None
    return cell.lower()


def _parse_type_table(section):
    rows = [ln.strip() for ln in section.splitlines() if ln.strip().startswith("|")]
    rows = [r for r in rows if not re.match(r"^\|[\s:|-]+\|$", r)]   # drop the |---|---| separator
    if len(rows) < 3:
        raise CheirognomyDoctrineError(
            "S2 type table: expected a header plus type rows, found "
            f"{len(rows)} table lines in {DOCTRINE_PATH}"
        )

    header = [c.strip().lower() for c in rows[0].strip("|").split("|")]
    try:
        type_idx = header.index("type")
        src_idx = header.index("src")
    except ValueError as exc:
        raise CheirognomyDoctrineError(
            f"S2 type table header lost a required column ('type'/'src'): {header}"
        ) from exc

    types = {}
    fallback = None
    for row in rows[1:]:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if len(cells) != len(header):
            raise CheirognomyDoctrineError(
                f"S2 type table row has {len(cells)} cells, header has {len(header)}: {row!r}"
            )
        name = cells[type_idx].strip().lower()
        src = cells[src_idx].strip()
        if "fallback" in src.lower():
            fallback = name
            continue                      # the fallback row carries meta-text, not criteria
        criteria = {}
        for col, cell in zip(header, cells):
            slot = _COLUMN_SLOT.get(col)
            if slot is None:
                continue
            value = _clean_cell(cell)
            if value is not None:
                criteria[slot] = value
        types[name] = TypeCriteria(name=name, src=src, criteria=criteria, fingertip_tokens=())

    if fallback is None:
        raise CheirognomyDoctrineError("S2 type table: no row marked FALLBACK ONLY (expected 'Mixed').")
    if not types:
        raise CheirognomyDoctrineError("S2 type table: no non-fallback type rows parsed.")
    return types, fallback


def _strip_code_fences(text):
    """Drop ``` fenced regions. Value menus are declared in prose; the fences hold schema shape."""
    out, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            out.append(line)
    return "\n".join(out)


def _braced_set(text, anchor):
    """
    Pull the first `{a, b, c}` VALUE MENU that follows `anchor` in `text`.

    The menu must sit in the anchor's OWN bullet -- its line plus any
    soft-wrapped continuation lines. Scanning forward from the anchor instead
    was wrong twice over: S4 names `broad_point` inside its JSON schema block
    long before the annotation that actually declares the menu, so a forward
    scan first hit `inter_finger_spacing`'s JSON object, and then -- once
    colon-bearing braces were skipped -- the `_provenance` line's
    `{value, source_arm, confidence}`. Both are prose ABOUT the schema, not
    `broad_point`'s values. Two rules separate a declaration from a mention:

      1. fenced code blocks are excluded outright -- menus live in prose, and
         every decoy above came from inside the ```json fence;
      2. the search is scoped to the anchor's bullet, because S3's menu is
         soft-wrapped onto the next line and a strict same-line rule missed it.

    A brace containing a colon is a JSON object, never a value menu.
    """
    prose = _strip_code_fences(text)
    lines = prose.splitlines()
    hits = [i for i, ln in enumerate(lines) if anchor in ln]
    if not hits:
        raise CheirognomyDoctrineError(
            f"doctrine: anchor {anchor!r} not found in this section's prose "
            "(it may exist only inside a code fence, which is excluded by design)."
        )
    for start in hits:
        block = [lines[start]]
        for ln in lines[start + 1:]:
            if not ln.strip() or not ln[:1].isspace():
                break                      # blank line or a new top-level bullet ends the item
            block.append(ln)
        for m in re.finditer(r"\{([^{}]*)\}", " ".join(block)):
            body = m.group(1)
            if ":" in body:
                continue                   # a JSON object, not a value menu
            values = tuple(v.strip().lower() for v in body.split(",") if v.strip())
            if values:
                return values
    raise CheirognomyDoctrineError(
        f"doctrine: {anchor!r} appears in {len(hits)} prose bullet(s) but none carries a "
        "colon-free brace VALUE MENU."
    )


# _STEM_MIN = 5 -- when mapping a S2 Fingertips CELL onto the S3 closed menu, a
#   cell word and a menu word match if either is a prefix of the other and the
#   shorter is at least this long. This exists for ONE real case the doctrine
#   contains: the Spatulate row's cell reads "spatula-flared/flattened" while the
#   menu word is "spatulate" -- the same doctrine word in a different
#   morphological form, NOT a synonym. Plain containment silently mapped that row
#   to nothing, which would have made spatulate unreachable forever.
#   An alias table is deliberately NOT used: an alias would be a paraphrase of
#   the rubric, which is exactly what the vocabulary contract forbids.
#   5 keeps short cell words ("full", "at", "on") from prefix-colliding.
#   SCOPE GUARD: cell -> fingertip menu mapping only; never applied to a value
#   the MODEL emits (those must match a menu exactly).
#   TUNING NOTE: `load_doctrine` raises if two menu words ever stem-collide with
#   each other, so an ambiguous menu fails loud instead of mapping arbitrarily.
_STEM_MIN = 5


def _stem_match(a, b):
    """True when `a` and `b` are the same doctrine word in different morphological form."""
    if a == b:
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    return len(short) >= _STEM_MIN and long_.startswith(short)


def _menu_tokens_in_cell(menu, cell):
    """Which closed-menu words a S2 table cell names. Word-level, order-preserving."""
    if not cell:
        return ()
    cell_words = [w for w in re.split(r"[^a-z]+", cell) if w]
    return tuple(m for m in menu if any(_stem_match(m, w) for w in cell_words))


def _parse_schema_keys(section):
    """Read the finger identity keys and spacing keys off S4's canonical JSON block."""
    m = re.search(r"```json\s*(\{.*?\})\s*```", section, re.DOTALL)
    if not m:
        raise CheirognomyDoctrineError("S4: canonical JSON capture-schema block not found.")
    try:
        schema = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        raise CheirognomyDoctrineError(f"S4: capture-schema JSON block does not parse: {exc}") from exc
    fingers = tuple(schema.get("fingers", {}).keys())
    spacing = tuple(schema.get("hand_geometry", {}).get("inter_finger_spacing", {}).keys())
    if not fingers or not spacing:
        raise CheirognomyDoctrineError("S4: schema block is missing `fingers` or `inter_finger_spacing`.")
    return fingers, spacing


@lru_cache(maxsize=4)
def load_doctrine(path=None):
    """
    Parse the rubric into the closed menus and the derive criteria.

    Raises:
        CheirognomyDoctrineError: file missing, or any parsed section has drifted.
                                  Fails LOUD at load time -- never falls back to a
                                  hardcoded copy of the vocabulary.
    """
    doc_path = Path(path) if path is not None else DOCTRINE_PATH
    try:
        text = doc_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise CheirognomyDoctrineError(f"cannot read cheirognomy doctrine at {doc_path}: {exc}") from exc

    secs = _sections(text)
    for required in (2, 3, 4, 7):
        if required not in secs:
            raise CheirognomyDoctrineError(f"doctrine {doc_path} is missing section S{required}.")

    types, fallback = _parse_type_table(secs[2])

    # S3 declares fingertip_form a CLOSED menu -- it is canonical, and each type
    # row's Fingertips cell is mapped ONTO it rather than the other way round.
    fingertip_menu = _braced_set(secs[3], "fingertip form")

    # Scope guard for _STEM_MIN made mechanical: if two menu words stem-collide,
    # a cell naming one would map to both, so fail loud rather than guess.
    for i, a in enumerate(fingertip_menu):
        for b in fingertip_menu[i + 1:]:
            if _stem_match(a, b):
                raise CheirognomyDoctrineError(
                    f"S3 fingertip menu is ambiguous under stem-matching: {a!r} and {b!r} "
                    "collide, so a table cell cannot be mapped to one of them unambiguously."
                )

    types = {
        name: TypeCriteria(
            name=tc.name,
            src=tc.src,
            criteria=tc.criteria,
            fingertip_tokens=_menu_tokens_in_cell(fingertip_menu, tc.criteria.get("fingertip_form")),
        )
        for name, tc in types.items()
    }

    # S3: "overall long-narrow vs broad" -- the whole-hand proportion axis.
    m_prop = re.search(r"overall\s+([a-z-]+)\s+vs\s+([a-z-]+)", secs[3])
    if not m_prop:
        raise CheirognomyDoctrineError("S3: the 'overall <x> vs <y>' proportion axis was not found.")
    overall_menu = (m_prop.group(1), m_prop.group(2))

    # S4 annotation: broad_point is a brace-menu -- the spatulate sub-signal.
    broad_point_menu = _braced_set(secs[4], "broad_point")

    # S7: "(tight = cautious/reserved, wide = independent, Cheiro p96)".
    spacing_menu = tuple(dict.fromkeys(w.lower() for w in re.findall(r"(\w+)\s*=\s*[\w/]+", secs[7])))
    if len(spacing_menu) < 2:
        raise CheirognomyDoctrineError("S7: the inter-finger spacing signal words were not found.")

    # finger_palm_ratio has no brace-menu anywhere; its two poles are the length
    # words the S2 Fingers/length column actually uses ("short, clumsy" /
    # "extremely long, tapering"). Read them off the table rather than invent them.
    length_words = tuple(
        w for w in ("long", "short")
        if any(re.search(r"\b" + w + r"\b", tc.criteria.get("finger_character", ""))
               for tc in types.values())
    )
    if len(length_words) < 2:
        raise CheirognomyDoctrineError(
            "S2 Fingers/length column no longer carries both length poles ('long'/'short')."
        )

    def _column_menu(slot):
        return tuple(dict.fromkeys(tc.criteria[slot] for tc in types.values() if slot in tc.criteria))

    menus = {
        "fingertip_form":       fingertip_menu,
        "palm":                 _column_menu("palm"),
        "finger_character":     _column_menu("finger_character"),
        "joint_knottiness":     _column_menu("joint_knottiness"),
        "nail_length":          _column_menu("nail_length"),
        "broad_point":          broad_point_menu,
        "overall_proportion":   overall_menu,
        "finger_palm_ratio":    length_words,
        "inter_finger_spacing": spacing_menu,
    }
    for key, values in menus.items():
        if not values:
            raise CheirognomyDoctrineError(f"doctrine: menu {key!r} parsed empty.")

    finger_keys, spacing_keys = _parse_schema_keys(secs[4])
    return Doctrine(
        types=types,
        fallback_type=fallback,
        menus=menus,
        finger_keys=finger_keys,
        spacing_keys=spacing_keys,
    )


# =============================================================================
# Prompt assembly -- built from the parsed menus, never from a paraphrase
# =============================================================================

def build_system_prompt(doc):
    """Render the closed menus into the observer instruction. Every listed value is doctrine-sourced."""
    def menu(key):
        return " | ".join(doc.menus[key] + (UNREADABLE,))

    lines = [
        "You are a trained observer recording HAND SHAPE notes for a Cheiro-tradition "
        "cheirognomist. You are NOT the cheirognomist.",
        "",
        "Record only what is physically visible. No meanings, no character traits, no "
        "predictions. Do NOT name a hand type -- the type is derived later from your "
        "observations, and naming it here would corrupt that derivation.",
        "",
        "CLOSED VOCABULARY: for every field below you must copy one value VERBATIM from "
        "that field's list. A value that is not on the list is a fabrication and will be "
        f"discarded. If you cannot see a feature clearly, answer exactly '{UNREADABLE}' -- "
        "that is always a legal answer and is strongly preferred over a guess.",
        "",
        "PER-FINGER (identify each finger by position; the THUMB is excluded entirely):",
        "  jupiter = index (1st), saturn = middle (2nd), apollo = ring (3rd), mercury = little (4th)",
        f"  fingertip_form: {menu('fingertip_form')}",
        "",
        "WHOLE HAND:",
        f"  palm (overall palm shape): {menu('palm')}",
        f"  finger_character: {menu('finger_character')}",
        f"  joint_knottiness: {menu('joint_knottiness')}",
        f"  nail_length: {menu('nail_length')}",
        f"  broad_point (where the palm is broadest): {menu('broad_point')}",
        f"  overall_proportion: {menu('overall_proportion')}",
        f"  finger_palm_ratio (finger length against palm length): {menu('finger_palm_ratio')}",
        "",
        "INTER-FINGER SPACING at rest, one value per gap "
        f"({', '.join(doc.spacing_keys)} = the gaps between adjacent fingers 1-2, 2-3, 3-4):",
        f"  {menu('inter_finger_spacing')}",
        "",
        "Set hand_present to false if the image does not show a human hand, or if the hand "
        "is too obscured to observe at all. When hand_present is false, leave every other "
        "field as the unreadable value.",
        "",
        "Return ONLY valid JSON, no markdown, exactly this shape:",
        "{",
        '  "hand_present": true,',
        '  "fingers": {'
        + ", ".join(f'"{k}": {{"fingertip_form": "..."}}' for k in doc.finger_keys)
        + "},",
        '  "hand": {' + ", ".join(f'"{k}": "..."' for k in _HAND_PRIMITIVES) + "},",
        '  "inter_finger_spacing": {'
        + ", ".join(f'"{k}": "..."' for k in doc.spacing_keys)
        + "}",
        "}",
    ]
    return "\n".join(lines)


# =============================================================================
# One classify run
# =============================================================================

def _encode_image(image_bytes):
    """Mirror of palm_processor's inline decode: sniff the PNG magic, else JPEG."""
    if not image_bytes:
        raise VLMArmError("vlm_arm: empty image_bytes -- nothing to classify.")
    mime = "image/png" if image_bytes[:8].startswith(b"\x89PNG") else "image/jpeg"
    return mime, base64.b64encode(image_bytes).decode("utf-8")


def _classify_once(image_bytes, doc, client, run_index):
    """
    One vision call. Returns (payload, off_menu) where payload holds ONLY on-menu
    values and off_menu records every rejected value verbatim.

    Off-menu values are dropped, never coerced: the primitive simply goes
    unobserved for this run, which lowers its agreement fraction downstream.
    """
    mime, b64 = _encode_image(image_bytes)
    try:
        response = client.chat.completions.create(
            model=_MODEL,
            messages=[
                {"role": "system", "content": build_system_prompt(doc)},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Observe this hand image."},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                },
            ],
            max_tokens=_MAX_TOKENS,
            temperature=_TEMPERATURE,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
    except Exception as exc:
        raise VLMArmError(f"vlm_arm: GPT-4o classify call failed on run {run_index}: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError) as exc:
        raise VLMArmError(
            f"vlm_arm: run {run_index} returned unparseable JSON: {exc}. raw={raw!r}"
        ) from exc

    off_menu = []

    def take(menu_key, value, path):
        """Keep the value only if it is on its doctrine menu; otherwise record and drop it."""
        if not isinstance(value, str):
            if value is not None:
                off_menu.append({"path": path, "value": repr(value), "reason": "not a string"})
            return None
        norm = re.sub(r"\s+", " ", value).strip().lower()
        if norm == UNREADABLE:
            return None                                    # legally unobserved, not a fabrication
        if norm in doc.menus[menu_key]:
            return norm
        off_menu.append({"path": path, "value": value, "reason": f"off-menu for {menu_key}"})
        return None

    payload = {
        "hand_present": bool(parsed.get("hand_present", False)),
        "fingers": {},
        "hand": {},
        "inter_finger_spacing": {},
    }

    fingers_in = parsed.get("fingers") or {}
    for fkey in doc.finger_keys:
        rec = fingers_in.get(fkey) or {}
        raw_val = rec.get("fingertip_form") if isinstance(rec, dict) else rec
        payload["fingers"][fkey] = take("fingertip_form", raw_val, f"fingers.{fkey}.fingertip_form")

    hand_in = parsed.get("hand") or {}
    for pkey in _HAND_PRIMITIVES:
        payload["hand"][pkey] = take(pkey, hand_in.get(pkey), f"hand.{pkey}")

    spacing_in = parsed.get("inter_finger_spacing") or {}
    for skey in doc.spacing_keys:
        payload["inter_finger_spacing"][skey] = take(
            "inter_finger_spacing", spacing_in.get(skey), f"inter_finger_spacing.{skey}"
        )

    return payload, off_menu


# =============================================================================
# Self-consistency -- majority vote across N runs
# =============================================================================

def _flatten(payload, doc):
    """Flatten one run's payload to path -> value|None, in a stable order."""
    flat = {}
    for fkey in doc.finger_keys:
        flat[f"fingers.{fkey}.fingertip_form"] = payload["fingers"][fkey]
    for pkey in _HAND_PRIMITIVES:
        flat[f"hand.{pkey}"] = payload["hand"][pkey]
    for skey in doc.spacing_keys:
        flat[f"inter_finger_spacing.{skey}"] = payload["inter_finger_spacing"][skey]
    return flat


def _majority(runs, doc):
    """
    Majority value per primitive across the runs.

    agreement = (votes for the winner) / (number of runs attempted) -- a run that
    dropped the value (unreadable or off-menu) counts against agreement rather
    than being quietly excluded, so silence is visible in the number.

    A tie, or no votes at all, yields value=None: no majority is not a coin toss.
    """
    n = len(runs)
    flats = [_flatten(p, doc) for p in runs]
    primitives = {}
    for path in flats[0]:
        votes = [f[path] for f in flats if f[path] is not None]
        counts = Counter(votes)
        value, agreement, tied = None, 0.0, False
        if counts:
            top = counts.most_common()
            best_n = top[0][1]
            winners = [v for v, c in top if c == best_n]
            if len(winners) == 1:
                value = winners[0]
                agreement = round(best_n / n, 3)
            else:
                tied = True
        primitives[path] = {
            "value": value,
            "source_arm": _SOURCE_ARM,
            "confidence": agreement,
            "agreement": agreement,
            "votes": dict(counts),
            "runs_observed": len(votes),
            "runs_total": n,
            "tied": tied,
        }
    return primitives


# =============================================================================
# Derive -- deterministic, straight off the S2 rubric table
# =============================================================================

def _finger_consensus(primitives, doc):
    """
    The fingertip form held by at least _FINGER_CONSENSUS_MIN of the four fingers.

    Returns (form|None, disagree: bool). S5: the whole-hand label is derived, so
    "fingers disagree" is what MAKES a hand mixed -- it is a finding, not a shrug.
    """
    forms = [primitives[f"fingers.{k}.fingertip_form"]["value"] for k in doc.finger_keys]
    observed = [f for f in forms if f is not None]
    if not observed:
        return None, False                    # nothing observed is not disagreement
    top_form, top_n = Counter(observed).most_common(1)[0]
    if top_n >= _FINGER_CONSENSUS_MIN:
        return top_form, False
    return None, True


def _score_types(primitives, doc, finger_form):
    """
    Score every non-fallback type against its OWN S2 criteria.

    score = matched criteria / evaluable criteria, where a criterion is evaluable
    only when the type declares it AND we actually observed that primitive. A
    type is never penalised for a cell the doctrine leaves as an em-dash, and
    never credited for a primitive we could not see.
    """
    scored = {}
    for name, tc in doc.types.items():
        matched, evaluable, detail = [], [], []
        for slot in _DERIVE_SLOTS:
            if slot not in tc.criteria:
                continue                       # em-dash: this type declares nothing here
            if slot == "fingertip_form":
                observed = finger_form
                expected_tokens = tc.fingertip_tokens
                if observed is None or not expected_tokens:
                    continue
                evaluable.append(slot)
                hit = observed in expected_tokens
            else:
                observed = primitives[f"hand.{slot}"]["value"]
                if observed is None:
                    continue
                evaluable.append(slot)
                hit = observed == tc.criteria[slot]
            if hit:
                matched.append(slot)
            detail.append({
                "slot": slot,
                "expected": list(tc.fingertip_tokens) if slot == "fingertip_form" else tc.criteria[slot],
                "observed": observed,
                "match": hit,
            })
        scored[name] = {
            "score": round(len(matched) / len(evaluable), 3) if evaluable else 0.0,
            "matched": matched,
            "evaluable": evaluable,
            "detail": detail,
            "src": tc.src,
        }
    return scored


def _derive_type(primitives, doc):
    """Map observed primitives -> (dominant_type, modifiers, ranking, reasons, finger_form)."""
    finger_form, fingers_disagree = _finger_consensus(primitives, doc)
    scored = _score_types(primitives, doc, finger_form)
    ranking = sorted(scored.items(), key=lambda kv: (-kv[1]["score"], kv[0]))

    reasons = []
    dominant = None

    if fingers_disagree:
        reasons.append(
            "fingertip form differs across the fingers "
            f"(no {_FINGER_CONSENSUS_MIN}-of-{len(doc.finger_keys)} consensus)"
        )
    if not any(v["evaluable"] for v in scored.values()):
        reasons.append("no S2 criterion was observable on this image")
    else:
        top_name, top = ranking[0]
        second = ranking[1][1]["score"] if len(ranking) > 1 else 0.0
        if top["score"] < _DOMINANCE_FLOOR:
            reasons.append(
                f"best-matching type '{top_name}' scored {top['score']} "
                f"< floor {_DOMINANCE_FLOOR}"
            )
        elif (top["score"] - second) < _DOMINANCE_MARGIN:
            runners = [n for n, v in ranking[1:] if abs(v["score"] - top["score"]) < _DOMINANCE_MARGIN]
            reasons.append(
                f"'{top_name}' ({top['score']}) does not separate from "
                f"{runners} by the {_DOMINANCE_MARGIN} margin"
            )
        elif fingers_disagree:
            pass                              # already recorded; disagreement wins over a clean score
        else:
            dominant = top_name

    if dominant is None:
        dominant = doc.fallback_type

    # -- modifiers: secondary, doctrine-named signals that do not change the type --
    modifiers = []
    bp = primitives["hand.broad_point"]["value"]
    if bp is not None:
        # S2 note: broad-at-wrist -> palm points to fingers; broad-at-base -> slopes to wrist.
        modifiers.append(f"spatulate sub-signal: broad at {bp}")
    prop = primitives["hand.overall_proportion"]["value"]
    if prop is not None:
        modifiers.append(f"overall proportion: {prop}")
    ratio = primitives["hand.finger_palm_ratio"]["value"]
    if ratio is not None:
        modifiers.append(f"fingers {ratio} against the palm")
    spacing_vals = [primitives[f"inter_finger_spacing.{k}"]["value"] for k in doc.spacing_keys]
    if any(v is not None for v in spacing_vals):
        modifiers.append(
            "inter-finger spacing: "
            + ", ".join(f"{k}={v or 'unobserved'}" for k, v in zip(doc.spacing_keys, spacing_vals))
        )
    for name, sc in ranking[1:]:
        if sc["score"] > 0 and dominant != doc.fallback_type and sc["score"] >= _DOMINANCE_FLOOR:
            modifiers.append(f"secondary type signal: {name} ({sc['score']}, {sc['src']})")

    return dominant, modifiers, ranking, reasons, finger_form


def _overall_confidence(primitives, dominant, doc):
    """
    Disclosed heuristic, NOT a probability: mean self-consistency agreement over
    the primitives that were actually observed, halved when nothing dominated.
    Reported so a reader can see how it was built; never treat it as calibrated.
    """
    agreements = [p["agreement"] for p in primitives.values() if p["value"] is not None]
    mean_agreement = round(statistics.fmean(agreements), 3) if agreements else 0.0
    clarity = 0.5 if dominant == doc.fallback_type else 1.0
    return round(mean_agreement * clarity, 3), mean_agreement


def _disclosure_text(dominant, reasons, disagreement_flags, unobserved, confidence, doc):
    """S1/S5: the type is a DISCLOSED, user-correctable ASSUMPTION -- say so in words."""
    parts = []
    if dominant == doc.fallback_type:
        parts.append(
            f"Assumed hand type: {dominant} -- no single Cheiro type dominated the "
            "observations"
            + (" (" + "; ".join(reasons) + ")" if reasons else "")
            + "."
        )
    else:
        parts.append(f"Assumed hand type: {dominant}, derived from the observed hand features.")
    if disagreement_flags:
        parts.append(
            "Repeat observations of the same photo disagreed on: "
            + ", ".join(disagreement_flags)
            + " -- these are flagged rather than decided."
        )
    if unobserved:
        parts.append("Not clearly visible in this photo: " + ", ".join(unobserved) + ".")
    parts.append(
        f"Confidence {confidence} is a self-consistency measure, not an accuracy measure: "
        "no verified hand-type reference exists, so this reflects only how repeatably the "
        "same features were observed. This assumption is yours to correct."
    )
    return " ".join(parts)


# =============================================================================
# Result
# =============================================================================

@dataclass
class CheirognomyResult:
    image_hash: str
    label: str
    n_runs: int
    temperature: float
    quality_flag: str | None = None
    runs: list = field(default_factory=list)          # per-run on-menu payloads
    off_menu_observed: list = field(default_factory=list)
    primitives: dict = field(default_factory=dict)    # path -> {value, source_arm, confidence, ...}
    finger_consensus_form: str | None = None
    type_ranking: list = field(default_factory=list)
    dominant_type: str | None = None
    modifiers: list = field(default_factory=list)
    confidence: float = 0.0
    mean_agreement: float = 0.0
    disagreement_flags: list = field(default_factory=list)
    unobserved: list = field(default_factory=list)
    disclosed_assumption_text: str = ""

    @property
    def populated(self):
        return self.quality_flag is None and self.dominant_type is not None

    def to_capture_schema(self, doc):
        """
        Emit the S4 canonical shape. Populated primitives carry
        {value, source_arm, confidence}; S4 `_reserved` fields stay null.
        """
        if not self.populated:
            return None

        def cell(path):
            p = self.primitives[path]
            if p["value"] is None:
                return None
            return {"value": p["value"], "source_arm": p["source_arm"], "confidence": p["confidence"]}

        reserved = {
            "length_abs": None, "length_relative": None, "thickness": None, "lean": None,
            "straightness": None, "flexibility": None, "base_shape": None,
            "phalanges": [None, None, None], "joints": {"upper": None, "lower": None},
        }
        return {
            "hand_geometry": {
                "palm_squareness": cell("hand.palm"),
                "broad_point": cell("hand.broad_point"),
                "finger_palm_ratio": cell("hand.finger_palm_ratio"),
                "overall_proportion": cell("hand.overall_proportion"),
                "inter_finger_spacing": {
                    k: cell(f"inter_finger_spacing.{k}") for k in doc.spacing_keys
                },
                "joint_knottiness": cell("hand.joint_knottiness"),
                "nail_length": cell("hand.nail_length"),
                "finger_character": cell("hand.finger_character"),
            },
            "fingers": {
                k: {
                    "fingertip_form": cell(f"fingers.{k}.fingertip_form"),
                    "_reserved": dict(reserved),
                }
                for k in doc.finger_keys
            },
            "_derived": {
                "dominant_type": self.dominant_type,
                "modifiers": list(self.modifiers),
                "confidence": self.confidence,
                "quality_flag": self.quality_flag,
                "disclosed_assumption_text": self.disclosed_assumption_text,
            },
        }


def _rejected(image_hash, label, reason):
    """A hard capture failure: quality_flag set, and NOTHING else populated."""
    return CheirognomyResult(
        image_hash=image_hash,
        label=label,
        n_runs=_N_RUNS,
        temperature=_TEMPERATURE,
        quality_flag=reason,
        disclosed_assumption_text=(
            f"No hand type was derived from this image: {reason} "
            "No features were recorded -- a partial or guessed reading is not offered."
        ),
    )


# =============================================================================
# Public entry point
# =============================================================================

def classify_hand(image_bytes, label="hand", client=None, doctrine_path=None, n_runs=None):
    """
    Capture cheirognomy primitives from one hand image and derive its type.

    Args:
        image_bytes:   Raw bytes of the hand image.
        label:         Free-text tag for logging/reporting (e.g. "right"). Never
                       fed to the model -- it must not know which hand it sees.
        client:        Optional OpenAI client (injected in tests).
        doctrine_path: Optional override for the rubric file.
        n_runs:        Optional override for the self-consistency run count.

    Returns:
        CheirognomyResult. Either `quality_flag` is set and nothing else is
        populated, or a type was derived -- never both.

    Raises:
        CheirognomyDoctrineError: the rubric could not be parsed.
        VLMArmError:              every vision run failed (no silent fallback).
    """
    doc = load_doctrine(doctrine_path)
    runs_wanted = _N_RUNS if n_runs is None else int(n_runs)
    if runs_wanted < 1:
        raise VLMArmError(f"vlm_arm: n_runs must be >= 1, got {runs_wanted}.")

    image_hash = hashlib.md5(image_bytes).hexdigest() if image_bytes else "empty"

    # Ingestion / readability gate -- reused, not reimplemented.
    gate = validate_palm_image(image_bytes, label)
    if gate["hard_reject"]:
        return _rejected(image_hash, label, gate["reject_message"] or "image rejected by the quality gate.")

    client = client or OpenAI()
    payloads, off_menu, run_errors = [], [], []
    for i in range(runs_wanted):
        try:
            payload, run_off_menu = _classify_once(image_bytes, doc, client, i + 1)
        except VLMArmError as exc:
            logger.warning("vlm_arm: %s", exc)
            run_errors.append(str(exc))
            continue
        payloads.append(payload)
        for rec in run_off_menu:
            rec["run"] = i + 1
            off_menu.append(rec)

    if not payloads:
        raise VLMArmError(
            f"vlm_arm: all {runs_wanted} classify runs failed for label={label} "
            f"hash={image_hash}: {run_errors}"
        )

    hand_votes = sum(1 for p in payloads if p["hand_present"])
    if hand_votes * 2 <= len(payloads):
        return _rejected(
            image_hash, label,
            f"the model did not see a readable hand ({hand_votes}/{len(payloads)} runs reported one).",
        )

    primitives = _majority(payloads, doc)

    # Pervasive fabrication guard: if nothing at all survived the menus, there is
    # no honest capture here -- flag it rather than derive a type from silence.
    if all(p["value"] is None for p in primitives.values()):
        return _rejected(
            image_hash, label,
            "no observation survived the closed vocabulary "
            f"({len(off_menu)} off-menu values rejected, none coerced).",
        )

    dominant, modifiers, ranking, reasons, finger_form = _derive_type(primitives, doc)
    confidence, mean_agreement = _overall_confidence(primitives, dominant, doc)

    disagreement_flags = [
        path for path, p in primitives.items()
        if p["tied"] or (p["value"] is not None and p["agreement"] < 1.0)
    ]
    unobserved = [path for path, p in primitives.items() if p["value"] is None and not p["tied"]]

    if off_menu:
        modifiers.append(f"{len(off_menu)} off-menu value(s) rejected, never coerced")

    result = CheirognomyResult(
        image_hash=image_hash,
        label=label,
        n_runs=len(payloads),
        temperature=_TEMPERATURE,
        quality_flag=None,
        runs=payloads,
        off_menu_observed=off_menu,
        primitives=primitives,
        finger_consensus_form=finger_form,
        type_ranking=[(n, v["score"], v["matched"], v["evaluable"]) for n, v in ranking],
        dominant_type=dominant,
        modifiers=modifiers,
        confidence=confidence,
        mean_agreement=mean_agreement,
        disagreement_flags=disagreement_flags,
        unobserved=unobserved,
    )
    result.disclosed_assumption_text = _disclosure_text(
        dominant, reasons, disagreement_flags, unobserved, confidence, doc
    )
    return result


def compare_hands(left, right):
    """
    Cross-hand agreement between two INDEPENDENT captures. Extra consistency
    signal only -- the hands are NEVER merged into one reading (Cheiro reads them
    as different hands, and merging would erase that).
    """
    if not (left.populated and right.populated):
        return {
            "comparable": False,
            "reason": "one or both hands were rejected by the quality gate.",
            "type_agreement": None,
            "primitive_agreement": None,
            "per_primitive": {},
        }
    paths = [p for p in left.primitives if p in right.primitives]
    per = {}
    both_observed = 0
    same = 0
    for path in paths:
        lv = left.primitives[path]["value"]
        rv = right.primitives[path]["value"]
        agree = None
        if lv is not None and rv is not None:
            both_observed += 1
            agree = lv == rv
            same += int(agree)
        per[path] = {"left": lv, "right": rv, "agree": agree}
    return {
        "comparable": True,
        "reason": None,
        "type_agreement": left.dominant_type == right.dominant_type,
        "primitive_agreement": round(same / both_observed, 3) if both_observed else None,
        "both_observed": both_observed,
        "compared_paths": len(paths),
        "per_primitive": per,
    }
