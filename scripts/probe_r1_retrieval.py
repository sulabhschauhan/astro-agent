"""
scripts/probe_r1_retrieval.py

S67 R1 measure-first probe (diagnostics-only, throwaway): which query
TEMPLATE -- RAW field text, LABEL+QUALITY prose, or a DOCTRINE-
INTERROGATIVE phrasing -- surfaces per-feature interpretive doctrine
(vs. nomenclature/procedural text) from the Cheiro corpus, per
confirmed hand-description feature, before any production retrieval
redesign is coded.

Does NOT touch agent/interpretive/palm_reading.py or any production
module. Not a test. Classification of retrieved chunks as "doctrine"
vs. "nomenclature" is a design-chat human call -- this script only
reports which variant(s) retrieved the two known-doctrine pages
(p.134 life-line, p.163 fate-line, per Ring 3 pass-2 evidence,
diagnostics/ring3_chunks_S66_pass2.md); it does not label chunks
itself.

Confirmed descriptions (LEFT/RIGHT/HAND_DETAIL) transplanted VERBATIM
from diagnostics/ring3_palm_rubric_S66_pass2.md (S66 Task 15/16
frozen artifact) -- not retyped from memory.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.query_engine import search  # same import path as palm_reading.py

_CHEIRO_BOOK = "cheiroslanguageo00chei_1"
_N_RESULTS = 5
_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "latest_run.md"

# ─── Confirmed descriptions (verbatim, diagnostics/ring3_palm_rubric_S66_pass2.md) ───

_LEFT = """HAND SHAPE: Square palm, overall build is robust.

FINGERS: Fingers are long relative to the palm, appear straight, with rounded fingertips, moderate spacing.

THUMB: Medium relative size, set moderately low, wide angle from the palm.

LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.

HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.

HEART LINE: Present, deep, long, slightly curved, ends below the index finger, no clear breaks or forks.

FATE LINE: Barely visible.

OTHER LINES: Not clearly visible.

MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.

MARKS: No clear marks visible."""

_RIGHT = """HAND SHAPE: Square palm, overall build is medium.
FINGERS: Fingers are slightly longer than the palm, appear straight, with rounded fingertips, spaced moderately apart.
THUMB: Medium size, set moderately low, wide angle from the palm.
LIFE LINE: Present, deep, long, curves around the base of the thumb, no clear breaks or forks.
HEAD LINE: Present, deep, long, slightly curved, runs across the palm, no clear breaks or forks.
HEART LINE: Present, deep, slightly curved, ends below the index finger, no clear breaks or forks.
FATE LINE: Present, moderately deep, runs from the base of the palm towards the middle finger, no clear breaks or forks.
OTHER LINES: Sun line is faintly visible.
MOUNTS: Mount of Venus appears developed, other mounts are unremarkable.
MARKS: No clear marks visible."""

# Transplanted for completeness / audit trail; NOT parsed for feature
# extraction below (markdown-bullet format, structurally different from
# LEFT/RIGHT's flat "LABEL: text" fields). Per the absent-feature rule,
# "mount of jupiter" -- which is named ONLY here, never in LEFT/RIGHT's
# MOUNTS field -- is deliberately treated as "not observed" rather than
# parsed from this second format.
_HAND_DETAIL = """The image shows a hand with the following observable features:

- **Hand Shape**: The hand appears broad with a relatively square palm.
- **Finger Lengths**: The fingers are of moderate length. The index finger is slightly shorter than the middle finger, and the ring finger is slightly longer than the index finger. The little finger is noticeably shorter.
- **Thumb**: The thumb is of average length with a moderate angle of separation from the hand, indicating some flexibility.
- **Visible Lines**:
  - **Life Line**: A prominent line curves around the base of the thumb.
  - **Head Line**: Appears to be separate from the life line, running across the palm.
  - **Heart Line**: Curves across the top of the palm, below the fingers.
  - **Fate Line**: Not clearly visible in the image.
- **Mounts**: The mounts of Venus (base of the thumb) and Jupiter (below the index finger) appear slightly raised.
- **Markings**: There are no unusual markings or features visible.
- **Other Features**: There is a moderate amount of hair on the back of the hand and fingers.

