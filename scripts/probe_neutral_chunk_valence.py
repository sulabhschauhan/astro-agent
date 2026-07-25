"""
scripts/probe_neutral_chunk_valence.py

S71 diagnostic probe -- PHASE 1 ONLY (throwaway, read-only, no production
code touched, no Stage-1 extraction run).

Purpose: the S71 reversal found `cheiroslanguageo00chei_1_p145_c0` (a
neutral/disjunctive "intellectual strength OR weakness" naming/taxonomy
chunk) mis-labeled `valence="supports"` by Stage 1 (`claim_extraction.py`)
across THREE consecutive Ring 3 passes (pass-3 Run A row 8, pass-4 Run A
row 4, pass-5 Run A row 5), plus a SECOND instance of the same
self-contradicting-label pattern on `p139_c0` (pass-5 Run A row 3, "When
the line of life sweeps far out..." -- a conditional claim labeled
"supports" instead of "conditional"). This script identifies OTHER
chunks in the corpus that share the same neutral/disjunctive SHAPE, so
design chat can decide (Phase 2, a separate future prompt) whether this
is a systematic Stage-1 prompt defect (many such chunks exist and would
likely mis-extract the same way) or an isolated corpus artifact (only
p145_c0/p139_c0-shaped chunks are rare). Mechanical pattern match only --
no judgment calls, no Stage-1 extraction, no fixes. Design chat reviews
this candidate list and ratifies which chunks/features to actually run
through Stage 1 in a future Phase 2 prompt.

Scope decision (stated, not silent): scanned corpus = book_name ==
"cheiroslanguageo00chei_1" ONLY, not the full ~7,281-chunk 14-book
collection. `agent/interpretive/palm_reading.py`'s `_retrieve_per_
feature()` hardcodes `book_name=_CHEIRO_BOOK` for every per-feature
query (see that module's `_CHEIRO_BOOK` constant) -- a neutral/
disjunctive chunk in any OTHER book can never be retrieved by the palm
reading pipeline in the first place, so it is out of scope for this
specific defect's investigation. Full corpus size is reported for
context only.

Whitespace normalization: chunk text is OCR-scanned and known to embed
mid-word/mid-phrase newlines that defeat literal substring matching
(precedent: `diagnostics/fc_heartline_corpus_S68.md` found `p159_c2`'s
"...first\\nfinger" line-wrap defeated a literal "first finger" check).
All pattern matching below runs against a single whitespace-normalized
copy of each chunk's text (all whitespace, including embedded newlines,
collapsed to single spaces) -- not a dual literal/normalized track like
that earlier probe, since this task has no literal-vs-normalized
comparison goal of its own.

Feature affinity ("top-3 features by cosine to feature-query template"):
reuses `agent/interpretive/palm_reading._build_feature_query` VERBATIM
(read-only import, not reimplemented) with a fixed generic placeholder
quality ("well-formed") applied uniformly across all 10
`_FEATURE_REGISTRY` entries -- this script has no per-reading "quality"
to plug in (there is no confirmed observation here, just a corpus scan),
so a neutral placeholder is used to rank which feature(s) a chunk is
MOST semantically associated with in general, not to reproduce any
specific reading's retrieval. Chunk embeddings are read directly from
ChromaDB (`collection.get(..., include=["embeddings"])`) -- NOT
re-embedded -- so cosine scores are computed against the exact vectors
already stored by `ingestion/embedder.py` (same `text-embedding-3-small`
model `ingestion/query_engine.py` uses for live queries). Only the 10
feature-template queries are freshly embedded (one OpenAI call each).

Candidate granularity: one row per (chunk_id, pattern_type) pair -- a
chunk matching multiple pattern types gets multiple rows (one per
type); multiple sentences matching the SAME pattern type in the same
chunk collapse to one row (first match kept), to avoid combinatorial
row explosion. States this choice rather than leaving it implicit.
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI

from agent.interpretive.palm_reading import _FEATURE_REGISTRY, _build_feature_query
from ingestion.query_engine import EMBEDDING_MODEL, get_collection

_REPORT_PATH = Path(__file__).resolve().parent.parent / "diagnostics" / "latest_run.md"
_BOOK_NAME = "cheiroslanguageo00chei_1"
_GENERIC_QUALITY = "well-formed"
_CANDIDATE_CEILING = 30
_TOP_N_FEATURES = 3

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# --- Pattern definitions -----------------------------------------------
# "exact" patterns = literal/structural phrase matches (high specificity).
# "heuristic" pattern = the flanking-trait-word disjunction check (lower
# specificity by construction -- it is explicitly named "heuristic" in
# the task that specified it).

_EXACT_PHRASE_PATTERNS: dict[str, re.Pattern] = {
    "exact:strength or weakness": re.compile(r"\bstrength\s+or\s+weakness\b", re.IGNORECASE),
    "exact:either...or": re.compile(r"\beither\b[^.?!]*?\bor\b", re.IGNORECASE),
    "exact:may indicate": re.compile(r"\bmay\s+indicate\b", re.IGNORECASE),
    "exact:may signify": re.compile(r"\bmay\s+signify\b", re.IGNORECASE),
    "exact:may denote": re.compile(r"\bmay\s+denote\b", re.IGNORECASE),
    "exact:relates to the": re.compile(r"\brelates\s+to\s+the\b", re.IGNORECASE),
    "exact:relates principally to": re.compile(r"\brelates\s+principally\s+to\b", re.IGNORECASE),
}

_TRAIT_SUFFIXES = ("ity", "ness", "ence", "ance")
_TRAIT_WORDLIST = {"good", "bad", "strong", "weak", "positive", "negative"}
_OR_PAIR = re.compile(r"\b([A-Za-z][\w'-]*)\s+or\s+([A-Za-z][\w'-]*)\b", re.IGNORECASE)


def _is_trait_word(word: str) -> bool:
    w = word.lower().strip(".,;:")
    if w in _TRAIT_WORDLIST:
        return True
    return any(w.endswith(suf) for suf in _TRAIT_SUFFIXES)


def _heuristic_or_match(sentence: str) -> bool:
    """Both flanking words of an ' or ' within the same sentence must
    independently satisfy the trait-suffix-or-wordlist check."""
    for m in _OR_PAIR.finditer(sentence):
        left, right = m.group(1), m.group(2)
        if _is_trait_word(left) and _is_trait_word(right):
            return True
    return False


def _split_sentences(text: str) -> list[str]:
    normalized = " ".join(text.split())
    return [s.strip() for s in _SENTENCE_SPLIT.split(normalized) if s.strip()]


def _scan_chunk(text: str) -> dict[str, str]:
    """Returns {pattern_type: first_matching_sentence} for this chunk."""
    hits: dict[str, str] = {}
    for sentence in _split_sentences(text):
        for label, pattern in _EXACT_PHRASE_PATTERNS.items():
            if label not in hits and pattern.search(sentence):
                hits[label] = sentence
        if "heuristic:or-disjunction" not in hits and _heuristic_or_match(sentence):
            hits["heuristic:or-disjunction"] = sentence
    return hits


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _embed_feature_templates(client: OpenAI) -> dict[str, list[float]]:
    queries = {f: _build_feature_query(f, _GENERIC_QUALITY) for f in _FEATURE_REGISTRY}
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=list(queries.values()))
    return {f: response.data[i].embedding for i, f in enumerate(queries)}


def _top_features(chunk_embedding: list[float], feature_embeddings: dict[str, list[float]]) -> list[tuple[str, float]]:
    scored = [(f, _cosine(chunk_embedding, emb)) for f, emb in feature_embeddings.items()]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored[:_TOP_N_FEATURES]


def main() -> None:
    collection = get_collection()
    total_collection_size = collection.count()

    book_result = collection.get(
        where={"book_name": {"$eq": _BOOK_NAME}},
        include=["documents", "metadatas", "embeddings"],
    )
    ids = book_result["ids"]
    docs = book_result["documents"]
    metas = book_result["metadatas"]
    embeddings = book_result["embeddings"]
    total_book_chunks = len(ids)

    client = OpenAI()
    feature_embeddings = _embed_feature_templates(client)

    # candidate rows: (chunk_id, pattern_type, sentence, page_ref, top_features)
    all_rows: list[dict] = []
    pattern_totals: dict[str, int] = {
        **{label: 0 for label in _EXACT_PHRASE_PATTERNS},
        "heuristic:or-disjunction": 0,
    }

    for chunk_id, text, meta, emb in zip(ids, docs, metas, embeddings):
        hits = _scan_chunk(text)
        if not hits:
            continue
        top_feats = _top_features(list(emb), feature_embeddings)
        for pattern_type, sentence in hits.items():
            pattern_totals[pattern_type] += 1
            all_rows.append(
                {
                    "chunk_id": chunk_id,
                    "page_ref": meta.get("page_ref", 0),
                    "pattern_type": pattern_type,
                    "sentence": sentence,
                    "top_features": top_feats,
                }
            )

    total_candidates = len(all_rows)

    # Specificity ranking: exact-phrase pattern rows first (in the fixed
    # dict-definition order above), heuristic rows last. Stable secondary
    # sort by (page_ref, chunk_id) for reproducibility.
    _EXACT_ORDER = {label: i for i, label in enumerate(_EXACT_PHRASE_PATTERNS)}

    def _specificity_key(row: dict) -> tuple:
        pt = row["pattern_type"]
        if pt in _EXACT_ORDER:
            return (0, _EXACT_ORDER[pt], row["page_ref"], row["chunk_id"])
        return (1, 0, row["page_ref"], row["chunk_id"])

    all_rows.sort(key=_specificity_key)
    reported_rows = all_rows[:_CANDIDATE_CEILING]

    # --- Report -----------------------------------------------------
    lines: list[str] = []
    lines.append("# S71 Phase 1 probe: neutral/disjunctive chunk valence candidates")
    lines.append("")
    lines.append(
        "**PHASE 1 ONLY -- candidate identification, no extraction run.** "
        "`scripts/probe_neutral_chunk_valence.py`, throwaway/read-only, "
        "no production code touched. Design chat reviews this table and "
        "ratifies which chunks/features to probe in a future Phase 2 "
        "prompt (not run here)."
    )
    lines.append("")
    lines.append(
        f"Scope: `book_name == \"{_BOOK_NAME}\"` only ({total_book_chunks} of "
        f"{total_collection_size} total collection chunks) -- "
        "`palm_reading._retrieve_per_feature()` hardcodes this book for every "
        "per-feature query, so chunks in other books can never be retrieved "
        "by the palm reading pipeline and are out of scope for this defect."
    )
    lines.append("")
    distinct_chunks = len({r["chunk_id"] for r in all_rows})
    lines.append(
        f"**{total_candidates} total (chunk_id, pattern_type) candidate rows "
        f"found across {distinct_chunks} distinct chunks.** "
        + (
            f"Reporting top {_CANDIDATE_CEILING} by specificity "
            "(exact-phrase patterns first, heuristic disjunction-match last)."
            if total_candidates > _CANDIDATE_CEILING
            else f"Under the {_CANDIDATE_CEILING}-row ceiling -- all reported."
        )
    )
    lines.append("")

    lines.append("## Candidate table")
    lines.append("")
    lines.append("| chunk_id | page | pattern | top-3 features (cosine) | sentence |")
    lines.append("|---|---|---|---|---|")
    for row in reported_rows:
        feats_str = "; ".join(f"{f} ({score:.3f})" for f, score in row["top_features"])
        sentence_escaped = row["sentence"].replace("|", "\\|")
        lines.append(
            f"| `{row['chunk_id']}` | {row['page_ref']} | {row['pattern_type']} "
            f"| {feats_str} | {sentence_escaped} |"
        )
    lines.append("")

    lines.append("## Per-pattern totals (data-quality signal)")
    lines.append("")
    lines.append("| pattern_type | chunks matched |")
    lines.append("|---|---|")
    zero_patterns: list[str] = []
    for label, count in pattern_totals.items():
        lines.append(f"| {label} | {count} |")
        if count == 0:
            zero_patterns.append(label)
    lines.append("")
    if zero_patterns:
        lines.append(
            f"**Zero-match pattern(s): {', '.join(zero_patterns)}** -- either "
            "genuinely absent from this book's corpus, or the pattern's "
            "phrasing doesn't occur in Cheiro's actual prose (OCR variants "
            "not probed beyond whitespace normalization). Reported as a "
            "fact, not investigated further -- out of Phase 1 scope."
        )
    else:
        lines.append("No pattern matched zero chunks.")
    lines.append("")

    lines.append("## Known instances (for cross-reference, not re-scanned specially)")
    lines.append("")
    lines.append(
        "`p145_c0` and `p139_c0` (the two chunks that triggered this probe) "
        "are included above ONLY if they matched one of the 5 mechanical "
        "patterns -- this script does not special-case them."
    )
    p145_hit = any(r["chunk_id"] == f"{_BOOK_NAME}_p145_c0" for r in all_rows)
    p139_hit = any(r["chunk_id"] == f"{_BOOK_NAME}_p139_c0" for r in all_rows)
    lines.append(f"- `{_BOOK_NAME}_p145_c0` matched by this scan: {p145_hit}")
    lines.append(f"- `{_BOOK_NAME}_p139_c0` matched by this scan: {p139_hit}")
    if not p139_hit:
        lines.append("")
        lines.append(
            "**Data-quality signal for design chat**: `p139_c0`'s defect shape "
            "(a CONDITIONAL claim -- \"When the line of life sweeps far out into "
            "the hand, it is a sign of...\" -- labeled `valence=\"supports\"` "
            "instead of `\"conditional\"`) is NOT a neutral/disjunctive taxonomy "
            "statement like `p145_c0`; it is a precondition-bearing sentence "
            "that none of the 5 patterns above are shaped to catch. This means "
            "the candidate list above targets ONE defect shape (`p145_c0`'s) "
            "and is silent on the OTHER shape the S71 reversal already found "
            "(`p139_c0`'s) -- a scope gap in this pattern set, not evidence "
            "that `p139_c0`-shaped chunks are rare or absent from the corpus."
        )
    lines.append("")

    lines.append("## Explicitly NOT done (Phase 1 boundary)")
    lines.append("")
    lines.append(
        "- No Stage-1 extraction (`agent/interpretive/claim_extraction.py`) "
        "run against any candidate.\n"
        "- No filtering by judgment -- every mechanical match is reported, "
        "including any that a human would call a false positive on sight; "
        "that judgment is design chat's job in review, not this script's.\n"
        "- No fix proposed.\n"
        "- No commit made this run."
    )
    lines.append("")

    _REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"Report written to {_REPORT_PATH} "
        f"({total_candidates} candidate rows, {min(_CANDIDATE_CEILING, total_candidates)} reported)"
    )


if __name__ == "__main__":
    main()
