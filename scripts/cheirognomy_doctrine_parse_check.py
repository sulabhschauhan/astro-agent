"""
scripts/cheirognomy_doctrine_parse_check.py

Prove agent/cheirognomy/vlm_arm.py's doctrine parser against the LIVE rubric
data/palm_rules/_doctrine/CHEIROGNOMY_HAND_TYPE.md.

NO API CALLS. Imports the parser, dumps every closed menu it builds, and asserts
each expected set against the doctrine. On ANY mismatch the raw markdown span is
printed beside what the regex actually captured, so a parse error is visible
rather than silent.

Writes diagnostics/latest_run.md (OVERWRITE, per the diagnostics convention).
Exit code 0 = all assertions passed, 1 = at least one failed.
"""

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from agent.cheirognomy.vlm_arm import (  # noqa: E402
    DOCTRINE_PATH,
    UNREADABLE,
    _DERIVE_SLOTS,
    _HAND_PRIMITIVES,
    _sections,
    _stem_match,
    load_doctrine,
)

REPORT_PATH = _REPO_ROOT / "diagnostics" / "latest_run.md"

# What the doctrine is expected to yield. These are the ASSERTIONS, written out
# independently of the parser so a parser bug cannot satisfy them by accident.
EXPECTED = {
    "type_names": {"elementary", "square", "spatulate", "philosophic", "conic", "psychic", "mixed"},
    "fallback_type": "mixed",
    "fingertip_form": {"square", "conic", "spatulate", "pointed", "knotty"},
    "finger_keys": ("jupiter", "saturn", "apollo", "mercury"),
    "spacing_keys": ("1_2", "2_3", "3_4"),
    "inter_finger_spacing": {"tight", "wide"},
    "broad_point": {"wrist", "base"},
    "overall_proportion": {"long-narrow", "broad"},
    "finger_palm_ratio": {"long", "short"},
}

# Where to look in the raw markdown when an assertion fails.
FAIL_ANCHORS = {
    "fingertip_form": (3, r"fingertip form"),
    "inter_finger_spacing": (7, r"="),
    "broad_point": (4, r"broad_point"),
    "overall_proportion": (3, r"overall .* vs "),
    "finger_palm_ratio": (2, r"^\|"),
    "finger_keys": (4, r'"fingers"'),
    "spacing_keys": (4, r"inter_finger_spacing"),
    "type_names": (2, r"^\|"),
    "fallback_type": (2, r"FALLBACK"),
}

results = []   # (name, passed, expected, actual, note)
raw_text = DOCTRINE_PATH.read_text(encoding="utf-8")
raw_sections = _sections(raw_text)


def raw_span(section_no, pattern, limit=6):
    """The raw markdown lines a failed assertion should be read against."""
    section = raw_sections.get(section_no)
    if section is None:
        return [f"(section S{section_no} ABSENT from the doctrine)"]
    hits = [ln for ln in section.splitlines() if re.search(pattern, ln)]
    if not hits:
        return [f"(no line in S{section_no} matches {pattern!r})"]
    return hits[:limit]


def check(name, actual, expected, ordered=False):
    if ordered:
        passed = tuple(actual) == tuple(expected)
    else:
        passed = set(actual) == set(expected)
    results.append((name, passed, expected, actual))
    return passed


def check_true(name, passed, detail):
    results.append((name, bool(passed), "true", detail))
    return bool(passed)


# ---------------------------------------------------------------------------
# Parse
# ---------------------------------------------------------------------------
parse_error = None
doc = None
try:
    doc = load_doctrine()
except Exception as exc:                       # noqa: BLE001 - report, do not swallow
    parse_error = f"{type(exc).__name__}: {exc}"

lines = []
w = lines.append

w("# Cheirognomy doctrine-parser verification")
w("")
w(f"- Source rubric: `{DOCTRINE_PATH.relative_to(_REPO_ROOT).as_posix()}` "
  f"({len(raw_text)} bytes, {len(raw_text.splitlines())} lines)")
w(f"- Sections parsed: {sorted(raw_sections)}")
w("- Mode: **NO API CALLS** — parser only, no VLM probe, no commit.")
w("")