These are the physical observations based on the image provided."""

# ─── Deterministic field parsing (no LLM) ──────────────────────────────

_FIELD_LINE = re.compile(r"^([A-Z][A-Z ]{2,}):\s*(.*)$")


def _parse_fields(block: str) -> dict[str, str]:
    """Line-based state machine: 'LABEL: text' lines, tolerant of both
    blank-line-separated (LEFT) and consecutive-line (RIGHT) layouts."""
    fields: dict[str, list[str]] = {}
    current: str | None = None
    for line in block.splitlines():
        m = _FIELD_LINE.match(line.strip())
        if m:
            current = m.group(1).strip()
            fields[current] = [m.group(2).strip()]
        elif line.strip() and current:
            fields[current].append(line.strip())
    return {k: " ".join(v).strip() for k, v in fields.items()}


def _extract_quality(text: str) -> str:
    """First non-generic descriptive clause: a bare leading 'Present' is
    uninformative on its own (true of every LIFE/HEAD/HEART/FATE LINE
    field here), so skip it and take the next clause; otherwise use the
    first clause as-is. Deterministic, no LLM -- 'quality' is not a
    formally defined field in the source data, this is the documented
    extraction rule."""
    clauses = [c.strip() for c in text.rstrip(".").split(",")]
    if clauses[0].lower() == "present" and len(clauses) > 1:
        return clauses[1].lower()
    return clauses[0].lower()


def _clean_quality_prefix(quality: str, feature: str) -> str:
    """Strip a leading self-referential mention of the feature name plus
    a linking verb (e.g. 'sun line is faintly visible' -> 'faintly
    visible') so variant (ii)'s '{quality} {feature}' template doesn't
    duplicate the feature name. Only fires when the feature name is
    genuinely the leading text; falls back to the unmodified quality
    otherwise."""
    q = quality.strip()
    fl = feature.lower()
    if q.lower().startswith(fl):
        q = q[len(fl):].strip()
    for verb in ("is ", "appears ", "are "):
        if q.lower().startswith(verb):
            q = q[len(verb):].strip()
            break
    return q or quality


def _sub_feature(left_fields: dict, right_fields: dict, field_label: str, needle: str) -> dict:
    """For a generic multi-purpose field (OTHER LINES, MOUNTS) that may
    or may not name a specific sub-feature (sun line; mount of venus /
    jupiter): raw text is kept unconditionally (variant i is about the
    verbatim field, regardless of relevance); a 'quality' source is only
    set when the sub-feature's name is actually present (case-
    insensitive substring match)."""
    rl = left_fields.get(field_label, "")
    rr = right_fields.get(field_label, "")
    return {
        "raw_left": rl or None,
        "raw_right": rr or None,
        "quality_left": rl if needle in rl.lower() else None,
        "quality_right": rr if needle in rr.lower() else None,
    }


def _build_feature_map(left_fields: dict, right_fields: dict) -> dict:
    plain = {
        "life line": "LIFE LINE",
        "head line": "HEAD LINE",
        "heart line": "HEART LINE",
        "fate line": "FATE LINE",
        "thumb": "THUMB",
        "fingers": "FINGERS",
        "markings/other features": "MARKS",
    }
    features: dict[str, dict] = {}
    for feature, label in plain.items():
        raw_l = left_fields.get(label)
        raw_r = right_fields.get(label)
        features[feature] = {
            "raw_left": raw_l,
            "raw_right": raw_r,
            "quality_left": raw_l,
            "quality_right": raw_r,
        }

    features["sun line"] = _sub_feature(left_fields, right_fields, "OTHER LINES", "sun")
    features["mount of venus"] = _sub_feature(left_fields, right_fields, "MOUNTS", "venus")
    features["mount of jupiter"] = _sub_feature(left_fields, right_fields, "MOUNTS", "jupiter")
    return features


# ─── Query construction (3 variants + negative control) ────────────────

_CANONICAL_FEATURES = [
    "life line", "head line", "heart line", "fate line", "sun line",
    "thumb", "fingers", "mount of venus", "mount of jupiter",
    "markings/other features",
]

_NEGATIVE_CONTROL_QUERY = "steam engine boiler maintenance"


def _build_queries(feature: str, data: dict) -> dict[str, str | None]:
    """Returns {'i': raw_query_or_None, 'ii': ..., 'iii': ...}.
    Query-noun used inside templates is a cleaned single/short phrase
    (feature.split('/')[0] for the compound 'markings/other features'
    key) -- the compound key stays intact as the canonical report label."""
    raw_left = data.get("raw_left")
    raw_right = data.get("raw_right")
    quality_left = data.get("quality_left")
    quality_right = data.get("quality_right")
    observed = bool(quality_left or quality_right)
    noun = feature.split("/")[0]

    if not observed:
        quality = "faint"
        return {
            "i": None,
            "ii": None,
            "iii": f"what does a {quality} {noun} signify — meaning and indications of a {quality} {noun}",
        }

    raw_parts = [p for p in (raw_left, raw_right) if p]
    raw_query = "; ".join(raw_parts)

    q_left = _clean_quality_prefix(_extract_quality(quality_left), feature) if quality_left else None
    q_right = _clean_quality_prefix(_extract_quality(quality_right), feature) if quality_right else None
    if q_left and q_right:
        quality = q_left if q_left == q_right else f"{q_left} / {q_right}"
    else:
        quality = q_left or q_right

    return {
        "i": raw_query,
        "ii": f"{quality} {noun}",
        "iii": f"what does a {quality} {noun} signify — meaning and indications of a {quality} {noun}",
    }


# ─── Retrieval ──────────────────────────────────────────────────────────

def _run_query(query_text: str) -> tuple[list[dict], str | None]:
    """Returns (results, error_str). On failure, results=[] and
    error_str carries the exception message; caller logs and continues."""
    try:
        return search(query_text, n_results=_N_RESULTS, book_name=_CHEIRO_BOOK), None
    except Exception as exc:  # noqa: BLE001 -- probe must survive any single bad query
        return [], f"{type(exc).__name__}: {exc}"


def _collapse(text: str, n: int = 120) -> str:
    return " ".join(text.split())[:n]


# ─── Report assembly ────────────────────────────────────────────────────

def main() -> None:
    left_fields = _parse_fields(_LEFT)
    right_fields = _parse_fields(_RIGHT)
    feature_map = _build_feature_map(left_fields, right_fields)

    lines: list[str] = []
    lines.append("# S67 R1 probe — per-feature retrieval template fingerprint")
    lines.append("")
    lines.append(
        "Measure-first probe for the S67 R1 per-feature retrieval redesign. "
        "Confirmed descriptions transplanted verbatim from "
        "`diagnostics/ring3_palm_rubric_S66_pass2.md` (cited, not retyped). "
        "Query construction and feature extraction are deterministic regex "
        "over the LEFT/RIGHT labeled fields, no LLM. Retrieval via "
        "`ingestion.query_engine.search`, `book_name=\"cheiroslanguageo00chei_1\"`, "
        "`n_results=5` — same call signature `palm_reading.py` uses."
    )
    lines.append("")
    lines.append(
        "**Scope note**: this script reports retrieval only. Whether a "
        "retrieved chunk is genuine interpretive *doctrine* vs. "
        "nomenclature/procedural text is NOT classified here — that "
        "judgment is a design-chat human call. Section 4 below reports "
        "only literal presence of the two known-doctrine pages (p.134 "
        "life-line, p.163 fate-line, per `ring3_chunks_S66_pass2.md`) in "
        "each result set."
    )
    lines.append("")

    lines.append("## 1. Query strings per feature × variant")
    lines.append("")
    lines.append(
        "| Feature | Observed? | (i) RAW | (ii) LABEL+QUALITY | (iii) DOCTRINE-INTERROGATIVE |"
    )
    lines.append("|---|---|---|---|---|")

    all_queries: list[tuple[str, str, str]] = []  # (feature, variant, query_text)
    per_feature_queries: dict[str, dict[str, str | None]] = {}

    for feature in _CANONICAL_FEATURES:
        data = feature_map[feature]
        queries = _build_queries(feature, data)
        per_feature_queries[feature] = queries
        observed = queries["i"] is not None
        lines.append(
            f"| {feature} | {'yes' if observed else 'NOT OBSERVED'} "
            f"| {queries['i'] or '_(skipped — not observed)_'} "
            f"| {queries['ii'] or '_(skipped — not observed)_'} "
            f"| {queries['iii']} |"
        )
        for variant, q in queries.items():
            if q is not None:
                all_queries.append((feature, variant, q))

    lines.append("")
    lines.append(f"Negative control query: `{_NEGATIVE_CONTROL_QUERY}`")
    lines.append("")

    lines.append("## 2. Per-query retrieval results")
    lines.append("")

    doctrine_hits: dict[str, list[str]] = {f: [] for f in _CANONICAL_FEATURES}
    errors: list[str] = []

    variant_titles = {"i": "RAW", "ii": "LABEL+QUALITY", "iii": "DOCTRINE-INTERROGATIVE"}

    for feature, variant, query_text in all_queries:
        lines.append(f"### {feature} — variant ({variant}) {variant_titles[variant]}")
        lines.append(f"Query: `{query_text}`")
        lines.append("")
        results, error = _run_query(query_text)
        if error:
            errors.append(f"{feature} / ({variant}): {error}")
            lines.append(f"**ERROR** — {error}")
            lines.append("")
            continue
        lines.append("| rank | page_ref | score | first 120 chars |")
        lines.append("|---|---|---|---|")
        for rank, r in enumerate(results, 1):
            lines.append(
                f"| {rank} | {r['page_ref']} | {r['score']:.4f} | {_collapse(r['text'])} |"
            )
            if r["page_ref"] == 134:
                doctrine_hits[feature].append(f"({variant}) rank {rank}, p.134")
            if r["page_ref"] == 163:
                doctrine_hits[feature].append(f"({variant}) rank {rank}, p.163")
        lines.append("")

    lines.append("## 3. Negative control")
    lines.append("")
    lines.append(f"Query: `{_NEGATIVE_CONTROL_QUERY}`")
    lines.append("")
    results, error = _run_query(_NEGATIVE_CONTROL_QUERY)
    if error:
        errors.append(f"negative control: {error}")
        lines.append(f"**ERROR** — {error}")
    else:
        lines.append("| rank | page_ref | score | first 120 chars |")
        lines.append("|---|---|---|---|")
        for rank, r in enumerate(results, 1):
            lines.append(
                f"| {rank} | {r['page_ref']} | {r['score']:.4f} | {_collapse(r['text'])} |"
            )
    lines.append("")

    lines.append("## 4. Summary — p.134 / p.163 literal presence by feature × variant")
    lines.append("")
    lines.append(
        "Report only — no doctrine-vs-nomenclature classification performed here."
    )
    lines.append("")
    lines.append("| Feature | p.134/p.163 hits |")
    lines.append("|---|---|")
    for feature in _CANONICAL_FEATURES:
        hits = doctrine_hits[feature]
        lines.append(f"| {feature} | {'; '.join(hits) if hits else 'none'} |")
    lines.append("")

    if errors:
        lines.append("### Query errors (logged, probe continued)")
        lines.append("")
        for e in errors:
            lines.append(f"- {e}")
        lines.append("")

    lines.append("## 5. Rider — unconsumed face/body test images removed")
    lines.append("")
    lines.append(
        "`git rm` on `data/test_images/` files whose filename contains "
        "\"face\" or \"body\" (case-insensitive) and have no consuming "
        "test/production surface. Palm fixture images "
        "(`palm_left_test.jpg`, `palm_right_test.jpg`) and `Back Hand.jpeg` "
        "(filename matches neither criterion) untouched."
    )
    lines.append("")
    lines.append("- `data/test_images/Face.jpeg` — removed")
    lines.append("- `data/test_images/Body.jpeg` — removed")
    lines.append("")

    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {_REPORT_PATH} ({len(all_queries) + 1} queries run, {len(errors)} errors)")


if __name__ == "__main__":
    main()
