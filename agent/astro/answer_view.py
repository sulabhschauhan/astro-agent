"""
Astro Agent -- USER-FACING ANSWER VIEW.

PATH B. Splits the one thing `pipeline._render` was doing into two, because it
was written as a lab renderer and is now what a person reads.

THE SPLIT
---------
  LOG surface  -- everything: verse ids, silent_on, gate stats, payload sizes,
                  timings, the interpreter's raw JSON. Goes to qa_capture.
  USER surface -- this module: what the chart says, in words a person who has
                  never read BPHS can follow.

Evidence this was needed (live run, S129): the user saw six lines of
`Not addressed: Whether the 10th lord is exalted... Combinations depending on
Atmakaraka, Amatyakaraka, Karakamsa/Arudha or divisional dignities
(ch40_s001-ch40_s015)...` appended to their career answer. Every word of that
is real and useful -- to us. To them it is noise that buries the answer.

WHAT THIS MODULE DOES, AND DELIBERATELY DOES NOT DO
---------------------------------------------------
DOES: drop internal diagnostics from the user's view, turn verse ids into a
human source line naming the chapter, normalise the classical third person
("the native") into second person, and append the capability gate's plain
decline notes.

DOES NOT: rewrite, soften, summarise or re-order the claims themselves. The
claim text is the Interpreter's, cited and gate-checked; paraphrasing it here
would put unverified words in front of the user with no citation behind them --
the exact failure the whole architecture exists to prevent. Jargon INSIDE a
claim is fixed in the interpreter's own voice instructions, upstream, not by
regex here. The only text transform permitted below is the pronoun swap, which
changes who a sentence is addressed to and nothing about what it asserts.

Python 3.11.
"""
from __future__ import annotations

import json
import os
import re
from typing import Iterable, Optional

__all__ = ["ANSWER_VIEW_VERSION", "render_user_answer", "source_line"]

ANSWER_VIEW_VERSION = "answer-view-1.0"

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CHAPTER_INDEX_PATH = os.path.join(_REPO_ROOT, "data", "chapter_index_bphs.json")

_BOOK_LABEL = "Brihat Parashara Hora Shastra"

# Classical third person -> second person. ORDER MATTERS: longest first, so
# "the native's" is consumed before "the native".
#
# SCOPE GUARD: this list is deliberately tiny and covers only forms that are
# unambiguously the chart-owner. It does NOT touch "one will", which can be a
# genuine generic in a verse paraphrase, and it never rewrites a noun that
# might name a third party the question was about (a child, a spouse) -- those
# read correctly in the third person and swapping them would be wrong.
_PRONOUN_SWAPS: tuple[tuple[str, str], ...] = (
    ("the native's", "your"),
    ("the native is", "you are"),
    ("the native will be", "you will be"),
    ("the native will", "you will"),
    ("the native has", "you have"),
    ("the native", "you"),
    ("the subject's", "your"),
    ("the subject", "you"),
)

_CITATION_RE = re.compile(r"\s*\[[A-Za-z0-9_.\-]+\]")

_chapter_titles: Optional[dict[str, str]] = None


def _load_chapter_titles() -> dict[str, str]:
    """unit key -> human chapter label, for BOTH the full and stripped id forms.

    `payload_builder` hands the interpreter a stripped id (`ch34_s011`) when
    that stem is unique across books, and the full one (`bphs1_ch34_s011`)
    when it is not, so both spellings must resolve here or a real citation
    silently loses its chapter name.
    """
    global _chapter_titles
    if _chapter_titles is not None:
        return _chapter_titles

    titles: dict[str, str] = {}
    try:
        with open(_CHAPTER_INDEX_PATH, encoding="utf-8") as fh:
            index = json.load(fh)
        units = index.get("units") or []
    except (OSError, ValueError, AttributeError):
        _chapter_titles = {}
        return _chapter_titles

    stems: dict[str, int] = {}
    for u in units:
        uid = u.get("unit_id") or ""
        stem = re.sub(r"^bphs\d+_", "", uid)
        stems[stem] = stems.get(stem, 0) + 1

    for u in units:
        uid = u.get("unit_id") or ""
        label = _usable_title(u.get("title_clean") or u.get("title_raw") or "")
        stem = re.sub(r"^bphs\d+_", "", uid)
        num = re.match(r"ch(\d+)$", stem)
        pretty = f"ch. {num.group(1)}" if num else stem.replace("_", " ")
        if label:
            pretty = f"{pretty} — {label}"
        titles[uid] = pretty
        if stems.get(stem) == 1:
            titles[stem] = pretty

    _chapter_titles = titles
    return titles