if parse_error is not None:
    w("## FATAL — the parser raised")
    w("")
    w("```")
    w(parse_error)
    w("```")
    w("")
    w("Raw S2 table as it stands in the file:")
    w("")
    w("```")
    for ln in raw_span(2, r"^\|", limit=12):
        w(ln)
    w("```")
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(parse_error)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------
all_type_names = set(doc.types) | {doc.fallback_type}
check("type_names (S2, 7 types incl. fallback)", all_type_names, EXPECTED["type_names"])
check_true(
    "fallback_type is 'mixed' and is EXCLUDED from the scored types",
    doc.fallback_type == EXPECTED["fallback_type"] and doc.fallback_type not in doc.types,
    f"fallback={doc.fallback_type!r}, scored types={sorted(doc.types)}",
)
check("fingertip_form menu (S3, closed)", doc.menus["fingertip_form"], EXPECTED["fingertip_form"])
check("finger identity keys (S4)", doc.finger_keys, EXPECTED["finger_keys"], ordered=True)
check_true(
    "thumb + nail are ABSENT from the finger keys (S4 scope)",
    not any(k in {"thumb", "nail", "nails"} for k in doc.finger_keys),
    f"finger_keys={doc.finger_keys}",
)
check("inter_finger_spacing menu (S7)", doc.menus["inter_finger_spacing"], EXPECTED["inter_finger_spacing"])
check("spacing gap keys (S4)", doc.spacing_keys, EXPECTED["spacing_keys"], ordered=True)
check("broad_point menu (S4 annotation)", doc.menus["broad_point"], EXPECTED["broad_point"])
check("overall_proportion menu (S3)", doc.menus["overall_proportion"], EXPECTED["overall_proportion"])
check("finger_palm_ratio menu (S2 length poles)", doc.menus["finger_palm_ratio"], EXPECTED["finger_palm_ratio"])

check_true(
    "every parsed menu is non-empty",
    all(len(v) > 0 for v in doc.menus.values()),
    {k: len(v) for k, v in doc.menus.items()},
)
check_true(
    "every scored type declares at least one criterion",
    all(len(tc.criteria) > 0 for tc in doc.types.values()),
    {n: len(tc.criteria) for n, tc in doc.types.items()},
)
check_true(
    "every type that declares a Fingertips cell maps onto the closed menu",
    all(
        tc.fingertip_tokens
        for tc in doc.types.values()
        if "fingertip_form" in tc.criteria
    ),
    {n: tc.fingertip_tokens for n, tc in doc.types.items() if "fingertip_form" in tc.criteria},
)
check_true(
    "every fingertip token a type maps to is ON the closed menu",
    all(
        set(tc.fingertip_tokens) <= set(doc.menus["fingertip_form"])
        for tc in doc.types.values()
    ),
    {n: tc.fingertip_tokens for n, tc in doc.types.items()},
)
check_true(
    "spatulate is REACHABLE from its S2 cell (the stem-match case)",
    "spatulate" in doc.types["spatulate"].fingertip_tokens,
    f"cell={doc.types['spatulate'].criteria.get('fingertip_form')!r} -> "
    f"{doc.types['spatulate'].fingertip_tokens}",
)
check_true(
    "no two fingertip menu words stem-collide (the _STEM_MIN scope guard)",
    not any(
        _stem_match(a, b)
        for i, a in enumerate(doc.menus["fingertip_form"])
        for b in doc.menus["fingertip_form"][i + 1:]
    ),
    list(doc.menus["fingertip_form"]),
)
check_true(
    f"the '{UNREADABLE}' sentinel collides with no doctrine menu value",
    all(UNREADABLE not in v for v in doc.menus.values()),
    UNREADABLE,
)
check_true(
    "every derive slot has a menu backing it",
    all(slot in doc.menus for slot in _DERIVE_SLOTS),
    _DERIVE_SLOTS,
)
check_true(
    "every prompted hand primitive has a menu backing it",
    all(p in doc.menus for p in _HAND_PRIMITIVES),
    _HAND_PRIMITIVES,
)

# ---------------------------------------------------------------------------
# Dump
# ---------------------------------------------------------------------------
w("## 1. S2 type table — parsed criteria per type")
w("")
w("`fallback` = assigned only when no single type dominates (S2 note, S5). Its row carries")
w("meta-text, not criteria, so it is excluded from scoring by construction.")
w("")
w("| # | type | src | palm | fingertip_form (cell -> menu tokens) | finger_character | joint_knottiness | nail_length |")
w("|---|---|---|---|---|---|---|---|")
for i, (name, tc) in enumerate(sorted(doc.types.items()), start=1):
    tips_cell = tc.criteria.get("fingertip_form")
    tips = f"`{tips_cell}` -> {list(tc.fingertip_tokens)}" if tips_cell else "— (declares none)"
    w("| {} | **{}** | {} | {} | {} | {} | {} | {} |".format(
        i, name, tc.src,
        tc.criteria.get("palm") or "—",
        tips,
        tc.criteria.get("finger_character") or "—",
        tc.criteria.get("joint_knottiness") or "—",
        tc.criteria.get("nail_length") or "—",
    ))
w("| {} | **{}** | — | *fallback only, no criteria parsed* | | | | |".format(
    len(doc.types) + 1, doc.fallback_type))
w("")
w(f"Types parsed: **{len(doc.types)} scored + 1 fallback = {len(all_type_names)}**.")
w("")

w("## 2. Closed menus the parser built")
w("")
w("Every value below was READ from the rubric — none is hardcoded in `vlm_arm.py`.")
w(f"The model may additionally answer `{UNREADABLE}` for any field (engineering sentinel,")
w("declared in the module, deliberately not a doctrine word).")
w("")
w("| menu | source | n | values |")
w("|---|---|---|---|")
_MENU_SRC = {
    "fingertip_form":       "S3 brace-menu (declared closed)",
    "palm":                 "S2 `Palm` column cells",
    "finger_character":     "S2 `Fingers/length` column cells",
    "joint_knottiness":     "S2 `Joints` column cells",
    "nail_length":          "S2 `Nails` column cells",
    "broad_point":          "S4 `broad_point` annotation",
    "overall_proportion":   "S3 'overall X vs Y'",
    "finger_palm_ratio":    "S2 length poles in `Fingers/length`",
    "inter_finger_spacing": "S7 spread signal",
}
for key in _MENU_SRC:
    vals = doc.menus[key]
    w("| `{}` | {} | {} | {} |".format(
        key, _MENU_SRC[key], len(vals), ", ".join(f"`{v}`" for v in vals)))
w("")
w("**Per-finger keys (S4):** " + ", ".join(f"`{k}`" for k in doc.finger_keys)
  + " — thumb excluded (own chapter), nails not a finger key.")
w("**Spacing gap keys (S4):** " + ", ".join(f"`{k}`" for k in doc.spacing_keys))
w("")

w("## 3. Assertions")
w("")
passed_n = sum(1 for _, p, _, _ in results if p)
w(f"**{passed_n}/{len(results)} passed.**")
w("")
w("| # | assertion | result | expected | actual |")
w("|---|---|---|---|---|")
for i, (name, passed, expected, actual) in enumerate(results, start=1):
    def fmt(x):
        if isinstance(x, (set, frozenset)):
            return ", ".join(f"`{v}`" for v in sorted(x))
        if isinstance(x, (tuple, list)):
            return ", ".join(f"`{v}`" for v in x)
        if isinstance(x, dict):
            return "; ".join(f"{k}={v}" for k, v in x.items())
        return f"`{x}`"
    w("| {} | {} | {} | {} | {} |".format(
        i, name, "PASS" if passed else "**FAIL**", fmt(expected), fmt(actual)))
w("")

failures = [(n, e, a) for n, p, e, a in results if not p]
if failures:
    w("## 4. FAILURES — raw markdown beside what the regex captured")
    w("")
    for name, expected, actual in failures:
        w(f"### {name}")
        w("")
        w(f"- expected: `{expected}`")
        w(f"- regex captured: `{actual}`")
        key = next((k for k in FAIL_ANCHORS if k in name), None)
        if key:
            sec, pattern = FAIL_ANCHORS[key]
            w(f"- raw doctrine span (S{sec}, lines matching `{pattern}`):")
            w("")
            w("```")
            for ln in raw_span(sec, pattern):
                w(ln)
            w("```")
        else:
            w("- (no raw-span anchor registered for this assertion)")
        w("")
else:
    w("## 4. FAILURES")
    w("")
    w("None — every expected set matched the doctrine.")
    w("")

w("## 5. Parse defects this pass found and fixed")
w("")
w("Found 2026-08-21 by running these assertions against the live file; all three were silent")
w("before the assertions existed — the parser returned plausible-looking wrong values, not errors.")
w("")
w("| # | defect | what the regex actually captured | fix |")
w("|---|---|---|---|")
w("| 1 | `_braced_set(S4, 'broad_point')` scanned FORWARD from the first mention. S4 names "
  "`broad_point` inside the JSON schema block long before the annotation that declares its menu. "
  "| `inter_finger_spacing`'s JSON object: `1_2, 2_3, 3_4` | skip colon-bearing braces "
  "(a JSON object is not a value menu) |")
w("| 2 | Same anchor, after fix 1: the next colon-free brace was the `_provenance` line's. "
  "| `value, source_arm, confidence` | exclude fenced code blocks outright, and scope the search "
  "to the anchor's own bullet |")
w("| 3 | Type-cell -> closed-menu mapping used plain substring containment. The Spatulate row's "
  "cell reads `spatula-flared/flattened`; the menu word is `spatulate`. | `()` — **spatulate was "
  "unreachable as a fingertip form** | prefix stem-match with `_STEM_MIN=5`, plus a load-time "
  "guard that raises if two menu words ever stem-collide |")