# THRESHOLD: chapter-title usability.
#   JUSTIFICATION -- `title_raw` is OCR'd from a chapter heading and 20 of the
#   100 units carry a run-on sentence instead, where the heading was missed and
#   body text was captured (measured 2026-09-12: e.g. bphs1_ch39's title_raw is
#   "and endowed with ncgligible wealth. One born with Vosi yoga will be
#   skilful..."). Real headings in this index run 11-44 chars ("The Creation",
#   "Yoga Karakas", "Effects Of The Bhava Lords"); the 20 broken ones are 65-120
#   and all contain mid-string sentence punctuation. 60 chars sits clear of both
#   populations rather than between them, and the punctuation test catches the
#   one broken title under 60 ("due to Nabhasa yogas etc. be also known...").
#   `title_clean` is empty for every unit today, so `title_raw` is the only
#   source; do not "fix" that by dropping the fallback.
#   SCOPE GUARD -- display only. A rejected title costs the reader the chapter
#   NAME, never the chapter NUMBER, and never affects retrieval, citation or
#   the claim itself. Failing to "ch. 39" is correct behaviour, not degradation.
#   TUNING NOTE -- re-measure against the index if the chapter index is ever
#   rebuilt; if a future ingestion populates `title_clean` properly, this guard
#   should go quiet on its own rather than being deleted.
_MAX_TITLE_CHARS = 60
_SENTENCE_PUNCT_RE = re.compile(r"[.;:]\s")


def _usable_title(raw: str) -> str:
    """Return the heading if it looks like a heading, else "" (number only)."""
    t = (raw or "").strip()
    if not t or len(t) > _MAX_TITLE_CHARS or _SENTENCE_PUNCT_RE.search(t):
        return ""
    return t


def _unit_of(segment_id: str) -> str:
    """`ch34_s011` -> `ch34`; `bphs1_ch34_s011` -> `bphs1_ch34`."""
    return re.sub(r"_s\d+$", "", segment_id or "")


def source_line(cited_ids: Iterable[str]) -> str:
    """One human source line for every chapter the answer drew on.

    Verse-level ids mean nothing to a reader and a list of twelve of them means
    less than nothing, so this collapses to unique chapters, in first-cited
    order.
    """
    titles = _load_chapter_titles()
    seen: list[str] = []
    for sid in cited_ids or []:
        unit = _unit_of(sid)
        label = titles.get(unit) or unit
        if label and label not in seen:
            seen.append(label)
    if not seen:
        return ""
    return f"Source: {_BOOK_LABEL} — " + "; ".join(seen)


def _to_second_person(text: str) -> str:
    """Swap the classical third person for direct address, case-insensitively,
    preserving sentence-initial capitalisation."""
    out = text
    for src, dst in _PRONOUN_SWAPS:
        out = re.sub(re.escape(src), dst, out, flags=re.IGNORECASE)
    # Re-capitalise anything now starting a sentence.
    out = re.sub(r"(^|(?<=[.!?]\s))([a-z])", lambda m: m.group(1) + m.group(2).upper(), out)
    return out


def render_user_answer(result: dict) -> str:
    """Turn a pipeline result into what the user reads.

    Args:
        result: the dict from pipeline.answer_question.

    Returns:
        Plain markdown. Never raises -- on any internal problem it falls back
        to the pipeline's own `answer` string, because showing the lab
        rendering beats showing nothing.
    """
    try:
        kept = result.get("kept_claims") or []
        declines = [m for _, m in (result.get("declined") or [])]

        # Stage 5b (S131). When the composer ran and produced blocks, IT is
        # the user surface: it has already ordered the claims and written
        # them in plain English, and its output passed the invented-fact
        # check in `composer._verify`. The S129b no-rewrite rule still binds
        # THIS module -- nothing below rewrites anything; the rewriting is
        # the composer's, mechanically checked, not ours.
        composed = result.get("composed") or {}
        if composed.get("composed") and composed.get("blocks"):
            from agent.astro import composer as _composer

            body = _composer.render(composed)
            if body.strip():
                cited_ids: list[str] = []
                for b in composed["blocks"]:
                    for sid in (b.get("segment_ids") or []):
                        if sid not in cited_ids:
                            cited_ids.append(sid)
                parts = [body] + declines
                src = source_line(cited_ids)
                if src:
                    parts.append(f"*{src}*")
                return "\n\n".join(parts)

        if not kept:
            # Nothing survived. Say so once, plainly, then the specific
            # capability limits. The per-verse reasons stay in the log.
            head = ("I can't answer this from your chart and the classical "
                    "text I have. Nothing in the verses that apply to your "
                    "placements addresses it directly.")
            return "\n\n".join([head] + declines) if declines else head

        cited: list[str] = []
        lines: list[str] = []
        for c in kept:
            statement = _CITATION_RE.sub("", str(c.get("statement") or "")).strip()
            if not statement:
                continue
            lines.append(f"- {_to_second_person(statement)}")
            for sid in (c.get("segment_ids") or []):
                if sid not in cited:
                    cited.append(sid)

        if not lines:
            return result.get("answer") or ""

        parts = ["\n".join(lines)]
        parts += declines
        src = source_line(cited)
        if src:
            parts.append(f"*{src}*")
        return "\n\n".join(parts)

    except Exception:  # noqa: BLE001 -- presentation must never lose the answer
        return result.get("answer") or ""