w("")
w("Defect 3 is the load-bearing one: it made `spatulate` — one of the five fingertip forms — "
  "impossible to credit to any type, so the spatulate hand could never have been derived from "
  "a fingertip observation. That is a silent-miss of exactly the class CLAUDE.md's VOCABULARY "
  "CONTRACT law names: registry-legal but not reachable.")
w("")

w("## 6. Findings for review — structural, NOT parse errors")
w("")
w("These are properties of the rubric-as-parsed that the assertions correctly pass but that")
w("affect how the derive step will behave. Flagging rather than silently shipping.")
w("")

w("**(a) Uneven criteria denominators across types.** `_score_types` normalises "
  "matched/evaluable, so a type declaring few criteria can reach a perfect score far more "
  "cheaply than one declaring many:")
w("")
w("| type | criteria declared | slots |")
w("|---|---|---|")
for name, tc in sorted(doc.types.items(), key=lambda kv: len(kv[1].criteria)):
    w(f"| {name} | **{len(tc.criteria)}** | {', '.join(sorted(tc.criteria))} |")
w("")
_min_t = min(doc.types.items(), key=lambda kv: len(kv[1].criteria))
_max_t = max(doc.types.items(), key=lambda kv: len(kv[1].criteria))
w(f"`{_min_t[0]}` needs {len(_min_t[1].criteria)} matches for a 1.0; "
  f"`{_max_t[0]}` needs {len(_max_t[1].criteria)}. Against `_DOMINANCE_FLOOR=0.50` and "
  f"`_DOMINANCE_MARGIN=0.15` this systematically favours the sparse types "
  f"(`{_min_t[0]}`). UNMEASURED — whether it matters depends on how often the sparse types' "
  "few criteria are observable at all. First evidence comes from the VLM probe.")
w("")

_multi = {n: tc.fingertip_tokens for n, tc in doc.types.items() if len(tc.fingertip_tokens) > 1}
if _multi:
    w("**(b) One fingertip observation can credit two types.** " + "; ".join(
        f"`{n}` maps to {list(v)}" for n, v in _multi.items())
      + ". So an observed `pointed` credits both of those types at once. This is faithful to the "
        "cell text and matches S2's own note that conic <-> psychic is a continuum — recorded so "
        "the resulting near-ties in the ranking read as expected, not as a scoring bug.")
    w("")

_phrase_menus = [k for k in ("palm", "finger_character")
                 if any(len(v.split()) > 2 for v in doc.menus[k])]
if _phrase_menus:
    w("**(c) Two menus are whole verbatim cell phrases, one per type.** " + ", ".join(
        f"`{k}` ({len(doc.menus[k])} values)" for k in _phrase_menus)
      + ". Values like `square at wrist + at finger-base` are near-1:1 with type identity, so "
        "asking the VLM to select one is closer to asking it to name the type than to observe a "
        "primitive. The model is never told which type a phrase belongs to, and the phrases are "
        "the doctrine's own words — splitting them into shorter tokens would be the paraphrase "
        "the vocabulary contract forbids. Flagged as a design consequence to watch in the probe: "
        "if `palm` and `finger_character` always co-vote for the same type, the derive step has "
        "fewer independent signals than its 5 slots suggest.")
    w("")

_no_tips = [n for n, tc in doc.types.items() if "fingertip_form" not in tc.criteria]
if _no_tips:
    w(f"**(d) {len(_no_tips)} type(s) declare no fingertip cell** (`{'`, `'.join(sorted(_no_tips))}`), "
      "so fingertip form — the one primitive S3 calls a discriminator and the only per-finger "
      "field captured — can never credit them. They are reachable only through palm / "
      "finger_character / joints / nails.")
    w("")

w("## 7. Verdict")
w("")
if failures:
    w(f"**FAIL — {len(failures)} assertion(s) did not match the doctrine.** The parser and the")
    w("rubric have drifted apart; see the raw spans above before touching either.")
else:
    w("**PASS — the parser reproduces the doctrine's vocabulary exactly.**")
    w("")
    w("The vocabulary contract holds: the closed menus offered to the VLM are the rubric's own")
    w("words, and the derive criteria are the S2 table's own cells. No VLM probe was run and no")
    w("API call was made — reproducibility and derive behaviour remain UNMEASURED.")
w("")

REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(f"{passed_n}/{len(results)} assertions passed -> {REPORT_PATH}")
for name, passed, expected, actual in results:
    if not passed:
        print(f"  FAIL {name}: expected={expected} actual={actual}")
sys.exit(1 if failures else 0)
